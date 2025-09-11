from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os
import logging


log = logging.getLogger("ollamarama_irc")


@dataclass
class IrcConfig:
    server: str
    nickname: str
    password: Optional[str] = None
    channels: List[str] = field(default_factory=list)
    admins: List[str] = field(default_factory=list)


@dataclass
class OllamaConfig:
    api_url: str
    options: Dict[str, Any] = field(default_factory=dict)
    models: Dict[str, str] = field(default_factory=dict)
    default_model: str = ""
    prompt: List[str] = field(default_factory=lambda: ["You are ", "."])
    personality: str = "a helpful assistant"
    history_size: int = 24
    timeout: int = 180
    mcp_servers: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False


@dataclass
class AppConfig:
    irc: IrcConfig
    ollama: OllamaConfig


def _normalize_channels(raw: Dict[str, Any]) -> List[str]:
    """Normalize channel configuration to a list of names.

    Accepts legacy ``irc.channel`` (single string) or modern ``irc.channels``
    (list of strings) and returns a clean list.

    Args:
        raw: Raw ``irc`` section mapping from the config.

    Returns:
        A list of channel names to join.
    """
    # Back-compat: support legacy single "channel" string
    channels = []
    if "channels" in raw and isinstance(raw["channels"], list):
        channels = [c for c in raw["channels"] if c]
    elif "channel" in raw and isinstance(raw["channel"], str):
        if raw["channel"]:
            channels = [raw["channel"]]
    return channels


def _deep_update(base: dict, updates: dict) -> dict:
    """Recursively update mapping ``base`` with values from ``updates``.

    Args:
        base: Destination mapping to update in place.
        updates: Mapping of changes to apply; nested dicts are merged.

    Returns:
        The updated ``base`` mapping.
    """
    for k, v in (updates or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _deep_update(dict(base[k]), v)
        else:
            base[k] = v
    return base


def load_config(path: Path | str, *, env: Optional[Dict[str, str]] = None, overrides: Optional[Dict[str, Any]] = None) -> AppConfig:
    """Load and normalize configuration from a JSON file.

    Applies selected environment variable overrides and optional caller
    overrides for convenience.

    Args:
        path: Path to the ``config.json`` file.
        env: Optional environment mapping to read overrides from.
        overrides: Optional mapping to deep-merge onto the config.

    Returns:
        A validated ``AppConfig`` object.

    Raises:
        ValueError: If required sections are missing or essential fields empty.
    """
    p = Path(path)
    data = json.loads(p.read_text())

    # Validate sections exist
    if "irc" not in data or "ollama" not in data:
        raise ValueError("Config must contain 'irc' and 'ollama' sections")

    env = env or os.environ
    # Apply selected ENV overrides
    env_over: Dict[str, Any] = {}
    if env.get("OLLAMARAMA_OLLAMA_URL"):
        env_over.setdefault("ollama", {})["api_url"] = env["OLLAMARAMA_OLLAMA_URL"]
    if env.get("OLLAMARAMA_MODEL"):
        env_over.setdefault("ollama", {})["default_model"] = env["OLLAMARAMA_MODEL"]
    if env.get("OLLAMARAMA_IRC_SERVER"):
        env_over.setdefault("irc", {})["server"] = env["OLLAMARAMA_IRC_SERVER"]
    if env_over:
        data = _deep_update(data, env_over)
    if overrides:
        data = _deep_update(data, overrides)

    irc_raw = data["irc"]
    ollama_raw = data["ollama"]
    # Back-compat: allow top-level mcp_servers to merge into ollama section
    try:
        top_mcp = data.get("mcp_servers")
        if isinstance(top_mcp, dict):
            existing = ollama_raw.get("mcp_servers")
            if not isinstance(existing, dict):
                ollama_raw["mcp_servers"] = dict(top_mcp)
            else:
                merged = dict(existing)
                merged.update(top_mcp)
                ollama_raw["mcp_servers"] = merged
    except Exception:
        pass

    # Deprecation warning for legacy key
    try:
        if isinstance(data.get("irc"), dict) and "channel" in data["irc"] and "channels" not in data["irc"]:
            log.warning("Config key 'irc.channel' is deprecated; use 'irc.channels' instead (will be normalized).")
    except Exception:
        pass

    irc_cfg = IrcConfig(
        server=str(irc_raw.get("server", "")),
        nickname=str(irc_raw.get("nickname", "ollamarama")),
        password=irc_raw.get("password"),
        channels=_normalize_channels(irc_raw),
        admins=list(irc_raw.get("admins", [])),
    )

    if not irc_cfg.server:
        raise ValueError("IRC server is required in config.irc.server")
    if not irc_cfg.channels:
        raise ValueError("At least one IRC channel is required (irc.channels or legacy irc.channel)")

    prompt_list = list(ollama_raw.get("prompt", ["You are ", "."]))
    if not (2 <= len(prompt_list) <= 3):
        prompt_list = ["You are ", "."]

    ollama_cfg = OllamaConfig(
        api_url=str(ollama_raw.get("api_url", "http://localhost:11434/api/chat")),
        options=dict(ollama_raw.get("options", {})),
        models=dict(ollama_raw.get("models", {})),
        default_model=str(ollama_raw.get("default_model", "")),
        prompt=prompt_list[:3],
        personality=str(ollama_raw.get("personality", "a helpful assistant")),
        history_size=int(ollama_raw.get("history_size", 24)),
        timeout=int(ollama_raw.get("timeout", 180)),
        mcp_servers=dict(ollama_raw.get("mcp_servers", {})),
        verbose=bool(ollama_raw.get("verbose", False)),
    )

    if not ollama_cfg.default_model:
        # If missing, but a models mapping exists, pick the first key
        if ollama_cfg.models:
            ollama_cfg.default_model = next(iter(ollama_cfg.models.values()))

    return AppConfig(irc=irc_cfg, ollama=ollama_cfg)


def validate_config(cfg: AppConfig) -> Tuple[bool, List[str]]:
    """Validate an ``AppConfig`` instance and collect errors.

    Args:
        cfg: The configuration to validate.

    Returns:
        Tuple of ``(ok, errors)`` where ``ok`` is ``True`` when validation
        passes, otherwise ``False`` with human-readable error messages.
    """
    errors: List[str] = []
    # IRC validation
    if not isinstance(cfg.irc.server, str) or not cfg.irc.server.strip():
        errors.append("irc.server must be a non-empty string (hostname or address)")
    if not isinstance(cfg.irc.nickname, str) or not cfg.irc.nickname.strip():
        errors.append("irc.nickname must be a non-empty string")
    if not isinstance(cfg.irc.channels, list) or not cfg.irc.channels:
        errors.append("irc.channels must be a non-empty list (or provide legacy irc.channel)")
    else:
        bad = [c for c in cfg.irc.channels if not isinstance(c, str) or not c.startswith("#")]
        if bad:
            errors.append(f"irc.channels entries must start with '#': {bad}")
    if not isinstance(cfg.irc.admins, list):
        errors.append("irc.admins must be a list of nicknames")

    # Ollama validation
    if not isinstance(cfg.ollama.api_url, str) or not cfg.ollama.api_url.startswith("http"):
        errors.append("ollama.api_url must be an http(s) URL")
    if not isinstance(cfg.ollama.models, dict):
        errors.append("ollama.models must be a mapping of name→id")
    if not isinstance(cfg.ollama.default_model, str) or not cfg.ollama.default_model:
        errors.append("ollama.default_model must be a non-empty string")
    else:
        try:
            models = cfg.ollama.models or {}
            if isinstance(models, dict) and (
                cfg.ollama.default_model not in models
                and cfg.ollama.default_model not in set(models.values())
            ):
                errors.append("ollama.default_model must match a key or id in ollama.models")
        except Exception:
            pass
    if not isinstance(cfg.ollama.prompt, list) or len(cfg.ollama.prompt) not in (2, 3) or not all(isinstance(p, str) for p in cfg.ollama.prompt):
        errors.append("ollama.prompt must be a list of 2 or 3 strings [prefix, suffix, (optional brevity clause)]")
    if not isinstance(cfg.ollama.personality, str) or not cfg.ollama.personality:
        errors.append("ollama.personality must be a non-empty string")
    if not (1 <= int(cfg.ollama.history_size) <= 1000):
        errors.append("ollama.history_size must be between 1 and 1000")
    if not isinstance(cfg.ollama.mcp_servers, dict):
        errors.append("ollama.mcp_servers must be a mapping if provided")
    # Options ranges
    opts = cfg.ollama.options or {}
    temp = opts.get("temperature")
    if temp is not None:
        try:
            if not (0 <= float(temp) <= 2):
                errors.append("ollama.options.temperature must be between 0 and 2")
        except Exception:
            errors.append("ollama.options.temperature must be numeric")
    top_p = opts.get("top_p")
    if top_p is not None:
        try:
            if not (0 < float(top_p) <= 1):
                errors.append("ollama.options.top_p must be >0 and ≤1")
        except Exception:
            errors.append("ollama.options.top_p must be numeric")
    rp = opts.get("repeat_penalty")
    if rp is not None:
        try:
            if not (0.5 <= float(rp) <= 2):
                errors.append("ollama.options.repeat_penalty must be between 0.5 and 2")
        except Exception:
            errors.append("ollama.options.repeat_penalty must be numeric")

    return (len(errors) == 0, errors)
