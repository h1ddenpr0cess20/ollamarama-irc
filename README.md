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

### Model Setup
1. Browse and [download models](https://ollama.com/library) that work best for your use case
2. Add your chosen models to the `config.json` file
3. Install models using: `ollama pull modelname`

### Configuration
Fill in the required values in `config.json`:
- `channel` - IRC channel to join
- `nickname` - Bot's IRC nickname  
- `server` - IRC server address
- `password` - IRC password (optional, but required for some channels)

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
python3 ollamarama.py
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
| `.model name` | Set a specific model *(admin only)* |

### Examples
```
.ai Hello, how are you today?
botname: What's the weather like?
.persona Sherlock Holmes
.x alice What do you think about this mystery?
.custom You are a helpful programming assistant
```
