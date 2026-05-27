"""Tokenizer protocol for token estimation."""

from __future__ import annotations

from typing import Protocol


class Tokenizer(Protocol):
    """A pluggable tokenizer.

    Implementations may wrap TikToken, HuggingFace tokenizers, or fall back
    to a regex heuristic.  Must be deterministic.
    """

    tokenizer_id: str
    version: str

    def encode(self, text: str) -> list[int]:
        """Tokenize *text* into a list of integer token IDs."""
        ...

    def decode(self, tokens: list[int]) -> str:
        """Decode *tokens* back into text."""
        ...

    def count(self, text: str) -> int:
        """Return the number of tokens in *text*."""
        return len(self.encode(text))
