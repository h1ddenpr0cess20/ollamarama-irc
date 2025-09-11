from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests

from .exceptions import NetworkError, RuntimeFailure


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434/api", timeout: int = 180, session: Optional[requests.Session] = None) -> None:
        """Initialize an Ollama client.

        Args:
            base_url: Base API URL excluding path (``.../api``).
            timeout: Default request timeout in seconds.
            session: Optional pre-configured ``requests.Session`` instance.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = int(timeout)
        self._session = session or requests.Session()

    def chat(self, *, model: str, messages: List[Dict[str, str]], options: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """Send a non-streaming chat request.

        Args:
            model: Model identifier or name.
            messages: Conversation messages as role/content dicts.
            options: Model-specific options.
            timeout: Optional per-request timeout override.

        Returns:
            Parsed JSON response from the server.

        Raises:
            NetworkError: On HTTP request failures.
            RuntimeFailure: When the server returns invalid JSON.
        """
        url = f"{self.base_url}/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options or {},
        }
        if timeout is not None:
            payload["timeout"] = int(timeout)
        try:
            resp = self._session.post(url, json=payload, timeout=(self.timeout if timeout is None else int(timeout)))
            resp.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e))
        try:
            return resp.json()
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from Ollama: {e}")

    def chat_with_tools(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: str,
        options: Optional[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: Optional[str] = "auto",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Send a chat request with tool calling enabled.

        Args:
            messages: Conversation messages as role/content dicts.
            model: Model identifier or name.
            options: Model-specific options or ``None``.
            tools: Tool schema definitions.
            tool_choice: Tool selection strategy or ``None`` to disable.
            timeout: Optional per-request timeout override.

        Returns:
            Parsed JSON response from the server.

        Raises:
            NetworkError: On HTTP request failures.
            RuntimeFailure: When the server returns invalid JSON.
        """
        url = f"{self.base_url}/chat"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options or {},
            "tools": tools,
        }
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if timeout is not None:
            payload["timeout"] = int(timeout)
        try:
            resp = self._session.post(url, json=payload, timeout=(self.timeout if timeout is None else int(timeout)))
            resp.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e))
        try:
            return resp.json()
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from Ollama: {e}")

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models (tags) from the Ollama server.

        Returns:
            A list of model tag dictionaries.

        Raises:
            NetworkError: On HTTP request failures.
            RuntimeFailure: When the server returns invalid JSON.
        """
        url = f"{self.base_url}/tags"
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json() or {}
            # Ollama returns {"models": [{"name": ...}, ...]}
            models = data.get("models")
            if isinstance(models, list):
                return models  # type: ignore[return-value]
            # Fallback: if array already
            if isinstance(data, list):
                return data  # type: ignore[return-value]
            return []
        except requests.RequestException as e:
            raise NetworkError(str(e))
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from Ollama: {e}")

    def health(self) -> bool:
        """Check server health by querying the tags endpoint.

        Returns:
            ``True`` when the server responds successfully, else ``False``.
        """
        try:
            _ = self.list_models()
            return True
        except Exception:
            return False
