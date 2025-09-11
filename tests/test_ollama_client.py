import json
import types

import pytest

from ollamarama_irc.ollama_client import OllamaClient
from ollamarama_irc.exceptions import NetworkError, RuntimeFailure


class FakeResponse:
    def __init__(self, ok=True, status_code=200, data=None, text=None, raise_for_status=False):
        self.ok = ok
        self.status_code = status_code
        self._data = data
        self.text = text or ""
        self._raise = raise_for_status

    def raise_for_status(self):
        if self._raise or not self.ok or self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        if isinstance(self._data, types.SimpleNamespace) and getattr(self._data, "invalid", False):
            raise ValueError("invalid json")
        return self._data


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, json=None, timeout=None):  # noqa: A002 - json arg shadow ok in test
        self.calls.append(("POST", url, json))
        if url.endswith("/chat"):
            return FakeResponse(data={"message": {"content": "ok"}})
        return FakeResponse(status_code=404, raise_for_status=True)

    def get(self, url, timeout=None):
        self.calls.append(("GET", url, None))
        if url.endswith("/tags"):
            return FakeResponse(data={"models": [{"name": "m1"}, {"name": "m2"}]})
        return FakeResponse(status_code=404, raise_for_status=True)

    def head(self, url, timeout=None):
        self.calls.append(("HEAD", url, None))
        return FakeResponse()


def test_chat_and_chat_with_tools_success():
    client = OllamaClient(base_url="http://x/api", session=FakeSession())
    out = client.chat(model="m", messages=[{"role": "user", "content": "hi"}], options={})
    assert out.get("message", {}).get("content") == "ok"

    out2 = client.chat_with_tools(
        messages=[{"role": "user", "content": "hi"}],
        model="m",
        options={},
        tools=[{"type": "function", "function": {"name": "t", "parameters": {"type": "object"}}}],
    )
    assert out2.get("message", {}).get("content") == "ok"


def test_list_models_and_health():
    s = FakeSession()
    client = OllamaClient(base_url="http://x/api", session=s)
    models = client.list_models()
    assert isinstance(models, list) and any((m.get("name") == "m1") for m in models)
    assert client.health() is True


def test_network_and_json_errors():
    import requests

    class BadSession(FakeSession):
        def post(self, url, json=None, timeout=None):
            raise requests.RequestException("boom")

    client = OllamaClient(base_url="http://x/api", session=BadSession())
    with pytest.raises(NetworkError):
        client.chat(model="m", messages=[], options={})

    class JsonSession(FakeSession):
        def post(self, url, json=None, timeout=None):
            return FakeResponse(data=types.SimpleNamespace(invalid=True))

    client2 = OllamaClient(base_url="http://x/api", session=JsonSession())
    with pytest.raises(RuntimeFailure):
        client2.chat(model="m", messages=[], options={})
