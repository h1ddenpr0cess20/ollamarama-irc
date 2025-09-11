# Operations & Security

Guidance for running, monitoring, and maintaining the bot in production‑like environments.

## Running the Bot
- Start: `python -m ollamarama_irc -c config.json`
- Log level: use `--log-level DEBUG` for diagnostics; default is `INFO`.

### Logging
- Rich logging in TTY; use `--log-format plain` for containers or log shippers.
- IRC highlighter colors:
  - Nicknames: cyan
  - Channels: magenta
  - “Thinking”/tool details: dim italic
  - Response body: bold
  - Models and tool info: yellow/cyan

### Graceful Exit
- Stop with Ctrl‑C (SIGINT) or SIGTERM. The bot disconnects cleanly and shuts down worker threads.

## Health & Model Management
- `.model` shows current and available models; `.model <name>` switches; `.model reset` restores default.
- Use `--server-models` to print models directly from the Ollama server.
- Remote servers: set `OLLAMARAMA_OLLAMA_URL` or `--ollama-url`.

## Channels & Identity
- Join multiple channels with `irc.channels`.
- NickServ: set `irc.password` to identify after connect; the bot waits briefly before joining.
- Use `irc.admins` to restrict admin commands to specific nicks.

## Backups & Persistence
- Histories are in‑memory. If you need persistence, run the bot continuously or integrate a store; otherwise history resets on restart.

## Monitoring
- Watch logs for connection churn, timeouts, and tool errors.
- Consider a process supervisor (systemd, Docker/Compose, or a PaaS) with restart policy.

## Security Guidelines
- Keep `config.json` out of version control. Redact secrets in logs and issues.
- Treat tool outputs as untrusted. Prefer local MCP servers you control.
- Limit network egress if you deploy tools with network capabilities.

## Troubleshooting
- No replies: confirm the bot joined the channel and Ollama is reachable.
- Model errors: ensure the model is pulled and the ID is correct.
- Flood/rate limits: increase pauses between message chunks if needed.
- Timeouts: raise `ollama.timeout` or reduce prompt/history size.
