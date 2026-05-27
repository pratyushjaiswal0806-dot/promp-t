"""Abstract storage repository protocol and data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class TraceRecord:
    trace_id: str
    endpoint: str = ""
    provider: str = ""
    model: str = ""
    session_id: str | None = None
    mode: str = ""
    original_token_count: int = 0
    optimized_token_count: int = 0
    token_reduction_percent: float = 0.0
    estimated_cost_before_usd: float = 0.0
    estimated_cost_after_usd: float = 0.0
    cache_status: str = "bypass"
    evaluation_status: str = "not_configured"
    zero_retention: bool = False
    latency_ms: int = 0
    transformations: list[dict[str, Any]] = field(default_factory=list)
    retention: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class SessionRecord:
    id: str
    provider: str = ""
    model: str = ""
    target_token_budget: int | None = None
    current_token_count: int = 0
    compression_mode: str = "lossless"
    zero_retention: bool = False
    compaction_count: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class TurnRecord:
    id: str
    session_id: str
    role: str = ""
    token_count: int = 0
    pinned: bool = False
    content: str | None = None
    is_summary: bool = False
    created_at: str = ""


@dataclass
class SessionState:
    session_id: str
    total_session_tokens: int = 0
    budget_utilization: float | None = None
    adaptive_management_triggered: bool = False
    summary_segment_id: str | None = None
    new_total_session_tokens: int = 0
    target_token_budget: int | None = None
    mode: str = ""
    retention: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheRecord:
    key: str
    value: dict[str, Any]
    created_at: str = ""
    ttl: int | None = None


@dataclass
class EmbeddingMatch:
    id: str
    text: str
    score: float = 0.0


@dataclass
class TraceFilter:
    provider: str | None = None
    model: str | None = None
    mode: str | None = None
    session_id: str | None = None
    since: str | None = None
    until: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass
class MetricFilter:
    provider: str | None = None
    model: str | None = None
    mode: str | None = None
    session_id: str | None = None


@dataclass
class MetricsResult:
    requests: int = 0
    original_tokens: int = 0
    optimized_tokens: int = 0
    tokens_saved: int = 0
    token_reduction_percent: float = 0.0
    estimated_cost_before_usd: float = 0.0
    estimated_cost_after_usd: float = 0.0
    estimated_cost_saved_usd: float = 0.0
    average_latency_ms: float = 0.0
    cache: dict[str, Any] = field(default_factory=dict)
    modes: dict[str, int] = field(default_factory=dict)
    sessions: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Repository Protocol
# ---------------------------------------------------------------------------


class Repository(Protocol):
    """Abstract storage backend for all promptcompiler data."""

    # Traces
    async def record_trace(self, trace: TraceRecord) -> None: ...
    async def get_trace(self, trace_id: str) -> TraceRecord | None: ...
    async def query_traces(self, filters: TraceFilter) -> list[TraceRecord]: ...

    # Sessions
    async def get_session(self, session_id: str) -> SessionRecord | None: ...
    async def upsert_session(self, session: SessionRecord) -> None: ...
    async def append_turn(self, session_id: str, turn: TurnRecord) -> SessionState: ...
    async def get_turns(self, session_id: str) -> list[TurnRecord]: ...

    # Cache
    async def get_cache(self, key: str) -> CacheRecord | None: ...
    async def set_cache(self, key: str, value: CacheRecord, ttl: int | None = None) -> None: ...
    async def invalidate_cache(self, pattern: str) -> int: ...

    # Embeddings
    async def get_embedding(self, key: str) -> list[float] | None: ...
    async def set_embedding(self, key: str, vector: list[float]) -> None: ...
    async def query_embeddings(self, vector: list[float], top_k: int) -> list[EmbeddingMatch]: ...

    # Provenance
    async def record_provenance(self, provenance: Any) -> None: ...
    async def get_provenance(self, input_hash: str, compiler_version: str) -> Any | None: ...

    # Metrics
    async def metrics(self, filters: MetricFilter) -> MetricsResult: ...
