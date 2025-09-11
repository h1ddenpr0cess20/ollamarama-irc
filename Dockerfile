FROM python:3.11-slim

WORKDIR /app

# Install system deps as needed (none required by default)

# Copy packaging metadata and install
COPY pyproject.toml README.md LICENSE ./
COPY ollamarama_irc ./ollamarama_irc
COPY help.md ./
COPY docs ./docs

RUN pip install --no-cache-dir .

# Default: look for config.json in /app
CMD ["python", "-m", "ollamarama_irc", "-c", "config.json"]

