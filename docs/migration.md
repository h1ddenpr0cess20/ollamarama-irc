## Migration Notes

The project moved from a single‑file script to a modular package. The new CLI runs the modern implementation; the legacy code remains under `legacy/` for historical reference only.

### What Changed

- Entry is now `python -m ollamarama_irc` (CLI in `ollamarama_irc/cli.py`)
- Clear separation of concerns: config, IRC wrapper, handlers, history, Ollama client
- Tools/MCP support and richer logging
- Tests and documentation are first‑class

### How To Run (now)

- Start the bot: `python -m ollamarama_irc -c config.json`

### Backwards Compatibility

- Legacy `irc.channel` (string) is accepted and normalized into `irc.channels`.
