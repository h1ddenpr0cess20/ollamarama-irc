## Docker

This guide covers building and running the Ollamarama IRC bot with Docker and Docker Compose. The image is minimal and runs the bot against a reachable Ollama server.

## Prerequisites

- Docker 20.10+
- Optional: Docker Compose v2 (`docker compose`)
- An IRC configuration (`config.json`) and an accessible Ollama server

## Build the Image

Build from the repo root:

```
docker build -t ollamarama-irc:latest .
```

What the image does:

- Installs Python dependencies from `requirements.txt` via `pip install .`
- Runs the app as `python -m ollamarama_irc -c config.json`
- Looks for `config.json` in `/app` by default

## Run with Docker

1) Prepare configuration on the host:

```
cp config.json ./config.json  # ensure it contains IRC server, nick, channels, models
```

2) Run the container (connects to an existing Ollama server):

```
docker run --rm -it \
  --name ollamarama-irc \
  -v "$(pwd)/config.json":/app/config.json:ro \
  -e OLLAMARAMA_OLLAMA_URL=http://<host>:11434/api/chat \
  -e OLLAMARAMA_LOG_FORMAT=plain \
  ollamarama-irc:latest
```

Notes:

- Replace `<host>` with your Ollama server host if not local.
- The bot does not expose ports; it connects out to the IRC network and Ollama.
- Prefer `OLLAMARAMA_LOG_FORMAT=plain` for clean logs in containers.

## Run with Docker Compose

This repo includes a simple `docker-compose.yml` that starts only the bot and points it at an external Ollama server.

1) Ensure your `config.json` is present at the repo root and contains IRC server, channels, and model selection. The compose file sets `OLLAMARAMA_OLLAMA_URL` (default points to `host.docker.internal`).

2) Start the bot:

```
docker compose up -d --build
```

3) Follow logs:

```
docker compose logs -f bot
```

If you want to include an Ollama service in Compose, add a service for `ollama` (publishing `11434`) and change `OLLAMARAMA_OLLAMA_URL` to `http://ollama:11434/api/chat`.

## Configuration

- File: mount your `config.json` at `/app/config.json` (read‑only recommended).
- Overrides: you can override selected fields via environment variables:
  - `OLLAMARAMA_OLLAMA_URL` → `ollama.api_url`
  - `OLLAMARAMA_MODEL` → `ollama.default_model`
  - `OLLAMARAMA_IRC_SERVER` → `irc.server`

See [Configuration](configuration.md) for the full schema and validation rules.

## Security Notes

- Keep `config.json` outside the image and mount it read‑only.
- Do not commit secrets. Redact sensitive values in logs and tickets.
- Limit outbound network access if you enable tools that make network requests.

## Troubleshooting

- No replies: verify the bot joined the channel(s) and that the Ollama API is reachable from the container.
- Models missing: pull the model on your Ollama server and confirm names.
- Flood/rate limits: adjust the bot’s pacing or your IRC server’s limits.
- Increase verbosity: set `-e OLLAMARAMA_LOG_LEVEL=DEBUG`.
