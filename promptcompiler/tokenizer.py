"""Fast local token estimation.

This is deliberately approximate. The MVP needs stable local budgeting without
depending on a provider tokenizer or paid API call.
"""

from __future__ import annotations

import re


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", re.UNICODE)


def estimate_text_tokens(text: str) -> int:
    """Estimate tokens for a block of text."""

    if not text:
        return 0
    return len(_TOKEN_PATTERN.findall(text))


def estimate_segment_tokens(text: str) -> int:
    """Estimate chat-style segment tokens with small structural overhead."""

    if not text:
        return 0
    return estimate_text_tokens(text) + 4
