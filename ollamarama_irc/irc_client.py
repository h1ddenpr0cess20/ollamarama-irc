from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, List, Optional
import threading

import irc.bot


log = logging.getLogger(__name__)


OnMessage = Callable[[str, str, str], None]
OnReady = Callable[[], None]


class IRCClient(irc.bot.SingleServerIRCBot):
    """Thin wrapper over irc.bot to expose simple callbacks.

    - Calls `on_ready()` after joining channels
    - Calls `on_message(channel, sender, text)` for public messages
    - Exposes `send_message` and `send_notice` helpers
    """

    def __init__(
        self,
        server: str,
        port: int,
        nickname: str,
        password: Optional[str],
        channels: List[str],
        on_ready: Optional[OnReady] = None,
        on_message: Optional[OnMessage] = None,
    ) -> None:
        super().__init__([(server, port)], nickname, nickname)
        self.server = server
        self.password = password
        # Avoid shadowing irc.bot.SingleServerIRCBot.channels (a dict)
        self.join_channels = channels
        self.on_ready_cb = on_ready
        self.on_message_cb = on_message
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._wait_event: Optional[asyncio.Event] = None

    # Event handlers
    def on_welcome(self, c, e):  # type: ignore[override]
        """Handle server welcome and join configured channels.

        Args:
            c: IRC connection object.
            e: Event payload from python-irc.
        """
        log.info("Connected to %s", self.server)
        if self.password:
            c.privmsg("NickServ", f"IDENTIFY {self.password}")
            log.info("Identifying to NickServ")
            time.sleep(5)

        for ch in self.join_channels:
            log.info("Joining channel: %s", ch)
            c.join(ch)

        if self.on_ready_cb:
            try:
                # Ensure callback runs on the main asyncio loop thread
                if self.loop is not None:
                    self.loop.call_soon_threadsafe(self.on_ready_cb)
                else:
                    # Fallback (should not happen when using run_async)
                    self.on_ready_cb()
            except Exception:
                log.exception("Error in on_ready callback")

    def on_pubmsg(self, c, e):  # type: ignore[override]
        """Forward public messages to the user callback if set.

        Args:
            c: IRC connection object.
            e: Event payload containing sender and message.
        """
        try:
            text = e.arguments[0]
        except Exception:
            return
        sender = e.source.split("!")[0]
        channel = e.target
        if self.on_message_cb:
            try:
                if self.loop is not None:
                    self.loop.call_soon_threadsafe(self.on_message_cb, channel, sender, text)
                else:
                    self.on_message_cb(channel, sender, text)
            except Exception:
                log.exception("Error in on_message callback")

    def on_nicknameinuse(self, c, e):  # type: ignore[override]
        """Handle nickname conflicts by appending an underscore and retrying.

        Args:
            c: IRC connection object.
            e: Nick-in-use event payload.
        """
        try:
            current = self.connection.get_nickname()
        except Exception:
            current = None
        new_nick = (current or "bot") + "_"
        log.info("Nickname in use, trying '%s'", new_nick)
        try:
            self.connection.nick(new_nick)
        except Exception:
            pass

    # Utilities
    def send_message(self, channel: str, text: str) -> None:
        """Send a message to an IRC channel.

        Args:
            channel: Target channel name (e.g. ``#room``).
            text: Message body to send.
        """
        self.connection.privmsg(channel, text)

    def send_notice(self, nick: str, text: str) -> None:
        """Send a NOTICE message to a nick.

        Args:
            nick: Recipient nickname.
            text: Notice body to send.
        """
        self.connection.notice(nick, text)

    async def run_async(self) -> None:
        """Run the IRC reactor in a background thread and await shutdown.

        Using a dedicated daemon thread avoids blocking Ctrl-C / loop shutdown,
        since python-irc's reactor "process_forever" does not return on its own.

        Returns:
            None. Completes when ``shutdown()`` signals the wait event.
        """
        self.loop = asyncio.get_running_loop()
        self._wait_event = asyncio.Event()
        # Start the IRC reactor in a background daemon thread
        try:
            th = threading.Thread(target=self.start, name="irc-reactor", daemon=True)
            th.start()
            self._thread = th
        except Exception:
            log.exception("Failed to start IRC reactor thread")
            return
        # Wait until shutdown is requested
        await self._wait_event.wait()

    def shutdown(self) -> None:
        """Request a clean shutdown and release any waiters.

        Returns:
            None. Signals the wait event created in ``run_async``.
        """
        try:
            # Disconnect current connection and all tracked connections
            self.disconnect("shutting down")
        except Exception:
            pass
        try:
            # Ensure all connections are dropped so the reactor idles
            self.reactor.disconnect_all("shutting down")
        except Exception:
            pass
        try:
            # Release the waiter in run_async
            if self.loop and self._wait_event is not None:
                self.loop.call_soon_threadsafe(self._wait_event.set)
        except Exception:
            pass
