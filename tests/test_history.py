from ollamarama_irc.history import HistoryStore


def test_history_persona_and_reset():
    h = HistoryStore(prompt_prefix="You are ", prompt_suffix=".", personality="helper", prompt_suffix_extra=" Be brief.", max_items=6)
    h.set_verbose(False)
    ch = "#a"
    user = "alice"
    # persona init
    h.init_prompt(ch, user, persona="pirate")
    msgs = h.get(ch, user)
    assert msgs[0]["role"] == "system"
    assert "pirate" in msgs[0]["content"]
    # add messages and trim
    for i in range(6):
        h.add(ch, user, "user", f"u{i}")
    assert len(h.get(ch, user)) <= 6
    # reset stock leaves empty
    h.reset(ch, user, stock=True)
    assert h.get(ch, user) == [] or h.get(ch, user)[0]["role"] == "system"
    # reset default seeds prompt
    h.reset(ch, user, stock=False)
    msgs = h.get(ch, user)
    assert msgs and msgs[0]["role"] == "system"


def test_verbose_omits_extra_suffix():
    h = HistoryStore(prompt_prefix="You are ", prompt_suffix=".", personality="helper", prompt_suffix_extra=" Be brief.")
    h.set_verbose(True)
    h.init_prompt("#a", "bob")
    msgs = h.get("#a", "bob")
    assert "Be brief." not in msgs[0]["content"]

