from __future__ import annotations

from typing import Callable, Awaitable


def make_ai_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.ai`` command handler.

    The handler records the user's message into history and asks the
    model to respond in the same channel/thread.

    Args:
        ctx: Application context with IRC, history and model clients.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def ai_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.ai`` messages.

        Args:
            channel: IRC channel where the command was issued.
            sender: Nickname of the user.
            tokens: Tokenized input, where ``tokens[0]`` is ``.ai``.
        """
        # tokens[0] is the command
        message = " ".join(tokens[1:]).strip()
        if not message:
            return
        ctx.history.add(channel, sender, "user", message)
        await ctx.respond(channel, sender)
    return ai_cmd


def make_x_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.x`` cross-user relay handler.

    The handler routes a message to another user's conversation context in
    the same channel and returns the model response addressed to the sender.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def x_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.x <target> <message>`` commands.

        Args:
            channel: IRC channel.
            sender: Nickname issuing the command.
            tokens: Tokenized input starting with ``.x``.
        """
        # .x <target> <message>
        if len(tokens) < 3:
            return
        target = tokens[1]
        message = " ".join(tokens[2:]).strip()
        if not message:
            return
        room_hist = ctx.history.store.get(channel, {})
        if target in room_hist:
            ctx.history.add(channel, target, "user", message)
            await ctx.respond(channel, target, sender2=sender)
    return x_cmd
