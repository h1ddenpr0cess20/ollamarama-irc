from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Awaitable, Callable, Dict, List, Optional, Tuple


Handler = Callable[[str, str, List[str]], Awaitable[None]]


@dataclass
class CommandRouter:
    nickname: str
    _commands: Dict[str, Handler] = field(default_factory=dict)

    def register(self, command: str, handler: Handler) -> None:
        """Register a handler for a command token.

        Args:
            command: Command token such as ``".ai"``.
            handler: Async callable with signature ``(channel, sender, tokens)``.
        """
        self._commands[command] = handler

    def parse(self, text: str) -> Tuple[str, List[str]]:
        """Parse raw text into the command token and token list.

        Args:
            text: Raw message text from IRC.

        Returns:
            A tuple of ``(command, tokens)`` where ``command`` is the first
            token or an empty string when none.
        """
        parts = text.split()
        return (parts[0] if parts else "", parts)

    async def dispatch(self, channel: str, sender: str, text: str) -> Optional[bool]:
        """Dispatch an incoming message to a registered handler.

        Supports mention-style invocations (``Nick: ...``) which are routed to
        the ``.ai`` handler when present.

        Args:
            channel: IRC channel where the message was received.
            sender: Nickname of the message author.
            text: Raw message text.

        Returns:
            ``True`` if a handler was found and invoked, ``None`` otherwise.
        """
        log = logging.getLogger("ollamarama_irc")
        cmd, tokens = self.parse(text)
        # Support mention-style: "BotNick: ..." routed to .ai
        if cmd == f"{self.nickname}:":
            handler = self._commands.get(".ai")
            if handler:
                try:
                    log.info("Command .ai (mention) from %s in %s: %s", sender, channel, text)
                except Exception:
                    pass
                await handler(channel, sender, tokens)
                return True

        handler = self._commands.get(cmd)
        if handler:
            try:
                log.info("Command %s from %s in %s: %s", cmd, sender, channel, text)
            except Exception:
                pass
            await handler(channel, sender, tokens)
            return True
        try:
            log.debug("No handler for input from %s in %s: %s", sender, channel, text)
        except Exception:
            pass
        return None
