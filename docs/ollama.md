## Ollama Setup

Ollama runs local models and exposes an HTTP API used by this bot.

### Install Ollama
- macOS: `brew install ollama` or download from the Ollama site.
- Linux: follow the official install script or packages for your distro.
- Windows (WSL): install under WSL2 and expose the port to Windows if needed.

Confirm installation:
```
ollama --version
ollama serve &  # optional; many packages start the daemon automatically
```

### Pull Models
```
ollama pull llama3.1
ollama pull qwen3
ollama pull mistral
```

List available models:
```
curl -s http://localhost:11434/api/tags | jq
```

### Configure the Bot
- Set `ollama.api_url` to the chat endpoint, typically `http://localhost:11434/api/chat`.
- Map friendly names in `ollama.models` to an Ollama model ID, e.g. `{ "llama": "llama3.1" }`.
- Choose an `ollama.default_model` (either a key from `models` or a raw ID).

Example snippet in `config.json`:
```
"ollama": {
  "api_url": "http://localhost:11434/api/chat",
  "models": { "llama": "llama3.1", "qwen3": "qwen3" },
  "default_model": "llama",
  "options": { "temperature": 0.7, "top_p": 0.95 }
}
```

### Overrides and CLI helpers

- Environment:
  - `OLLAMARAMA_OLLAMA_URL` → `ollama.api_url`
  - `OLLAMARAMA_MODEL` → `ollama.default_model`
- CLI flags:
  - `--ollama-url` to override the API URL
  - `--model` to override the default model
  - `--server-models` to fetch available models from the server and exit

### Verify Connectivity

Check that the Ollama server is up and has models:
```
curl -s http://<host>:11434/api/tags | jq .
```

Minimal chat test (replace the model as needed):
```
curl -s http://<host>:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
        "model": "qwen3",
        "messages": [
          {"role": "system", "content": "you are a helpful assistant."},
          {"role": "user", "content": "hello"}
        ]
      }' | jq .
```

### Performance Tips
- GPU: ensure your GPU build is supported; confirm with `ollama run tinyllama "hello"` and monitor GPU usage.
- Context length: large contexts increase latency and memory; keep histories trimmed.
- Options: tune `temperature`, `top_p`, and penalties for stability vs. creativity.

### Remote Servers
If Ollama runs on another host:
- Set `ollama.api_url` to the remote server’s chat endpoint.
- Ensure network connectivity and that any reverse proxy forwards `POST /api/chat`.
- Consider TLS and authentication if the endpoint is exposed beyond localhost.

### Troubleshooting
- 404 or connection errors: is `ollama serve` running and reachable from the bot host?
- "model not found": pull the model and verify the exact name (e.g., `llama3.1:8b` vs `llama3.1`).
- Timeouts: increase `ollama.timeout` in the bot config or verify GPU/CPU load.
