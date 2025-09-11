# ollamarama-irc

[![License](https://img.shields.io/badge/License-AGPL--3.0-green.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-orange.svg)](https://ollama.com/)
[![IRC](https://img.shields.io/badge/Protocol-IRC-purple.svg)](https://en.wikipedia.org/wiki/Internet_Relay_Chat)

Ollamarama is an AI chatbot for IRC that uses local LLMs with Ollama. It can roleplay as almost anything you can think of with customizable personalities, individual user chat histories, and collaborative features.

## ✨ Features

- 🎭 **Roleplay as any character or personality** - Set any default personality that can be changed at any time
- 👥 **Individual chat histories** - Each user maintains their own separate conversation with their chosen personality
- 🤝 **Collaborative mode** - Users can interact with each other's chat histories for collaboration
- 🔄 **Real-time personality switching** - Change personalities on the fly during conversations

## 🌐 Other Versions

- **Matrix**: [ollamarama-matrix](https://github.com/h1ddenpr0cess20/ollamarama-matrix/)
- **Terminal**: [ollamarama](https://github.com/h1ddenpr0cess20/ollamarama)


## 🚀 Setup

### Prerequisites
Install and familiarize yourself with [Ollama](https://ollama.com/). Make sure you can run local LLMs successfully.

**Linux installation:**
```bash
curl https://ollama.com/install.sh | sh
```

**Windows installation:**  
Download the app from the [Ollama website](https://ollama.com/).

Or install the bot as a package (optional):
```bash
pip install .
```

### Model Setup
1. Browse and [download models](https://ollama.com/library) that work best for your use case
2. Add your chosen models to the `config.json` file
3. Install models using: `ollama pull modelname`

### Configuration
Edit `config.json` with nested keys (see `docs/configuration.md`):

IRC:
- `irc.server`: IRC server (e.g., `irc.libera.chat`)
- `irc.nickname`: bot nickname
- `irc.password`: NickServ password (optional)
- `irc.channels`: list of channels (or legacy `irc.channel`)
- `irc.admins`: list of admin nicknames (for admin commands)

Ollama:
- `ollama.api_url`: e.g., `http://localhost:11434/api/chat`
- `ollama.models`: mapping of names to model IDs
- `ollama.default_model`: selected model (name or ID)
- `ollama.options`: generation options (temperature, top_p, etc.)
- `ollama.timeout`: request timeout seconds
- `ollama.mcp_servers`: optional MCP servers

### Environment Setup
Create a virtual environment and install dependencies:

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```cmd
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 💬 Usage

### Starting the Bot
```bash
python -m ollamarama_irc -c config.json
```

Installed script (after `pip install .`):
```bash
ollamarama-irc -c config.json
```

In Docker or CI, prefer plain logs:
```bash
ollamarama-irc -c config.json --log-format plain
```

### Commands

| Command | Description |
|---------|-------------|
| `.ai message` or `botname: message` | Basic chat with the AI |
| `.x user message` | Talk to another user's chat history |
| `.persona personality` | Change personality (character, type, object, idea) |
| `.custom prompt` | Set a custom system prompt instead of roleplay |
| `.reset` | Reset to preset personality |
| `.stock` | Remove personality and use standard model settings |
| `.help` | Display the help menu |
| `.model` | Show current model and available models *(admin only)* |
| `.model name|reset` | Set or reset model *(admin only)* |
| `.clear` | Clear all histories and reset bot *(admin only)* |
| `.verbose [on|off|toggle]` | Control verbosity of prompts *(admin only)* |

## 📚 Documentation

- Full docs index: [docs/index.md](./docs/index.md)
- Ollama setup: [docs/ollama.md](./docs/ollama.md)
- Quickstart: [docs/getting-started.md](./docs/getting-started.md)
- Configuration: [docs/configuration.md](./docs/configuration.md)
- Commands: [docs/commands.md](./docs/commands.md)
- CLI: [docs/cli.md](./docs/cli.md)
- Architecture: [docs/architecture.md](./docs/architecture.md)
- Tools & MCP: [docs/tools-and-mcp.md](./docs/tools-and-mcp.md)
- Operations: [docs/operations.md](./docs/operations.md)
- Development: [docs/development.md](./docs/development.md)
- Migration: [docs/migration.md](./docs/migration.md)
- Legacy map: [docs/legacy-map.md](./docs/legacy-map.md)
- Refactor plan: [docs/refactor-plan.md](./docs/refactor-plan.md)
- Security: [docs/security.md](./docs/security.md)
- AI output disclaimer: [docs/ai-output-disclaimer.md](./docs/ai-output-disclaimer.md)
- Not a companion: [docs/not-a-companion.md](./docs/not-a-companion.md)
- Verification & safety: [docs/verification.md](./docs/verification.md)

## Docker

Build and run:
```bash
docker build -t ollamarama-irc .
docker run --rm -v $PWD/config.json:/app/config.json:ro ollamarama-irc
```

Compose:
```yaml
services:
  bot:
    build: .
    volumes:
      - ./config.json:/app/config.json:ro
    environment:
      - OLLAMARAMA_OLLAMA_URL=http://host.docker.internal:11434/api/chat
```

### Examples
```
.ai Hello, how are you today?
botname: What's the weather like?
.persona Sherlock Holmes
.x alice What do you think about this mystery?
.custom You are a helpful programming assistant
```
