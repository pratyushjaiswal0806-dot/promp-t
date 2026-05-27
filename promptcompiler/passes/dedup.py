"""DedupPass — detect and remove duplicate segments."""

from __future__ import annotations

import re
from collections import defaultdict

from promptcompiler.ir import ContextGraph
from promptcompiler.ir.segment import TransformRecord
from promptcompiler.passes import Diagnostic, PassContext, PassRegistry


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


@PassRegistry.register
class DedupPass:
    """Remove exact duplicate unpinned segments, keeping the first occurrence.

    A duplicate is defined as a segment whose normalised text (collapsed
    whitespace, lowercased) exactly matches another earlier segment.
    Pinned segments are never removed.
    """

    pass_id = "dedup.v1"
    pass_version = "1.0.0"
    dependencies: list[str] = ["normalize.v1"]

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        seen: dict[str, str] = {}
        to_remove: list[str] = []
        kept_for: dict[str, str] = {}
        tokens_saved = 0

        for seg_id in graph.root_segments.copy():
            seg = graph.segments.get(seg_id)
            if seg is None:
                continue

            if seg.metadata.is_pinned:
                continue

            norm = _normalize(seg.text)
            if norm in seen:
                to_remove.append(seg_id)
                kept_id = seen[norm]
                kept_for[seg_id] = kept_id
                tokens_saved += seg.metadata.tokens_after or len(seg.text)
            else:
                seen[norm] = seg_id

        # Remove duplicates from the graph
        for seg_id in to_remove:
            kept_id = kept_for[seg_id]
            # Record provenance for the surviving segment
            kept = graph.segments[kept_id]
            kept.transforms.append(TransformRecord(
                pass_id=self.pass_id,
                pass_version=self.pass_version,
                reason=f"merged duplicate segment {seg_id}",
                metadata={"collapsed_segment": seg_id, "tokens_saved": seg.metadata.tokens_after if seg_id in graph.segments else 0},
            ))
            # Remove the duplicate
            if seg_id in graph.segments:
                del graph.segments[seg_id]
            if seg_id in graph.root_segments:
                graph.root_segments.remove(seg_id)

        ctx.diagnostics.append(Diagnostic(
            severity="info",
            pass_id=self.pass_id,
            code="DEDUP_COMPLETE",
            message=f"Removed {len(to_remove)} duplicate segments (saved ~{tokens_saved} tokens)",
        ))
        return graph
