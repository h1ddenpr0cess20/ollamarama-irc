import asyncio

from ollamarama_irc.handlers.cmd_ai import make_ai_handler, make_x_handler
from ollamarama_irc.handlers.cmd_prompt import make_persona_handler, make_custom_handler
from ollamarama_irc.handlers.cmd_reset import make_reset_handler, make_stock_handler
from ollamarama_irc.handlers.cmd_model import make_model_handler
from ollamarama_irc.history import HistoryStore


class FakeIRC:
    def __init__(self):
        self.sent = []
        self.notices = []

    def send_message(self, channel, text):
        self.sent.append((channel, text))

    def send_notice(self, nick, text):
        self.notices.append((nick, text))


class FakeCtx:
    def __init__(self):
        self.nickname = "Bot"
        self.models = {"m": "m", "q": "q"}
        self.default_model = "m"
        self.model = "m"
        self.default_personality = "helper"
        self.personality = "helper"
        self.options = {}
        self.timeout = 5
        self.irc = FakeIRC()
        self.history = HistoryStore(
            prompt_prefix="You are ", prompt_suffix=".", personality="helper", prompt_suffix_extra=" Be brief.", max_items=8
        )
        self.cfg = type("Cfg", (), {"irc": type("I", (), {"admins": ["admin"]})})
        self.log = type("Log", (), {"info": lambda *a, **k: None})()

    async def respond(self, channel, user, sender2=None):
        # Pretend model returned fixed answer
        self.history.add(channel, user, "assistant", "ok")
        self.irc.send_message(channel, f"{sender2 or user}:")
        self.irc.send_message(channel, "ok")


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_ai_and_persona_and_custom_flow():
    ctx = FakeCtx()
    ai = make_ai_handler(ctx)
    persona = make_persona_handler(ctx)
    custom = make_custom_handler(ctx)
    ch = "#c"
    u = "alice"
    # persona sets prompt and responds
    run(persona(ch, u, [".persona", "pirate"]))
    assert any("pirate" in m["content"] for m in ctx.history.get(ch, u) if m["role"] == "system")
    # ai appends and responds
    run(ai(ch, u, [".ai", "hello"]))
    msgs = ctx.history.get(ch, u)
    assert msgs[-2]["role"] == "user" and "hello" in msgs[-2]["content"]
    # custom replaces prompt and responds
    run(custom(ch, u, [".custom", "You are a test."]))
    msgs = ctx.history.get(ch, u)
    assert msgs[0]["role"] == "system" and "You are a test." in msgs[0]["content"]


def test_x_handler_targets_existing_history():
    ctx = FakeCtx()
    xh = make_x_handler(ctx)
    ch = "#c"
    target = "bob"
    # seed target prompt so history exists
    ctx.history.init_prompt(ch, target, persona="pirate")
    run(xh(ch, "alice", [".x", target, "hi there"]))
    # should have responded addressing alice
    assert any(s[1] == "alice:" for s in ctx.irc.sent)


def test_reset_and_stock():
    ctx = FakeCtx()
    reset = make_reset_handler(ctx)
    stock = make_stock_handler(ctx)
    ch = "#c"
    u = "alice"
    ctx.history.init_prompt(ch, u, persona="pirate")
    run(reset(ch, u, [".reset"]))
    msgs = ctx.history.get(ch, u)
    assert msgs and msgs[0]["role"] == "system"
    run(stock(ch, u, [".stock"]))
    assert ctx.history.get(ch, u) == [] or ctx.history.get(ch, u)[0]["role"] == "system"


def test_model_handler():
    ctx = FakeCtx()
    mh = make_model_handler(ctx)
    ch = "#c"
    admin = "admin"
    # list
    run(mh(ch, admin, [".model"]))
    # set by key
    run(mh(ch, admin, [".model", "q"]))
    assert ctx.model == "q"
    # reset
    run(mh(ch, admin, [".model", "reset"]))
    assert ctx.model == ctx.default_model

