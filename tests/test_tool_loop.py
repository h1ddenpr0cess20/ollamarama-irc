import sys
import types

# Provide a minimal stub for the 'irc' package to avoid external dependency
irc_pkg = types.ModuleType("irc")
irc_bot = types.ModuleType("irc.bot")


class _DummyIRCBot:
    def __init__(self, *args, **kwargs):
        self.connection = types.SimpleNamespace(privmsg=lambda *a, **k: None, notice=lambda *a, **k: None)

    def start(self):
        pass

    def disconnect(self, *args, **kwargs):
        pass


irc_bot.SingleServerIRCBot = _DummyIRCBot
sys.modules.setdefault("irc", irc_pkg)
sys.modules.setdefault("irc.bot", irc_bot)
setattr(irc_pkg, "bot", irc_bot)

from ollamarama_irc.app import AppContext
from ollamarama_irc.config import AppConfig, IrcConfig, OllamaConfig


class FakeOllama:
    def __init__(self):
        # First response requests a builtin tool; second gives the final message
        self._responses = [
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "t1",
                            "type": "function",
                            "function": {
                                "name": "calculate_expression",
                                "arguments": '{"expression": "2+2"}',
                            },
                        }
                    ],
                }
            },
            {"message": {"role": "assistant", "content": "4"}},
        ]

    def chat_with_tools(self, *, messages, model, options, tools, tool_choice=None, timeout=None):  # noqa: D401
        return self._responses.pop(0)


def make_cfg() -> AppConfig:
    irc = IrcConfig(server="irc.example.org", nickname="Bot", channels=["#c"], admins=[])
    ollama = OllamaConfig(
        api_url="http://localhost:11434/api/chat",
        options={},
        models={"q": "q"},
        default_model="q",
        prompt=["You are ", "."],
        personality="helper",
        history_size=8,
        timeout=5,
        mcp_servers={},
        verbose=False,
    )
    return AppConfig(irc=irc, ollama=ollama)


def test_tool_loop_uses_builtin_math():
    ctx = AppContext(make_cfg())
    # Monkeypatch the Ollama client to the fake one
    ctx.ollama = FakeOllama()  # type: ignore[assignment]

    # Seed messages list similar to a normal chat
    messages = [
        {"role": "system", "content": "You are helper."},
        {"role": "user", "content": "calculate 2+2"},
    ]
    out = ctx.respond_with_tools(messages, tool_choice="auto")
    assert out == "4"
    # Ensure the tool scaffolding was pruned from messages stored by the loop
    assert all("tool_calls" not in m for m in messages if isinstance(m, dict))
