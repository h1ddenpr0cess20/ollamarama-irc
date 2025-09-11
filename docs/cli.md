## CLI

Preferred: `ollamarama-irc [options]`

Or run as a module: `python -m ollamarama_irc [options]`

### Options
- `-c, --config <path>`: Path to JSON config (default `./config.json`).
- `--ollama-url <url>`: Override Ollama chat API URL.
- `--model <name|id>`: Override default model (key or id).
- `--verbose`: Start with verbose mode ON (omit brevity clause).
- `--server-models`: List models from the Ollama server and exit.
- `--log-level <level>`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- `--log-format <auto|rich|plain|json>`: Log formatting. `auto` selects Rich in TTY, plain otherwise.

### Environment Variables
- `OLLAMARAMA_OLLAMA_URL`
- `OLLAMARAMA_MODEL`
- `OLLAMARAMA_IRC_SERVER`
- `OLLAMARAMA_LOG_FORMAT` (`auto|rich|plain|json`)
  - In containers or CI, set to `plain` for clean logs without ANSI codes.

### Examples
- Use a different config: `ollamarama-irc -c ./myconfig.json`
- Point to remote Ollama: `ollamarama-irc --ollama-url http://host:11434/api/chat`
- Start with a model: `ollamarama-irc --model qwen3`
- List server models: `ollamarama-irc --server-models`

### Exit Codes
- `0`: success
- `2`: invalid configuration or CLI arguments
