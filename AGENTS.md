## Repository Guidelines

### Project Structure & Module Organization

- `ollamarama_irc/`: application code (CLI, config, IRC/Ollama clients, history, tools/MCP). Command handlers live in `ollamarama_irc/handlers/` (e.g., `cmd_ai.py`, `cmd_model.py`, `router.py`).
- `docs/`: user and operator docs (getting started, commands, security, architecture).
- `tests/`: pytest suite covering config, history, router, tools.
- Top-level: `config.json` (example), `help.md` (rendered help), `README.md`, policy docs.

### Build, Test, and Development Commands

- Create venv: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run tests: `pytest -q`
- Run locally: `ollamarama-irc -c config.json`
- Editable install (optional): `pip install -e .`

### Coding Style & Naming Conventions

- Python 3.10+; 4‑space indentation; prefer clear names and small, focused modules.
- Files and modules: `snake_case.py`. Handlers prefixed `cmd_*.py`.
- Functions/variables: `lower_snake_case`; classes: `CapWords`.
- Type hints where useful; avoid unnecessary dependencies.
- Markdown: keep tidy (e.g., fix blank lines around lists). Help is formatted with headings/tables.

### Testing Guidelines

- Frameworks: `pytest` (and `pytest-asyncio` where async is used).
- Naming: files `tests/test_*.py`; tests `test_*` functions or `Test*` classes.
- Scope: add tests alongside behavior changes; prefer small, deterministic cases.

### Commit & Pull Request Guidelines

- Commits: present-tense, concise, scoped (e.g., “Add model reset in handler”).
- PRs: describe problem and solution; list minimal changes; include/adjust tests; update docs if behavior changes.
- Keep PRs focused (no unrelated refactors); do not commit secrets or credentials.

### Security & Configuration Tips

- Read `SECURITY.md` and `docs/security.md` for hardening and reporting.
- Use a dedicated bot account; keep credentials private.
- Protect `config.json` (e.g., `chmod 600`); avoid logging sensitive content.
