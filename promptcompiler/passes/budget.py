"""BudgetPass — enforce a target token budget by pruning low-priority segments."""

from __future__ import annotations

from promptcompiler.ir import ContextGraph
from promptcompiler.ir.segment import TransformRecord
from promptcompiler.passes import Diagnostic, PassContext, PassRegistry


@PassRegistry.register
class BudgetPass:
    """Trim segments to fit within ``target_token_budget``.

    Segments are prioritised by ``metadata.priority_score`` (highest first).
    Low-priority segments are:
      1. Summarised if a summarizer plugin is available (TODO).
      2. Dropped if they cannot be summarised and budget is still exceeded.

    Pinned segments are never removed or summarised.
    """

    pass_id = "budget.v1"
    pass_version = "1.0.0"
    dependencies: list[str] = ["parse.v1"]

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        budget = graph.pipeline_config.get("target_token_budget")
        if budget is None:
            return graph

        # Compute current total
        total = sum(
            seg.metadata.tokens_after or len(seg.text)
            for seg in graph.segments.values()
        )
        if total <= budget:
            return graph

        # Sort root segments by priority (ascending — worst first)
        sorted_segs = sorted(
            (graph.segments[sid] for sid in graph.root_segments if sid in graph.segments),
            key=lambda s: s.metadata.priority_score if s.metadata else 1.0,
        )

        overage = total - budget
        removed: list[str] = []
        tokens_freed = 0

        for seg in sorted_segs:
            if tokens_freed >= overage:
                break
            if seg.metadata.is_pinned:
                continue

            tokens = seg.metadata.tokens_after or len(seg.text)
            removed.append(seg.id)
            tokens_freed += tokens

            seg.transforms.append(TransformRecord(
                pass_id=self.pass_id,
                pass_version=self.pass_version,
                reason="dropped to meet token budget",
                metadata={"tokens_freed": tokens, "overage_at_decision": overage - tokens_freed + tokens},
            ))

        # Actually remove from graph
        for seg_id in removed:
            if seg_id in graph.segments:
                del graph.segments[seg_id]
            if seg_id in graph.root_segments:
                graph.root_segments.remove(seg_id)

        ctx.diagnostics.append(Diagnostic(
            severity="info",
            pass_id=self.pass_id,
            code="BUDGET_ENFORCED",
            message=f"Dropped {len(removed)} segments to meet budget of {budget} tokens (freed {tokens_freed})",
        ))
        return graph
