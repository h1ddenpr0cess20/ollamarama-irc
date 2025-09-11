## Getting Started (IRC)

Follow these steps to run the bot locally against your Ollama instance.

### 1) Prerequisites
- Python 3.10+
- Ollama installed and serving (see [ollama.md](./ollama.md))

Install Ollama and pull at least one model (example):

```
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3
```

### 2) Install
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure
Create or edit `config.json` and set the basics:
- `irc.server`: e.g., `irc.libera.chat`
- `irc.nickname`: your bot nickname
- `irc.password`: optional NickServ password
- `irc.channels`: list of channels like `["#yourchannel"]`
- `irc.admins`: list of nicknames allowed to use admin commands
- `ollama.api_url`: usually `http://localhost:11434/api/chat`
- `ollama.models` and `ollama.default_model`

See [Configuration](configuration.md) for full schema and validation rules.

### 4) Run
```
python -m ollamarama_irc -c config.json
```

If installed as a package:
```
ollamarama-irc -c config.json
```

Join the same channel(s) and try:
- `.ai hello there`
- `.model` to list available models, or `.model reset` to revert

### Next Steps
- Learn commands: [commands.md](./commands.md)
- Tune configuration: [configuration.md](./configuration.md)
- Enable tools/MCP: [tools-and-mcp.md](./tools-and-mcp.md)
