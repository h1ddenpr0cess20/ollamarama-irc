from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


Message = Dict[str, str]


@dataclass
class HistoryStore:
    prompt_prefix: str
    prompt_suffix: str
    personality: str
    prompt_suffix_extra: str = ""
    max_items: int = 24
    _include_extra: bool = True
    store: Dict[str, Dict[str, List[Message]]] = field(default_factory=dict)

    def set_verbose(self, verbose: bool) -> None:
        """Enable or disable the optional extra suffix in system prompts.

        Args:
            verbose: When ``True``, omit the extra suffix for brevity.
        """
        # When verbose is True, omit the optional extra suffix
        self._include_extra = not bool(verbose)

    def _full_suffix(self) -> str:
        """Return the complete suffix including the optional extra part."""
        return f"{self.prompt_suffix}{self.prompt_suffix_extra if self._include_extra and self.prompt_suffix_extra else ''}"

    def _system_msg(self, personality: Optional[str] = None) -> Message:
        """Build a system message with the given or default persona.

        Args:
            personality: Optional persona string to use instead of default.

        Returns:
            A message dict with ``role='system'`` and composed content.
        """
        persona = personality if (personality is not None and personality != "") else self.personality
        return {"role": "system", "content": f"{self.prompt_prefix}{persona}{self._full_suffix()}"}

    def _ensure(self, channel: str, user: str) -> None:
        """Ensure storage structures exist for the given channel and user."""
        if channel not in self.store:
            self.store[channel] = {}
        if user not in self.store[channel]:
            self.store[channel][user] = [self._system_msg()]

    def reset(self, channel: str, user: str, stock: bool = False) -> None:
        """Reset the conversation history for a user in a channel.

        Args:
            channel: IRC channel name.
            user: Nickname whose conversation to reset.
            stock: When ``True``, do not reinitialize a system message.
        """
        if channel not in self.store:
            self.store[channel] = {}
        self.store[channel][user] = []
        if not stock:
            self.init_prompt(channel, user, persona=self.personality)

    def clear_all(self) -> None:
        """Clear all stored conversation history for all channels and users."""
        self.store.clear()

    def init_prompt(self, channel: str, user: str, persona: Optional[str] = None, custom: Optional[str] = None) -> None:
        """Initialize the system prompt for a user in a channel.

        Args:
            channel: IRC channel name.
            user: Nickname for which to initialize the prompt.
            persona: Optional persona string to embed.
            custom: Optional custom system message to use as-is.
        """
        self._ensure(channel, user)
        if custom:
            self.store[channel][user] = [{"role": "system", "content": custom}]
        else:
            self.store[channel][user] = [self._system_msg(persona)]

    def add(self, channel: str, user: str, role: str, content: str) -> None:
        """Append a message to a user's conversation history.

        Args:
            channel: IRC channel name.
            user: Nickname whose history to append to.
            role: Message role (e.g. ``"user"`` or ``"assistant"``).
            content: Message content.
        """
        self._ensure(channel, user)
        self.store[channel][user].append({"role": role, "content": content})
        self._trim(channel, user)

    def get(self, channel: str, user: str) -> List[Message]:
        """Get a copy of the current message history for a user.

        Args:
            channel: IRC channel name.
            user: Nickname whose messages to read.

        Returns:
            A shallow copy of the user's message list.
        """
        self._ensure(channel, user)
        return list(self.store[channel][user])

    def _trim(self, channel: str, user: str) -> None:
        """Trim conversation history to the configured maximum items."""
        msgs = self.store[channel][user]
        while len(msgs) > self.max_items:
            if msgs and msgs[0].get("role") == "system":
                if len(msgs) > 1:
                    msgs.pop(1)
                else:
                    break
            else:
                msgs.pop(0)
