# Architecture

The bot is a small, modular application that wires an IRC client to the Ollama Chat API through a command router and stateless handlers, mirroring the Matrix project’s design.

## Modules

- `ollamarama_irc/cli.py`: CLI entry; merges overrides and starts the app.
- `ollamarama_irc/config.py`: Dataclasses, deep‑merge, env/CLI overrides, validation.
- `ollamarama_irc/logging_conf.py`: Rich logging with a custom IRC highlighter.
- `ollamarama_irc/ollama_client.py`: HTTP client for `/api/chat` and tool calls.
- `ollamarama_irc/irc_client.py`: Thin wrapper over `irc.bot.SingleServerIRCBot` (connect/join/send/callbacks).
- `ollamarama_irc/history.py`: Per‑channel/user histories with system prompt seeding and trimming.
- `ollamarama_irc/handlers/`: Router and command handlers (`.ai`, `.model`, `.reset`, `.help`, `.persona`, `.custom`, `.x`, `.clear`, `.verbose`).
- `ollamarama_irc/tools/*`: Builtin tools and schema; merged with MCP tools.
- `ollamarama_irc/fastmcp_client.py`: MCP client for discovering and calling tools.

## Data Flow

1. CLI loads and validates config; composes dependencies into an `AppContext`.
2. IRC wrapper connects, identifies to NickServ (optional), joins channels, and dispatches public messages to the router.
3. Router selects a handler by command prefix or `BotNick:` mention.
4. Handlers read/write `HistoryStore` and call `OllamaClient` in a background thread.
5. Replies are sent as plain text; think/solution tags are stripped from output and optionally logged.

## Async Boundaries

- IRC I/O runs on a background thread via the `irc` library; the app exposes async callbacks and schedules coroutines.
- Ollama HTTP calls are synchronous; they run in a thread executor via `ctx.to_thread`.

## Histories and Personas

`HistoryStore` maintains a per‑user, per‑channel transcript. A system prompt is always the first entry, constructed from the configured personality and prompt prefix/suffix. An optional third “brevity” clause can be omitted in verbose mode. Trim logic enforces a max history size while preserving context.

## Tools and MCP

Builtin tools (described in a JSON schema) and MCP tools are merged at startup. When the model emits `tool_calls`, the app executes each call, appends tool results to the transcript, and asks the model to continue (up to 8 iterations). MCP tools take precedence on name collisions.

## Security Notes

- No secrets are committed. `config.json` lives locally.
- Restrict admin commands to trusted nicknames via `irc.admins`.
- Treat tool outputs as untrusted; see [security.md](./security.md) and [tools-and-mcp.md](./tools-and-mcp.md).
