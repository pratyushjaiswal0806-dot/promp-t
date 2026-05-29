"""Fast local token estimation.

Attempts to use tiktoken for accurate OpenAI-compatible token counts,
falling back to a fast regex estimation when tiktoken is unavailable.
Supports per-model encoding selection with approximation warnings.
"""

from __future__ import annotations

import re
import warnings
from typing import Any


_ENCODING: Any = None
_HAS_TIKTOKEN = False

try:
    import tiktoken

    _HAS_TIKTOKEN = True
except ImportError:
    _TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", re.UNICODE)

# Model prefix → tiktoken encoding name mapping.
# Ordered most-to-least specific; first match wins.
_MODEL_ENCODING_MAP: list[tuple[str, str]] = [
    # OpenAI o-series / GPT-4o family (o200k_base)
    ("o1-", "o200k_base"),
    ("o3-", "o200k_base"),
    ("gpt-4o", "o200k_base"),
    ("gpt-4a", "o200k_base"),
    ("gpt-4-turbo", "cl100k_base"),
    ("gpt-4-", "cl100k_base"),
    ("gpt-3.5-turbo", "cl100k_base"),
    ("gpt-35-turbo", "cl100k_base"),
    ("gpt-3.5-", "cl100k_base"),
    ("gpt-35-", "cl100k_base"),
    ("text-embedding-ada", "cl100k_base"),
    ("text-embedding-3", "cl100k_base"),
    # NVIDIA NIM OpenAI-compatible models default to cl100k_base
    ("openai/gpt-oss", "cl100k_base"),
    ("openai/gpt-4", "cl100k_base"),
    ("nvidia/llama", "cl100k_base"),
    ("nvidia/nemotron", "cl100k_base"),
    ("meta/llama", "cl100k_base"),
    ("deepseek-ai/deepseek", "cl100k_base"),
    ("qwen/", "cl100k_base"),
]

# Known encoding names that can be loaded on demand
_KNOWN_ENCODINGS: set[str] = {"cl100k_base", "o200k_base", "p50k_base", "r50k_base"}

_ACTIVE_ENCODING: Any = None
_ACTIVE_ENCODING_NAME: str = ""
_ACTIVE_MODEL_WARNED: set[str] = set()


def _load_encoding(name: str) -> Any:
    if not _HAS_TIKTOKEN:
        return None
    try:
        return tiktoken.get_encoding(name)
    except Exception:
        return None


def set_active_model(model: str | None) -> None:
    """Set the active model so subsequent token estimates use the right encoding.

    Call at the start of a compilation. Pass ``None`` to reset to the default
    (``cl100k_base``, no warnings).
    """
    global _ACTIVE_ENCODING, _ACTIVE_ENCODING_NAME

    if not model or not _HAS_TIKTOKEN:
        _ACTIVE_ENCODING = None
        _ACTIVE_ENCODING_NAME = ""
        return

    for prefix, enc_name in _MODEL_ENCODING_MAP:
        if model.lower().startswith(prefix):
            enc = _load_encoding(enc_name)
            if enc is not None:
                _ACTIVE_ENCODING = enc
                _ACTIVE_ENCODING_NAME = enc_name
            else:
                _ACTIVE_ENCODING = None
                _ACTIVE_ENCODING_NAME = ""
            return

    # Unknown model — warn once per model and fall back to cl100k_base
    if model not in _ACTIVE_MODEL_WARNED:
        _ACTIVE_MODEL_WARNED.add(model)
        warnings.warn(
            f"Unknown model '{model}' — no exact tokenizer mapping available. "
            f"Falling back to cl100k_base approximation. Token counts may be off.",
            stacklevel=2,
        )
    enc = _load_encoding("cl100k_base")
    _ACTIVE_ENCODING = enc
    _ACTIVE_ENCODING_NAME = "cl100k_base"


def _resolve_encoding() -> tuple[Any, str]:
    if _ACTIVE_ENCODING is not None:
        return _ACTIVE_ENCODING, _ACTIVE_ENCODING_NAME
    if _HAS_TIKTOKEN:
        global _ENCODING
        if _ENCODING is None:
            _ENCODING = tiktoken.get_encoding("cl100k_base")
        return _ENCODING, "cl100k_base"
    return None, "regex-fallback"


def estimate_text_tokens(text: str, model: str | None = None) -> int:
    """Estimate tokens for a block of text.

    If *model* is supplied it overrides the active model (set via
    :func:`set_active_model`).  Pass ``model=None`` (the default) to
    use whatever encoding is currently active.
    """
    if not text:
        return 0
    if model is not None:
        old_enc, old_name = _ACTIVE_ENCODING, _ACTIVE_ENCODING_NAME
        set_active_model(model)
        enc, _ = _resolve_encoding()
        _ACTIVE_ENCODING, _ACTIVE_ENCODING_NAME = old_enc, old_name
    else:
        enc, _ = _resolve_encoding()
    if enc is not None:
        return len(enc.encode(text, disallowed_special=()))
    return len(_TOKEN_PATTERN.findall(text))


def estimate_segment_tokens(text: str, model: str | None = None) -> int:
    """Estimate chat-style segment tokens with small structural overhead."""
    if not text:
        return 0
    return estimate_text_tokens(text, model=model) + 4
