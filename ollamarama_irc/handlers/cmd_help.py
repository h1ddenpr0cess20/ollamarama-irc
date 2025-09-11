from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable, Awaitable


def make_help_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.help`` handler that sends usage information.

    It prefers the top-level ``help.md`` (or ``help.txt``) file and sends
    the main section via NOTICE to the requesting user to avoid channel spam.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def help_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.help`` by streaming help text to the requester.

        Args:
            channel: IRC channel (unused).
            sender: Nickname of the requester.
            tokens: Tokenized input starting with ``.help``.
        """
        # Prefer Markdown help; fallback to txt or stub
        help_menu = ""
        for path in (Path("help.md"), Path("help.txt")):
            if path.exists():
                help_menu = path.read_text()
                break
        if not help_menu:
            ctx.log.info("help.md/help.txt not found; sending inline help stub")
            ctx.irc.send_notice(sender, "Commands: .ai, .x, .persona, .custom, .reset, .stock, .help, .model, .clear, .verbose")
            return
        parts = help_menu.split("~~~")
        # Send main section to requester via NOTICE to avoid flooding channel
        for line in parts[0].splitlines():
            ctx.irc.send_notice(sender, line.strip())
            await asyncio.sleep(0)
        # Admin-only section
        if sender in ctx.cfg.irc.admins and len(parts) > 1:
            for line in parts[1].splitlines():
                ctx.irc.send_notice(sender, line.strip())
                await asyncio.sleep(0)

    return help_cmd
