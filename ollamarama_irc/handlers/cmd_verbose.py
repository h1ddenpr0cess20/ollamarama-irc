from __future__ import annotations

from typing import Callable, Awaitable


def make_verbose_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.verbose`` handler to manage verbosity.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def verbose_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.verbose [on|off|toggle|status]`` commands.

        Args:
            channel: IRC channel.
            sender: Nickname issuing the command.
            tokens: Tokenized input starting with ``.verbose``.
        """
        arg = (" ".join(tokens[1:]) if len(tokens) > 1 else "").strip().lower()
        if arg in ("", "status"):
            state = "ON" if getattr(ctx, "verbose", False) else "OFF"
            ctx.irc.send_message(channel, f"Verbose mode is {state}")
            return
        new_state = None
        if arg in ("on", "true", "1", "enable", "enabled"):
            new_state = True
        elif arg in ("off", "false", "0", "disable", "disabled"):
            new_state = False
        elif arg in ("toggle", "switch"):
            new_state = not bool(getattr(ctx, "verbose", False))
        else:
            ctx.irc.send_message(channel, "Usage: .verbose [on|off|toggle]")
            return

        ctx.verbose = bool(new_state)
        try:
            ctx.history.set_verbose(ctx.verbose)
        except Exception:
            pass
        state = "ON" if ctx.verbose else "OFF"
        body = f"Verbose mode set to {state}"
        ctx.log.info(body)
        ctx.irc.send_message(channel, body)

    return verbose_cmd
