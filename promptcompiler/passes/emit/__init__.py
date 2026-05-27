"""Emission passes (text, provenance, audit)."""

from __future__ import annotations

from promptcompiler.ir import ContextGraph
from promptcompiler.passes.base import Diagnostic, PassContext, PassRegistry


@PassRegistry.register
class EmitPass:
    """Serialize the final ContextGraph to plain text.

    Always runs last.  Produces ``graph.data["output_text"]``.
    """

    pass_id = "emit.v1"
    pass_version = "1.0.0"
    dependencies: list[str] = []

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        segments = [graph.segments[sid] for sid in graph.root_segments if sid in graph.segments]
        text = "\n\n".join(seg.text for seg in segments)
        graph.data["output_text"] = text

        ctx.diagnostics.append(Diagnostic(
            severity="info",
            pass_id=self.pass_id,
            code="EMIT_COMPLETE",
            message=f"Emitted {len(segments)} segments ({len(text)} chars)",
        ))
        return graph
