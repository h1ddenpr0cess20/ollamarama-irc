from __future__ import annotations

import re
from typing import Dict, Any


def text_stats(text: str) -> Dict[str, Any]:
    """Compute simple statistics for a given text.

    Args:
        text: Input text to analyze.

    Returns:
        A mapping with counts for:
        - ``words``: Number of word tokens.
        - ``characters``: Total character count.
        - ``sentences``: Number of sentence terminators (., !, ?).
    """
    if not isinstance(text, str) or not text.strip():
        return {"words": 0, "characters": 0, "sentences": 0}
    words = re.findall(r"\b\w+\b", text)
    sentences = re.findall(r"[.!?]+", text)
    return {
        "words": len(words),
        "characters": len(text),
        "sentences": len(sentences),
    }
