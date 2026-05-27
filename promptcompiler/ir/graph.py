"""Context graph — the top-level IR container."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Iterator

from .segment import Segment
from .entity import EntityGraph
from .provenance import ProvenanceChain


@dataclass
class ContextGraph:
    """The full IR graph representing a prompt context.

    The graph is composed of typed ``Segment`` nodes linked by entity
    references, with full provenance tracking.  Passes consume and produce
    ``ContextGraph`` instances.
    """

    segments: dict[str, Segment] = field(default_factory=dict)
    entities: EntityGraph = field(default_factory=EntityGraph)
    provenance: dict[str, ProvenanceChain] = field(default_factory=dict)
    root_segments: list[str] = field(default_factory=list)
    compiler_version: str = ""
    pipeline_config: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_segment(self, segment: Segment, *, is_root: bool = True) -> str:
        self.segments[segment.id] = segment
        if is_root:
            self.root_segments.append(segment.id)
        return segment.id

    def remove_segment(self, segment_id: str) -> None:
        self.segments.pop(segment_id, None)
        if segment_id in self.root_segments:
            self.root_segments.remove(segment_id)

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Subgraph
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Fingerprint
    # ------------------------------------------------------------------

    def fingerprint(self) -> str:
        h = sha256()
        for sid in self.root_segments:
            seg = self.segments.get(sid)
            if seg is not None:
                h.update(f"{sid}:{seg.text[:64]}:{seg.context_role.name}".encode())
        return h.hexdigest()[:16]
