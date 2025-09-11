# Development Guide

## Project Structure

- Core bot: `ollamarama_irc/` package (IRC client wrapper, handlers, router, Ollama client, tools/MCP).
- Config: `config.json` (IRC server/nick, channels, Ollama settings).
- Help text: `help.md` (user/admin commands shown in chat; split by `~~~`).
- Docs: see the index at [docs/index.md](./index.md) for overview, guides, and references.

## Local Setup

- Install: `pip install -r requirements.txt`
- Run: `python -m ollamarama_irc -c config.json`
- Optional linters: `ruff check .` and `black .`

## Coding Style

- PEP 8; 4‑space indentation; line length ≈ 100–120 chars.
- Names: functions/vars `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- Prefer small functions and pure helpers.
- Public functions should have docstrings and types where practical.
- Avoid wildcard imports; use the provided logger (`self.log`/`ctx.log`).

## Testing

- Framework: `pytest`. Tests live under `tests/` as `test_*.py`.
- Mock external I/O (IRC, HTTP calls to Ollama). The code exposes thin wrappers to simplify mocking.
- Target unit tests around:
  - Message parsing and router behavior
  - History trim/initialization
  - Model switching and prompt handling
  - Think‑tag stripping

## Security & Configuration

- Do not commit secrets. Keep `config.json` out of version control.
- Keep `ollama.api_url` configurable; default stays local.

## Contributing

- Use scoped, imperative commit messages (e.g., `fix: handle .x mentions`).
- Reference issues and describe user impact.
- Keep diffs focused. Update docs and `help.md` when commands/flags change.
