"""Base pass interface, pipeline executor, and registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Protocol

from promptcompiler.ir import ContextGraph
from promptcompiler.settings import CompilerSettings


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


@dataclass
class Diagnostic:
    """A structured diagnostic emitted by a compiler pass."""
    severity: str = "info"
    pass_id: str = ""
    segment_id: str | None = None
    code: str = ""
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pass context
# ---------------------------------------------------------------------------


@dataclass
class PassContext:
    """Context passed to every pass during pipeline execution.

    Carries runtime configuration, caches, diagnostics accumulator, and
    the current compilation stage.
    """

    compiler_version: str = ""
    settings: CompilerSettings | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    cache: dict[str, Any] = field(default_factory=dict)
    stage: str = ""


# ---------------------------------------------------------------------------
# Pass Protocol
# ---------------------------------------------------------------------------


class Pass(Protocol):
    """A single compiler pass.

    Every pass:
    1. Receives a ContextGraph and PassContext
    2. May modify the graph
    3. May emit diagnostics via ctx.diagnostics
    4. Must be deterministic (same graph + ctx → identical result)
    """

    pass_id: str
    pass_version: str
    dependencies: list[str]

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        """Execute the pass.  Return the (possibly modified) graph."""
        ...


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


@dataclass
class CompilationStats:
    """Aggregate statistics from a compilation run."""
    segments_input: int = 0
    segments_output: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    entity_count: int = 0
    passes_run: int = 0
    warnings: int = 0
    errors: int = 0
    duration_ms: float = 0.0


@dataclass
class CompilationResult:
    """Result of a full compilation pipeline."""
    output_graph: ContextGraph | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    stats: CompilationStats = field(default_factory=CompilationStats)
    compiler_version: str = ""
    pipeline_id: str = ""
    started_at: str = ""
    completed_at: str = ""


class CompilerPipeline:
    """A DAG of compiler passes, executed in dependency order."""

    def __init__(self, pipeline_id: str, passes: list[Pass]) -> None:
        self.pipeline_id = pipeline_id
        self._passes = self._topological_sort(passes)
        self._validate_deps()

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        graph: ContextGraph,
        ctx: PassContext | None = None,
    ) -> CompilationResult:
        started = datetime.now(timezone.utc)
        started_at = started.isoformat()

        if ctx is None:
            ctx = PassContext(
                compiler_version=graph.compiler_version or "dev",
                settings=CompilerSettings(),
            )

        ctx.diagnostics = []
        ctx.stage = ""
        passes_run = 0

        for p in self._passes:
            ctx.stage = p.pass_id
            pre_count = len(ctx.diagnostics)
            graph = p.run(graph, ctx)
            # If the pass appended no diagnostics, add an implicit "ok"
            if len(ctx.diagnostics) == pre_count:
                ctx.diagnostics.append(Diagnostic(
                    severity="info",
                    pass_id=p.pass_id,
                    code="PASS_OK",
                    message=f"Pass {p.pass_id} completed silently",
                ))
            passes_run += 1

        completed_at = datetime.now(timezone.utc).isoformat()
        duration = (datetime.now(timezone.utc) - started).total_seconds() * 1000

        stats = self._compute_stats(graph, passes_run, ctx.diagnostics, duration)

        return CompilationResult(
            output_graph=graph,
            diagnostics=ctx.diagnostics,
            stats=stats,
            compiler_version=ctx.compiler_version,
            pipeline_id=self.pipeline_id,
            started_at=started_at,
            completed_at=completed_at,
        )

    # ------------------------------------------------------------------
    # Topological sort
    # ------------------------------------------------------------------

    @staticmethod
    def _topological_sort(passes: list[Pass]) -> list[Pass]:
        by_id = {p.pass_id: p for p in passes}
        visited: set[str] = set()
        result: list[Pass] = []

        def _visit(pass_id: str) -> None:
            if pass_id in visited:
                return
            visited.add(pass_id)
            p = by_id.get(pass_id)
            if p is None:
                raise ValueError(f"Pass {pass_id!r} required but not in pipeline")
            for dep in p.dependencies:
                _visit(dep)
            result.append(p)

        for p in passes:
            _visit(p.pass_id)

        return result

    def _validate_deps(self) -> None:
        pass  # TODO: cycle detection, missing dep checks

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_stats(
        graph: ContextGraph,
        passes_run: int,
        diagnostics: list[Diagnostic],
        duration_ms: float,
    ) -> CompilationStats:
        tokens_in = sum(
            (seg.metadata.tokens_original if seg.metadata else 0)
            for seg in graph.segments.values()
        )
        tokens_out = sum(
            (seg.metadata.tokens_after if seg.metadata else len(seg.text))
            for seg in graph.segments.values()
        )
        errors = sum(1 for d in diagnostics if d.severity == "error")
        warnings = sum(1 for d in diagnostics if d.severity == "warning")

        return CompilationStats(
            segments_input=len(graph.segments),
            segments_output=len(graph.root_segments),
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            entity_count=len(graph.entities.entities),
            passes_run=passes_run,
            warnings=warnings,
            errors=errors,
            duration_ms=round(duration_ms, 2),
        )


# ---------------------------------------------------------------------------
# Pass registry
# ---------------------------------------------------------------------------


class PassRegistry:
    """Registry of known pass types, keyed by pass_id."""

    _passes: dict[str, type[Pass]] = {}

    @classmethod
    def register(cls, pass_cls: type[Pass]) -> type[Pass]:
        pid = pass_cls.pass_id  # type: ignore[union-attr]
        cls._passes[pid] = pass_cls
        return pass_cls

    @classmethod
    def get(cls, pass_id: str) -> type[Pass]:
        if pass_id not in cls._passes:
            raise KeyError(f"Pass {pass_id!r} not registered; available: {list(cls._passes)}")
        return cls._passes[pass_id]

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._passes.keys())

    @classmethod
    def build_pipeline(cls, pipeline_id: str, pass_ids: list[str]) -> CompilerPipeline:
        passes = [cls.get(pid)() for pid in pass_ids]
        return CompilerPipeline(pipeline_id, passes)
