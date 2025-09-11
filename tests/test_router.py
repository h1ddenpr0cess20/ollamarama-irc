import asyncio

from ollamarama_irc.handlers.router import CommandRouter


async def _dummy(channel, sender, tokens):
    return channel, sender, tokens


def test_router_dispatch_and_mention():
    r = CommandRouter(nickname="Bot")
    called = {}

    async def ai(channel, sender, tokens):
        called["ai"] = (channel, sender, tokens)

    r.register(".ai", ai)

    # direct command
    asyncio.get_event_loop().run_until_complete(r.dispatch("#c", "alice", ".ai hello there"))
    assert called["ai"][2] == [".ai", "hello", "there"]

    # mention form
    asyncio.get_event_loop().run_until_complete(r.dispatch("#c", "alice", "Bot: hi"))
    assert called["ai"][2] == ["Bot:", "hi"]

