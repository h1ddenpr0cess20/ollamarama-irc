## Verification & Safety

This guide outlines how to verify model outputs and operate the bot safely in IRC environments.

### Pre‑Deploy Checklist
- Secrets: Keep `config.json` local and untracked; do not paste secrets into prompts.
- Access: Use `irc.admins` to restrict admin commands to trusted nicknames.
- Ollama: Confirm the correct `ollama.api_url` and that required models are pulled.
- Logs: Set `--log-format plain` in containers/CI to avoid ANSI sequences in logs.

### Runtime Safeguards
- Rate limiting: Respect network flood protections; introduce small delays between multi‑line sends.
- Length controls: Configure history size and chunk outbound messages to fit server limits.
- Timeouts: Set `ollama.timeout` to fail fast rather than hang the bot.
- Verbose mode: Prefer non‑verbose mode for public channels to keep replies concise.

### Verifying Model Outputs
- Treat responses as drafts. Cross‑check facts with primary sources.
- For code/shell: run in a sandbox first; inspect destructive commands.
- For calculations: recompute with a trusted tool or library.
- Prefer reproducible links and citations; follow them and verify independently.

### Tools & MCP
- Review each MCP server’s capabilities and code before enabling.
- Monitor logs for suspicious tool calls (unexpected network, file, or process access).
- Pass only the minimum required arguments; avoid secrets in tool inputs.

### Prompt Injection & Jailbreaks
- Do not execute instructions copied from model output without validation.
- Treat content retrieved from the web as untrusted. Sanitize or summarize before feeding back to the model.
- Use strong system prompts and keep them short, explicit, and focused on allowed behaviors.

### Incident Response
- If the bot posts harmful or sensitive content: remove from the channel, rotate secrets, and review logs.
- File an issue with sanitized logs and steps to reproduce.
- Consider temporarily disabling tools or switching to a safer model.

### Operational Tips
- Use `.model reset` to return to the configured default if behavior derails.
- Use `.clear` to wipe histories (admin only) after major prompt changes.
- Keep a changelog of config and model updates for traceability.
