"""Core IR node: Segment and its supporting types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class ContextRole(Enum):
    """The role a segment plays in the overall prompt context."""

    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()
    TOOL_OUTPUT = auto()
    PLAN = auto()
    MEMORY = auto()
    SCRATCHPAD = auto()
    RETRIEVAL = auto()
    INSTRUCTION = auto()
    EXAMPLE = auto()
    REFERENCE = auto()
    UNKNOWN = auto()


class SegmentType(Enum):
    """Structural type of a segment."""

    TEXT = auto()
    STRUCTURED = auto()
    CODE = auto()
    ACTOR = auto()
    TOOL_SCHEMA = auto()


@dataclass(frozen=True)
class SourceRef:
    """Original source location of an IR node."""
    uri: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    retrieval_index: int | None = None
    provenance_id: str | None = None


@dataclass(frozen=True)
class PolicyBinding:
    """A policy attached to this segment or its subtree."""
    policy_id: str
    scope: str = "self"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformRecord:
    """Record of a single transformation applied to a node."""
    pass_id: str
    pass_version: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeMetadata:
    """Mutable metadata attached to an IR node."""
    tokens_original: int = 0
    tokens_after: int = 0
    entity_ids: set[str] = field(default_factory=set)
    risk_score: float = 0.0
    attention_weight: float = 1.0
    priority_score: float = 1.0
    is_pinned: bool = False
    is_summary: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Segment:
    """A single segment in the IR graph — the fundamental IR node.

    Every segment carries its original text, a typed role, source provenance,
    attached policies, a transformation history, and mutable metadata computed
    by compiler passes.
    """

    id: str = field(default_factory=lambda: f"seg_{uuid4().hex[:12]}")
    text: str = ""
    segment_type: SegmentType = SegmentType.TEXT
    context_role: ContextRole = ContextRole.UNKNOWN
    source: SourceRef | None = None
    policies: list[PolicyBinding] = field(default_factory=list)
    transforms: list[TransformRecord] = field(default_factory=list)
    metadata: NodeMetadata | None = None
    children: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = NodeMetadata(tokens_original=0, tokens_after=0)

    @property
    def is_pinned(self) -> bool:
        return self.metadata is not None and self.metadata.is_pinned
