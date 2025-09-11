from __future__ import annotations

from typing import Callable, Awaitable


def make_clear_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.clear`` admin handler to reset global state.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def clear_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.clear`` to wipe all history and restore defaults.

        Args:
            channel: IRC channel.
            sender: Nickname issuing the command.
            tokens: Tokenized input starting with ``.clear``.
        """
        ctx.history.clear_all()
        ctx.model = ctx.default_model
        ctx.personality = ctx.default_personality
        body = "Bot has been reset for everyone"
        ctx.log.info(body)
        ctx.irc.send_message(channel, body)
    return clear_cmd
