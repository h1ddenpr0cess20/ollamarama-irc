## Configuration

The bot reads a JSON configuration file (default `./config.json`). You can override with `--config` or environment variables. CLI flags and selected environment variables are merged on top of the file.

### Schema

- irc:
  - server (hostname or address)
  - nickname
  - password (optional NickServ password)
  - channels: list of channel names (e.g., `"#room"`)
  - admins: list of nicknames with admin privileges
- ollama:
  - api_url: Chat endpoint (default: `http://localhost:11434/api/chat`)
  - models: mapping of friendly names to model IDs (e.g., `{ "qwen3": "qwen3" }`)
  - default_model: selected model (must match a key or ID)
  - prompt: two strings `[prefix, suffix]` with optional third brevity clause `[prefix, suffix, brevity]`
  - personality: non‑empty default personality text
  - history_size: 1–1000 messages retained per user per channel
  - options: advanced generation options (e.g., `temperature`, `top_p`, `repeat_penalty`)
  - timeout: request timeout in seconds (default: 180)
  - verbose: when true omit the optional brevity clause for new conversations
  - mcp_servers: mapping of names to MCP server specs (optional)
    - Supports: URL string, shell string, argv list, or dict forms
    - Top‑level `mcp_servers` is also accepted and merged for backward compatibility

### Overrides

- CLI flags: `--ollama-url`, `--model`, `--log-level`
- Environment variables:
  - `OLLAMARAMA_OLLAMA_URL`
  - `OLLAMARAMA_MODEL`
  - `OLLAMARAMA_IRC_SERVER`

### Validation

The app validates configuration on startup; on errors it prints messages and exits with code `2`.

Checks include:

- `irc.server`, `irc.nickname` non‑empty; `irc.channels` non‑empty list of `#channel`
- `ollama.default_model` set and present by key or id
- `ollama.prompt` is a list of 2 or 3 strings
- Bounds on `options` (temperature 0–2, top_p 0–1, repeat_penalty 0.5–2)
- `ollama.mcp_servers` must be a mapping if provided

### Backwards Compatibility

- `irc.channel` (string) is accepted and normalized into `irc.channels`.
- Top‑level `mcp_servers` is merged into `ollama.mcp_servers`.
