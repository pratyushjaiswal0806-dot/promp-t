"""Storage abstraction layer for promptcompiler v2.

This package re-exports the v1 SQLiteStore for backward compatibility while
adding the new Repository Protocol-based abstraction.
"""

from __future__ import annotations

# Re-export v1 storage for backward compatibility
from promptcompiler.storage_v1 import (
    DEFAULT_DB_PATH,
    SQLiteStore,
    ROOT,
    _COMPACTION_TRIGGER_THRESHOLD,
    _COMPACTION_SUMMARY_RATIO,
    _now,
    _trace_from_row,
    _budget_utilization,
    get_store,
)

from .repository import (
    Repository,
    TraceRecord,
    SessionRecord,
    TurnRecord,
    SessionState,
    CacheRecord,
    EmbeddingMatch,
    TraceFilter,
    MetricFilter,
    MetricsResult,
)

__all__ = [
    # v1 backward compat
    "DEFAULT_DB_PATH",
    "SQLiteStore",
    "ROOT",
    "get_store",
    # v2 protocol
    "Repository",
    "TraceRecord",
    "SessionRecord",
    "TurnRecord",
    "SessionState",
    "CacheRecord",
    "EmbeddingMatch",
    "TraceFilter",
    "MetricFilter",
    "MetricsResult",
]
