"""NormalizePass — whitespace, encoding, type normalization, and minification."""

from __future__ import annotations

import json
import re
import unicodedata

from promptcompiler.ir import ContextGraph, SegmentType
from promptcompiler.ir.segment import TransformRecord
from promptcompiler.passes import Diagnostic, PassContext, PassRegistry
from promptcompiler.tokenizer import estimate_segment_tokens


def _compact_json_text(text: str) -> str:
    try:
        value = json.loads(text)
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    except json.JSONDecodeError:
        return text


def _compact_markdown_text(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        stripped = re.sub(r"^#{1,6}\s*", "", stripped)
        stripped = re.sub(r"^[-*+]\s+", "", stripped)
        stripped = re.sub(r"^\d+\.\s+", "", stripped)
        stripped = stripped.replace("**", "").replace("__", "").replace("`", "")
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def _maybe_minify(text: str) -> tuple[str, str | None]:
    stripped = text.strip()
    if not stripped:
        return text, None
    if stripped.startswith(("{", "[")):
        compacted = _compact_json_text(stripped)
        return (compacted, "json_minify") if compacted != text else (text, None)
    if any(line.lstrip().startswith(("#", "-", "*", "+")) for line in text.splitlines()):
        compacted = _compact_markdown_text(text)
        return (compacted, "markdown_plaintext") if len(compacted) < len(text) else (text, None)
    return text, None


@PassRegistry.register
class NormalizePass:
    """Normalize segment text: trim, NFC-encode, detect code blocks, minify, re-tokenize."""

    pass_id = "normalize.v1"
    pass_version = "1.0.0"
    dependencies: list[str] = ["parse.v1"]

    _BLANK_LINE_RE = re.compile(r"\n{3,}")

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        count = 0
        for seg_id, seg in list(graph.segments.items()):
            original = seg.text
            text = unicodedata.normalize("NFC", original)
            text = text.strip()
            text = self._BLANK_LINE_RE.sub("\n\n", text)

            actions: list[str] = []
            if text != original:
                actions.append("normalization")

            # JSON / markdown minification
            minified, minify_action = _maybe_minify(text)
            if minify_action and minified != text:
                text = minified
                actions.append(minify_action)

            # Detect code blocks → upgrade to CODE type
            seg_type = seg.segment_type
            if seg_type != SegmentType.CODE and "```" in text:
                seg_type = SegmentType.CODE
                actions.append("type-upgrade")

            if not actions and seg.segment_type == SegmentType.CODE:
                continue
            if not actions:
                continue

            tokens = estimate_segment_tokens(text)
            token_delta = tokens - seg.metadata.tokens_after

            seg.text = text
            seg.segment_type = seg_type
            seg.metadata.tokens_original = seg.metadata.tokens_after
            seg.metadata.tokens_after = tokens

            seg.transforms.append(TransformRecord(
                pass_id=self.pass_id,
                pass_version=self.pass_version,
                reason="; ".join(actions),
                metadata={"token_delta": token_delta},
            ))
            count += 1

        ctx.diagnostics.append(Diagnostic(
            severity="info",
            pass_id=self.pass_id,
            code="NORMALIZE_COMPLETE",
            message=f"Normalized {count} segments",
        ))
        return graph
