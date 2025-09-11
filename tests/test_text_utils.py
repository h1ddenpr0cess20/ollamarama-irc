from ollamarama_irc.text_utils import strip_thinking_markers


def test_strip_thinking_tags():
    s1 = "<think>foo</think> answer here"
    assert strip_thinking_markers(s1) == "answer here"
    s2 = "<|begin_of_thought|>thinking<|end_of_thought|> actual"
    assert strip_thinking_markers(s2) == "actual"
    s3 = "<|begin_of_solution|>final<|end_of_solution|> extra"
    assert strip_thinking_markers(s3) == "final"

