"""NormalizePass — whitespace, encoding, and type normalization."""

from __future__ import annotations

import re
import unicodedata

from promptcompiler.ir import ContextGraph, SegmentType
from promptcompiler.ir.segment import TransformRecord
from promptcompiler.passes import Diagnostic, PassContext, PassRegistry
from promptcompiler.tokenizer import estimate_segment_tokens


@PassRegistry.register
class NormalizePass:
    """Normalize segment text: trim, NFC-encode, detect code blocks, re-tokenize."""

    pass_id = "normalize.v1"
    pass_version = "1.0.0"
    dependencies: list[str] = ["parse.v1"]

    _CODE_LANG_RE = re.compile(r"^```(\w+)", re.MULTILINE)
    _BLANK_LINE_RE = re.compile(r"\n{3,}")

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        count = 0
        for seg_id, seg in list(graph.segments.items()):
            original = seg.text
            text = unicodedata.normalize("NFC", original)
            text = text.strip()
            text = self._BLANK_LINE_RE.sub("\n\n", text)

            if text == original and seg.segment_type != SegmentType.CODE:
                continue

            # Detect code blocks → upgrade to CODE type
            seg_type = seg.segment_type
            if seg_type != SegmentType.CODE and "```" in text:
                seg_type = SegmentType.CODE

            tokens = estimate_segment_tokens(text)

            seg.text = text
            seg.segment_type = seg_type
            seg.metadata.tokens_original = seg.metadata.tokens_after
            seg.metadata.tokens_after = tokens

            seg.transforms.append(TransformRecord(
                pass_id=self.pass_id,
                pass_version=self.pass_version,
                reason="normalization" if text != original else "type-upgrade",
            ))
            count += 1

        ctx.diagnostics.append(Diagnostic(
            severity="info",
            pass_id=self.pass_id,
            code="NORMALIZE_COMPLETE",
            message=f"Normalized {count} segments",
        ))
        return graph
