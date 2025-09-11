## Commands

All commands are issued as public messages in a channel. Many also work via `BotNick: <message>` mention routing. Admin‑only commands require your nickname in `irc.admins`.

### User Commands
- `.ai <message>`: Send a prompt to the current model. Also triggered by `BotNick: <message>`.
  - Example: `.ai summarize the last 20 lines`
- `.x <target> <message>`: Ask on behalf of another nick in the same channel. The target must have an existing history.
  - Example: `.x alice what did you ask earlier?`
- `.persona <text>`: Set a persona for your conversation and introduce the bot to the channel.
  - Example: `.persona You are a concise systems engineer.`
- `.custom <system prompt>`: Replace the system prompt entirely for your conversation and introduce the bot.
  - Example: `.custom You only answer with JSON objects.`
- `.reset`: Reset your history (keeps default persona/prompt).
- `.stock`: Reset to a “stock” history without a system prompt.
- `.help`: Show help (via NOTICE if available, inline fallback otherwise).

### Admin Commands
- `.model [name|reset]`: Show or set the active model for the channel context.
  - Examples: `.model`, `.model qwen2.5`, `.model reset`
- `.clear`: Clear all histories in this channel and reset defaults.
- `.verbose [on|off|toggle]`: Control omission of the optional brevity clause in prompts.
  - Example: `.verbose on` for long‑form answers; `.verbose off` for concise.

### Notes & Tips
- Rate limits: servers may throttle bursts. The bot chunks long replies into multiple messages with short pauses.
- Tools/MCP: when enabled, the model may call tools before responding. Tool calls and results are summarized in logs.
- Privacy: messages are stored in memory per user per channel to maintain context; use `.stock` for minimal context.
