# Security Hardening Guide

This guide provides practical steps to deploy the bot more safely in real channels. Review and adapt based on your network, risk profile, and compliance needs.

## Reporting

- See `SECURITY.md` for the project’s security policy and how to report vulnerabilities.

## Admin & Access Control

- Restrict admin commands to trusted nicknames via `irc.admins`.
- Keep your bot’s nickname/password private; identify with NickServ when supported.
- Invite the bot only to channels where it is needed; prefer private channels for testing.

## Prompts, Inputs, and Output Handling

- Treat all user inputs as untrusted. Avoid forwarding secrets to models.
- Be aware that responses may contain links or untrusted content. Do not execute code or commands without validation.
- If you export or mirror content outside IRC, sanitize and redact sensitive details.

## Configuration and Secrets

- Store configuration files outside world‑readable paths; set restrictive permissions (e.g., `chmod 600 config.json`).
- Do not commit real API keys or credentials. Use templates or environment variables.
- Prefer least‑privilege keys/tokens where applicable; rotate credentials periodically.

## Tools & MCP

- Only enable MCP servers you trust. Review their capabilities and network access.
- Builtin and MCP tool arguments are logged (truncated). Avoid passing secrets.
- Tool results are coerced to JSON strings before being sent back to the model, but they are not inherently safe.

## Logging and Data Retention

- Avoid logging full prompts or responses in production. Log only what is necessary for debugging (e.g., summaries).
- If logs must include content during debugging, ensure short retention, access controls, and redaction.

## Network and Runtime

- Run the bot under a dedicated OS user with minimal filesystem permissions.
- Place the bot behind a firewall; allow outbound connections only to required endpoints (IRC server, Ollama, MCP servers you control).
- Keep Python and dependencies up to date. Use pinned `requirements.txt` and scan for known CVEs.

## Dependency Hygiene

- Periodically update pinned dependencies after testing.
- Review transitive dependencies for licenses and security posture.

## Abuse, Misuse, and Rate Limiting

- Consider adding soft limits (e.g., per‑user rate limits, message length caps) to reduce abuse risk and cost.
- Be mindful of channel flood protections and rate limits. Throttle if necessary.
- Some networks restrict automated clients; comply with network policies.

## Backups and Recovery

- If you persist any local state (e.g., your own history store), back up only what you need and exclude secrets.
- Document the steps to re‑provision the bot account and restore configuration.

## Operational Practices

- Test changes in a non‑production channel first.
- Use feature flags or configuration toggles for risky changes.
- Keep a changelog of model updates and configuration changes that affect behavior.

## Responsible Use

- Share the [AI Output Disclaimer](ai-output-disclaimer.md) with users. Set expectations about non‑professional use and risks.
