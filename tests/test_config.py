import json
from pathlib import Path

from ollamarama_irc.config import load_config, validate_config


def write_tmp(tmp_path, data):
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(data))
    return p


def test_channel_normalization(tmp_path):
    data = {
        "irc": {"server": "irc.example.org", "nickname": "bot", "channel": "#chan", "admins": []},
        "ollama": {"api_url": "http://localhost:11434/api/chat", "models": {"m": "m"}, "default_model": "m", "prompt": ["You are ", "."], "personality": "p"},
    }
    path = write_tmp(tmp_path, data)
    cfg = load_config(path)
    assert cfg.irc.channels == ["#chan"]
    ok, errs = validate_config(cfg)
    assert ok, errs


def test_top_level_mcp_merge(tmp_path):
    data = {
        "irc": {"server": "irc.example.org", "nickname": "bot", "channels": ["#chan"], "admins": []},
        "ollama": {"api_url": "http://localhost:11434/api/chat", "models": {"m": "m"}, "default_model": "m", "prompt": ["a","b"], "personality": "p", "mcp_servers": {"a": "http://x"}},
        "mcp_servers": {"b": ["tool-b"]},
    }
    path = write_tmp(tmp_path, data)
    cfg = load_config(path)
    assert set(cfg.ollama.mcp_servers.keys()) == {"a", "b"}


def test_prompt_lengths(tmp_path):
    data = {
        "irc": {"server": "irc.example.org", "nickname": "bot", "channels": ["#chan"], "admins": []},
        "ollama": {"api_url": "http://localhost:11434/api/chat", "models": {"m": "m"}, "default_model": "m", "prompt": ["a","b","c"], "personality": "p"},
    }
    path = write_tmp(tmp_path, data)
    cfg = load_config(path)
    assert len(cfg.ollama.prompt) == 3
    ok, errs = validate_config(cfg)
    assert ok, errs

