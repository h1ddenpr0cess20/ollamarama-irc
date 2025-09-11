import argparse
import sys
from pathlib import Path

from .logging_conf import setup_logging


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser.

    Returns:
        Configured ``argparse.ArgumentParser`` for the CLI.
    """
    p = argparse.ArgumentParser(
        prog="ollamarama-irc",
        description="Ollama IRC bot with modular architecture",
    )
    p.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Path to config JSON (default: ./config.json)",
    )
    p.add_argument(
        "--ollama-url",
        dest="ollama_url",
        help="Override Ollama chat API URL",
    )
    p.add_argument(
        "--model",
        dest="model",
        help="Override default model (key or id)",
    )
    p.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Start with verbose mode ON (omit brevity clause)",
    )
    p.add_argument(
        "--server-models",
        dest="server_models",
        action="store_true",
        help="List models from the Ollama server and exit",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    p.add_argument(
        "--log-format",
        choices=["auto", "rich", "plain", "json"],
        default=None,
        help="Logging format: auto (default), rich, plain, or json",
    )
    return p


def main(argv=None) -> int:
    """CLI entry point.

    Parses arguments, configures logging, optionally lists server models,
    and launches the IRC bot application.

    Args:
        argv: Optional list of CLI arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code (0 on success).
    """
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)

    # Resolve log format from CLI or env
    import os
    log_format = args.log_format or os.environ.get("OLLAMARAMA_LOG_FORMAT", "auto")
    setup_logging(args.log_level, mode=log_format)
    from .app import run_app  # defer heavy imports
    overrides = {}
    if args.ollama_url:
        overrides.setdefault("ollama", {})["api_url"] = args.ollama_url
    if args.model:
        overrides.setdefault("ollama", {})["default_model"] = args.model
    if args.verbose:
        overrides.setdefault("ollama", {})["verbose"] = True

    # Optional: list server models and exit
    if args.server_models:
        try:
            from .config import load_config
            from .ollama_client import OllamaClient
            cfg = load_config(args.config, overrides=overrides or None)
            base_url = cfg.ollama.api_url.rsplit("/", 1)[0] if "/" in cfg.ollama.api_url else cfg.ollama.api_url
            client = OllamaClient(base_url=base_url, timeout=cfg.ollama.timeout)
            tags = client.list_models()
            names = [t.get("name") or t.get("model") or "" for t in (tags or [])]
            for n in names:
                if n:
                    print(n)
            return 0
        except Exception as e:
            print(f"Failed to list models: {e}", file=sys.stderr)
            return 2
    run_app(args.config, overrides=overrides or None)
    return 0
