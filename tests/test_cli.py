from ollamarama_irc.cli import build_parser


def test_cli_overrides_parse():
    p = build_parser()
    args = p.parse_args(["-c", "cfg.json", "--ollama-url", "http://x/api/chat", "--model", "q", "--log-level", "DEBUG"])
    assert args.config.name == "cfg.json"
    assert args.ollama_url == "http://x/api/chat"
    assert args.model == "q"
    assert args.log_level == "DEBUG"

