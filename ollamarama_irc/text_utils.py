from __future__ import annotations


def strip_thinking_markers(text: str) -> str:
    """Remove hidden "thinking" markers from model output.

    Supports several common marker formats such as
    ``<|begin_of_solution|>…<|end_of_solution|>``,
    ``<think>…</think>``, and
    ``<|begin_of_thought|>…<|end_of_thought|>``.

    Args:
        text: Raw model output string.

    Returns:
        The cleaned text with thinking segments removed and whitespace trimmed.
    """
    out = text or ""
    try:
        if "<|begin_of_solution|>" in out and "<|end_of_solution|>" in out:
            out = out.split("<|begin_of_solution|>", 1)[1].split("<|end_of_solution|>", 1)[0]
    except Exception:
        pass
    try:
        if "<think>" in out and "</think>" in out:
            _, rest = out.split("</think>", 1)
            out = rest
    except Exception:
        pass
    try:
        if "<|begin_of_thought|>" in out and "<|end_of_thought|>" in out:
            parts = out.split("<|end_of_thought|>")
            if len(parts) > 1:
                out = parts[1]
    except Exception:
        pass
    return out.strip()
