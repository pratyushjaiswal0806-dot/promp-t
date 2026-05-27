"""Scorer protocol for semantic chunk similarity."""

from __future__ import annotations

from typing import Any, Protocol


class Scorer(Protocol):
    """A pluggable scorer for determining chunk similarity / redundancy.

    Implementations must be deterministic: same input chunks + policy must
    produce identical scores.
    """

    scorer_id: str
    version: str

    def score_chunks(
        self,
        chunks: list[dict[str, Any]],
        query: str,
        policy: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Score *chunks* and attach per-chunk scores and an edge-weight matrix.

        Each output chunk dict should include at minimum:
            - ``score``: float relevance to query
            - ``similarity_matrix``: dict[str, float] of {peer_chunk_id: similarity}
            - ``decision``: "retained" | "removed"
        """
        ...

    def similarity(self, tokens_a: list[str], tokens_b: list[str]) -> float:
        """Return a similarity score in [0, 1] between two token lists."""
        ...
