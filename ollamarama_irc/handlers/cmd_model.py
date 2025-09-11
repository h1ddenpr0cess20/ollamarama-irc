from __future__ import annotations

from typing import Callable, Awaitable


def make_model_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.model`` admin handler.

    Without arguments it shows the current model and available keys.
    With an argument it sets the model to a known key or raw name.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def model_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.model [reset|<name>]`` commands.

        Args:
            channel: IRC channel.
            sender: Nickname issuing the command.
            tokens: Tokenized input starting with ``.model``.
        """
        arg = tokens[1] if len(tokens) > 1 else None
        if not arg:
            keys = []
            try:
                keys = sorted(list(ctx.models)) if isinstance(ctx.models, dict) else sorted(list(ctx.models))
            except Exception:
                pass
            ctx.irc.send_message(channel, f"Current model: {ctx.model}")
            ctx.irc.send_message(channel, f"Available models: {', '.join(keys)}")
            return
        if arg == "reset":
            ctx.model = ctx.default_model
        else:
            try:
                if isinstance(ctx.models, dict) and arg in ctx.models:
                    ctx.model = ctx.models[arg]
                else:
                    ctx.model = arg
            except Exception:
                pass
        ctx.log.info("Model set to %s", ctx.model)
        ctx.irc.send_message(channel, f"Model set to {ctx.model}")

    return model_cmd
