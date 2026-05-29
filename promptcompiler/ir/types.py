"""Flat IR types — all data structures used by the v2 pass pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from hashlib import sha256
from typing import Any
from uuid import uuid4


class ContextRole(Enum):
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
    TEXT = auto()
    STRUCTURED = auto()
    CODE = auto()
    ACTOR = auto()
    TOOL_SCHEMA = auto()


@dataclass(frozen=True)
class SourceRef:
    uri: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    retrieval_index: int | None = None
    provenance_id: str | None = None


@dataclass(frozen=True)
class PolicyBinding:
    policy_id: str
    scope: str = "self"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformRecord:
    pass_id: str
    pass_version: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeMetadata:
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


@dataclass(frozen=True)
class Entity:
    id: str
    surface_form: str
    canonical_form: str | None = None
    entity_type: str = "unknown"
    confidence: float = 1.0


@dataclass
class EntityRelation:
    source_id: str
    target_id: str
    relation_type: str = "co_occurs"
    weight: float = 1.0


@dataclass
class EntityGraph:
    entities: dict[str, Entity] = field(default_factory=dict)
    relations: list[EntityRelation] = field(default_factory=list)
    segment_to_entities: dict[str, set[str]] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def link_entity(self, segment_id: str, entity_id: str) -> None:
        self.segment_to_entities.setdefault(segment_id, set()).add(entity_id)

    def entities_for_segment(self, segment_id: str) -> list[Entity]:
        eids = self.segment_to_entities.get(segment_id, set())
        return [self.entities[eid] for eid in eids if eid in self.entities]

    def merge(self, other: EntityGraph) -> None:
        self.entities.update(other.entities)
        self.relations.extend(other.relations)
        for sid, eids in other.segment_to_entities.items():
            self.segment_to_entities.setdefault(sid, set()).update(eids)


@dataclass
class ProvenanceChain:
    output_segment_id: str
    original_segment_ids: list[str] = field(default_factory=list)
    transforms: list[TransformRecord] = field(default_factory=list)
    risk_score: float = 0.0
    preservation_status: str = "full"
    missing_entities: list[str] = field(default_factory=list)


@dataclass
class CompilationProvenance:
    input_hash: str = ""
    compiler_version: str = ""
    pipeline_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    segments: dict[str, ProvenanceChain] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)

    def verify_replay(self, other: CompilationProvenance) -> bool:
        return (
            self.input_hash == other.input_hash
            and self.compiler_version == other.compiler_version
            and self.pipeline_id == other.pipeline_id
        )


@dataclass
class ContextGraph:
    segments: dict[str, Segment] = field(default_factory=dict)
    entities: EntityGraph = field(default_factory=EntityGraph)
    provenance: dict[str, ProvenanceChain] = field(default_factory=dict)
    root_segments: list[str] = field(default_factory=list)
    compiler_version: str = ""
    pipeline_config: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    def add_segment(self, segment: Segment, *, is_root: bool = True) -> str:
        self.segments[segment.id] = segment
        if is_root:
            self.root_segments.append(segment.id)
        return segment.id

    def remove_segment(self, segment_id: str) -> None:
        self.segments.pop(segment_id, None)
        if segment_id in self.root_segments:
            self.root_segments.remove(segment_id)

    def traverse(self, strategy: str = "dfs") -> list[Segment]:
        if strategy == "dfs":
            return self._dfs()
        return self._bfs()

    def _dfs(self) -> list[Segment]:
        visited: set[str] = set()
        result: list[Segment] = []

        def _visit(sid: str) -> None:
            if sid in visited:
                return
            visited.add(sid)
            seg = self.segments.get(sid)
            if seg is None:
                return
            result.append(seg)
            for child_id in seg.children:
                _visit(child_id)

        for sid in self.root_segments:
            _visit(sid)
        return result

    def _bfs(self) -> list[Segment]:
        from collections import deque

        visited: set[str] = set()
        result: list[Segment] = []
        queue: deque[str] = deque(self.root_segments)

        while queue:
            sid = queue.popleft()
            if sid in visited:
                continue
            visited.add(sid)
            seg = self.segments.get(sid)
            if seg is None:
                continue
            result.append(seg)
            for child_id in seg.children:
                if child_id not in visited:
                    queue.append(child_id)
        return result

    def subgraph(self, segment_ids: set[str]) -> ContextGraph:
        g = ContextGraph(
            compiler_version=self.compiler_version,
            pipeline_config=dict(self.pipeline_config),
            data=dict(self.data),
        )
        for sid in segment_ids:
            if sid in self.segments:
                seg = self.segments[sid]
                g.segments[sid] = seg
                g.root_segments.append(sid)
                if seg.id in self.provenance:
                    g.provenance[sid] = self.provenance[sid]
        return g

    def merge(self, other: ContextGraph) -> None:
        self.segments.update(other.segments)
        self.entities.merge(other.entities)
        self.provenance.update(other.provenance)
        for sid in other.root_segments:
            if sid not in self.root_segments:
                self.root_segments.append(sid)

    def fingerprint(self) -> str:
        h = sha256()
        for sid in self.root_segments:
            seg = self.segments.get(sid)
            if seg is not None:
                h.update(f"{sid}:{seg.text[:64]}:{seg.context_role.name}".encode())
        return h.hexdigest()[:16]
