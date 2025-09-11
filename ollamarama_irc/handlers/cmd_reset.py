from __future__ import annotations

from typing import Callable, Awaitable


def make_reset_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.reset`` handler to restore defaults for a user.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def reset_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.reset`` to reset conversation and persona for the user.

        Args:
            channel: IRC channel.
            sender: Nickname of the user to reset.
            tokens: Tokenized input starting with ``.reset``.
        """
        ctx.history.reset(channel, sender, stock=False)
        ctx.irc.send_message(channel, f"{ctx.nickname} reset to default for {sender}")
    return reset_cmd


def make_stock_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.stock`` handler to apply stock settings for a user.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def stock_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.stock`` to reset to stock settings (no persona).

        Args:
            channel: IRC channel.
            sender: Nickname of the user.
            tokens: Tokenized input starting with ``.stock``.
        """
        ctx.history.reset(channel, sender, stock=True)
        ctx.irc.send_message(channel, f"Stock settings applied for {sender}")
    return stock_cmd
