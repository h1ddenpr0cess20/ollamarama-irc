import logging
import logging.config
import os
import re
import sys


class IRCHighlighter:
    """Rich highlighter for IRC log messages.

    Highlights nicknames, channels, tool call details, model names and
    model "thinking" sections to improve readability when using Rich.
    """

    _chan_re = re.compile(r"#[A-Za-z0-9_\-]+")
    _nick_re = re.compile(r"^(?P<nick>[^\s:]+):")
    _model_re = re.compile(r"\bModel set to\s+(?P<model>\S+)")
    _sending_re = re.compile(r"Sending response to\s+(?P<name>.+?)\s+in\s+(?P<chan>#[^\s]+):\s+(?P<body>.*)", re.S)
    _tool_call_re = re.compile(r"(?P<tool>Tool)\s+\((?P<origin>MCP|builtin)\):\s+(?P<name>\S+)\s+args=(?P<args>.*)")
    _thinking_re = re.compile(r"\bModel thinking:\s+(?P<thought>[\s\S]*)")

    def __call__(self, value):
        """Return a Rich ``Text`` with styles applied.

        Args:
            value: A string or Rich ``Text`` instance.

        Returns:
            The styled Rich ``Text`` instance for logging.
        """
        try:
            from rich.text import Text
        except Exception:
            return value
        text = value if hasattr(value, "stylize") else Text(str(value))
        self.highlight(text)
        return text

    def highlight(self, text) -> None:
        """Apply syntax highlighting to a Rich ``Text`` value in-place.

        Args:
            text: The mutable ``Text`` object to stylize.
        """
        s = text.plain
        for m in self._chan_re.finditer(s):
            text.stylize("magenta", m.start(), m.end())
        for m in self._nick_re.finditer(s):
            span = m.span("nick")
            text.stylize("bold cyan", span[0], span[1])
        for m in self._model_re.finditer(s):
            span = m.span("model")
            text.stylize("bold yellow", span[0], span[1])
        for m in self._sending_re.finditer(s):
            nsp = m.span("name")
            csp = m.span("chan")
            bsp = m.span("body")
            text.stylize("bold cyan", nsp[0], nsp[1])
            text.stylize("magenta", csp[0], csp[1])
            text.stylize("bold", bsp[0], bsp[1])
        for m in self._tool_call_re.finditer(s):
            tsp = m.span("tool")
            osp = m.span("origin")
            nsp = m.span("name")
            asp = m.span("args")
            text.stylize("bold cyan", tsp[0], tsp[1])
            text.stylize("cyan", osp[0], osp[1])
            text.stylize("bold yellow", nsp[0], nsp[1])
            text.stylize("dim", asp[0], asp[1])
        for m in self._thinking_re.finditer(s):
            tsp = m.span("thought")
            # Dim only the thinking content, keep prefix readable
            text.stylize("dim", tsp[0], tsp[1])


def setup_logging(level: str = "INFO", json: bool = False, mode: str = "auto") -> None:
    """Configure package logging handlers and formatters.

    Args:
        level: Logging level name (e.g. ``"DEBUG"`` or ``"INFO"``).
        json: Backward-compatibility flag to force JSON output.
        mode: One of ``"auto"``, ``"rich"``, ``"plain"``, or ``"json"``.

    Returns:
        None. Configures the ``ollamarama_irc`` logger and suppresses noisy
        third-party libraries.
    """
    lvl = getattr(logging, level.upper(), logging.INFO)

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": True,
    })

    # Back-compat: json=True flag takes precedence
    if json:
        mode = "json"

    # Auto-select when requested
    if mode == "auto":
        is_tty = False
        try:
            is_tty = sys.stderr.isatty() or sys.stdout.isatty()
        except Exception:
            is_tty = False
        if os.environ.get("NO_COLOR"):
            mode = "plain"
        elif os.environ.get("CI"):
            mode = "plain"
        elif os.environ.get("RICH_FORCE_TERMINAL"):
            mode = "rich"
        else:
            mode = "rich" if is_tty else "plain"

    if mode == "json":
        fmt = "{\"time\": \"%(asctime)s\", \"level\": \"%(levelname)s\", \"name\": \"%(name)s\", \"message\": %(message)r}"
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))
        root = logging.getLogger()
        root.handlers = []
        root.setLevel(logging.ERROR)
        pkg_logger = logging.getLogger("ollamarama_irc")
        pkg_logger.handlers = []
        pkg_logger.setLevel(lvl)
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False
        logging.getLogger("fastmcp").setLevel(logging.ERROR)
        logging.getLogger("mcp").setLevel(logging.ERROR)
        return

    if mode == "plain":
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        root = logging.getLogger()
        root.handlers = []
        root.setLevel(logging.ERROR)
        pkg_logger = logging.getLogger("ollamarama_irc")
        pkg_logger.handlers = []
        pkg_logger.setLevel(lvl)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False
        logging.getLogger("fastmcp").setLevel(logging.ERROR)
        logging.getLogger("mcp").setLevel(logging.ERROR)
        return

    # Else: mode == 'rich'
    try:
        from rich.console import Console
        from rich.logging import RichHandler
        from rich.traceback import install as rich_traceback_install

        rich_traceback_install(show_locals=False)
        console = Console(highlight=False)
        highlighter = IRCHighlighter()
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=True,
            show_level=True,
            show_time=True,
            show_path=False,
            highlighter=highlighter,
        )
        datefmt = "[%X]"
        fmt = "%(message)s"

        root = logging.getLogger()
        root.handlers = []
        root.setLevel(logging.ERROR)
        pkg_logger = logging.getLogger("ollamarama_irc")
        pkg_logger.handlers = []
        pkg_logger.setLevel(lvl)
        logging.Formatter(fmt=fmt, datefmt=datefmt)
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False
        # Suppress noisy third-party loggers
        logging.getLogger("fastmcp").setLevel(logging.ERROR)
        logging.getLogger("mcp").setLevel(logging.ERROR)
    except Exception:
        # Fallback to plain if Rich is unavailable
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        root = logging.getLogger()
        root.handlers = []
        root.setLevel(logging.ERROR)
        pkg_logger = logging.getLogger("ollamarama_irc")
        pkg_logger.handlers = []
        pkg_logger.setLevel(lvl)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False
        logging.getLogger("fastmcp").setLevel(logging.ERROR)
        logging.getLogger("mcp").setLevel(logging.ERROR)
