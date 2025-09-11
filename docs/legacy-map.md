## Legacy → New Mapping

This page maps parts of the archived legacy implementation to their equivalents in the refactored IRC codebase.

### Startup & Runtime

- Legacy `ollamarama.py: __main__` → New `ollamarama_irc/__main__.py` (entry), `ollamarama_irc/cli.py` (flags), `ollamarama_irc/app.py: run_app()` (compose/connect/join).
- Legacy direct `config.json` read → New `ollamarama_irc/config.py` (`load_config`, `AppConfig`, `validate_config`).
- Legacy logging via `logging.basicConfig` → New `ollamarama_irc/logging_conf.py: setup_logging()` and `AppContext.log`.

### IRC I/O

- Legacy `SingleServerIRCBot` used inline → New `ollamarama_irc/irc_client.py: IRCClient` (connect, NickServ identify, join, callbacks, shutdown).
- Legacy `on_pubmsg` inline routing → New `handlers/router.py: CommandRouter` with `register()` and `dispatch()`.

### Routing & Commands

- Legacy `handle_message()` dict of commands → New router + individual handler modules.
- Legacy “BotNick:” mention handled inline → Router supports mention and routes to `.ai`.

### AI Interaction

- Legacy `respond()` building payload + `httpx.post` → New `ollamarama_irc/ollama_client.py: OllamaClient.chat()` and `.chat_with_tools()`.
- Legacy think/solution markers stripping → Centralized in `ollamarama_irc/text_utils.py` and used by app/handlers.

### History & Personas

- Legacy `messages` dict + `add_history()` + trim → New `ollamarama_irc/history.py: HistoryStore` (`add`, `get`, `reset`, `init_prompt`, `_trim`) keyed by channel+user.
- Legacy `set_prompt(persona/custom)` → New handlers `cmd_prompt.py` for `.persona` and `.custom`.

### User Commands

- Legacy `.ai` / `BotNick:` → New `handlers/cmd_ai.py: make_ai_handler()`.
- Legacy `.x` cross‑user → New `handlers/cmd_ai.py: make_x_handler()` (nickname with prior history in the channel).
- Legacy `.reset` and `.stock` → New `handlers/cmd_reset.py`.
- Legacy `.help` → New `handlers/cmd_help.py` (prefers `help.md`, admin section after `~~~`).

### Admin Commands

- Legacy `.model` (list/set/reset) → New `handlers/cmd_model.py`.
- Legacy `.clear` → New `handlers/cmd_clear.py`.
- New `.verbose` → `handlers/cmd_verbose.py`.

### Welcome/Chunking

- Legacy welcome + chunking → New `app.py` (`_send_welcome`, `chop`).

### Documentation

- Legacy top‑level docs → New consolidated under [docs/index.md](./index.md) (getting started, configuration, commands, architecture, CLI, operations, development, migration, refactor plan, security, disclaimers).
- `help.md` remains at repo root; consumed by `handlers/cmd_help.py`.
