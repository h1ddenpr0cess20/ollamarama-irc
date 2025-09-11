from __future__ import annotations

from typing import Callable, Awaitable


def make_persona_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.persona`` handler to set a predefined persona.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def persona_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.persona <text>`` to set the system persona.

        Args:
            channel: IRC channel.
            sender: Nickname of the user.
            tokens: Tokenized input starting with ``.persona``.
        """
        persona = " ".join(tokens[1:]).strip()
        ctx.history.init_prompt(channel, sender, persona=persona)
        ctx.log.info("System prompt for %s set to persona: '%s'", sender, persona)
        # Greet: introduce yourself
        ctx.history.add(channel, sender, "user", "introduce yourself")
        await ctx.respond(channel, sender)
    return persona_cmd


def make_custom_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.custom`` handler to set an arbitrary system prompt.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def custom_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.custom <text>`` to set a custom system prompt.

        Args:
            channel: IRC channel.
            sender: Nickname of the user.
            tokens: Tokenized input starting with ``.custom``.
        """
        custom = " ".join(tokens[1:]).strip()
        ctx.history.init_prompt(channel, sender, custom=custom)
        ctx.log.info("System prompt for %s set to custom: '%s'", sender, custom)
        # Greet: introduce yourself
        ctx.history.add(channel, sender, "user", "introduce yourself")
        await ctx.respond(channel, sender)
    return custom_cmd
