"""Fast local token estimation.

Attempts to use tiktoken for accurate OpenAI-compatible token counts,
falling back to a fast regex estimation when tiktoken is unavailable.
"""

from __future__ import annotations

import re
from typing import Any


_ENCODING: Any = None
_HAS_TIKTOKEN = False

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("cl100k_base")
    _HAS_TIKTOKEN = True
except ImportError:
    _TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", re.UNICODE)


def estimate_text_tokens(text: str) -> int:
    """Estimate tokens for a block of text."""
    if not text:
        return 0
    if _HAS_TIKTOKEN:
        return len(_ENCODING.encode(text, disallowed_special=()))
    return len(_TOKEN_PATTERN.findall(text))


def estimate_segment_tokens(text: str) -> int:
    """Estimate chat-style segment tokens with small structural overhead."""
    if not text:
        return 0
    return estimate_text_tokens(text) + 4
