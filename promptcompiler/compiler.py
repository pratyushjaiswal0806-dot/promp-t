"""Deterministic prompt compilation.

This module performs local, explainable transformations. Lossless mode keeps the
original safety-first behavior. Balanced and aggressive modes add local
budget-aware compaction without using external models.
"""

from __future__ import annotations

import re
from typing import Any

from .diff import kept_diff, removed_diff
from .entities import extract_entities
from .minify import maybe_compact_text
from .models import DEFAULT_NIM_MODEL
from .parser import Segment, parse_prompt
from .semantic import build_semantic_report
from .tokenizer import estimate_text_tokens


_ALLOWED_MODES = {"lossless", "balanced", "aggressive"}
_PINNED_BUDGET_RATIO = 0.25


class CompilePolicyError(ValueError):
    """Raised when a compile policy cannot be satisfied."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


def compile_prompt(
    raw_input: str,
    model: str = DEFAULT_NIM_MODEL,
    mode: str = "lossless",
    target_token_budget: int | None = None,
    dry_run: bool = False,
    semantic_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile a prompt with deterministic, safety-first transforms.

    Parameters
    ----------
    raw_input : str
        The prompt text to compile.
    model : str
        Model identifier for token estimation (default from DEFAULT_NIM_MODEL).
    mode : str
        Compression mode: "lossless" (default, no content removed),
        "balanced" (moderate dedup/summarization), or "aggressive" (maximum).
    target_token_budget : int | None
        Target token count for the output. When set, the compiler attempts to
        meet this budget. Raises CompilePolicyError if pinned content exceeds
        25% of the budget. A warning is emitted if the budget cannot be met safely.
    dry_run : bool
        If True, compute the plan but return the original text unchanged.
    semantic_policy : dict | None
        Optional semantic dedup configuration. See build_semantic_report.

    Returns
    -------
    dict
        Compiled result with optimized_text, diff, plan, semantic metadata, warnings, etc.

    Raises
    ------
    CompilePolicyError
        If the mode is invalid, target_token_budget is invalid, or pinned
        content exceeds the budget.
    """
    normalized_mode = _validate_mode(mode)
    normalized_budget = _normalize_budget(target_token_budget)
    original_segments = parse_prompt(raw_input)
    original_tokens = sum(segment.tokens for segment in original_segments)
    _enforce_pinned_budget(original_segments, normalized_budget, original_tokens)

    proposed = _build_compile(
        original_segments,
        raw_input,
        model=model,
        mode=normalized_mode,
        target_token_budget=normalized_budget,
        semantic_policy=semantic_policy,
    )

    if dry_run:
        active_optimized_text = raw_input
        active_optimized_tokens, active_tokens_saved = _token_metrics_for_output(
            raw_input,
            original_tokens,
            active_optimized_text,
        )
    else:
        active_optimized_text = proposed["optimized_text"]
        active_optimized_tokens = proposed["optimized_tokens"]
        active_tokens_saved = proposed["tokens_saved"]

    return {
        "model": model,
        "mode": normalized_mode,
        "target_token_budget": normalized_budget,
        "dry_run": dry_run,
        "original_tokens": original_tokens,
        "optimized_tokens": active_optimized_tokens,
        "tokens_saved": active_tokens_saved,
        "savings_ratio": round(active_tokens_saved / original_tokens, 4) if original_tokens else 0,
        "optimized_text": active_optimized_text,
        "proposed_optimized_text": proposed["optimized_text"],
        "proposed_optimized_tokens": proposed["optimized_tokens"],
        "proposed_tokens_saved": proposed["tokens_saved"],
        "proposed_savings_ratio": (
            round(proposed["tokens_saved"] / original_tokens, 4) if original_tokens else 0
        ),
        "changes": proposed["changes"],
        "diff": proposed["diff"],
        "retained_segment_ids": proposed["retained_segment_ids"],
        "preservation": proposed["preservation"],
        "plan": proposed["plan"],
        "semantic": proposed["semantic"],
        "warnings": proposed["warnings"],
        "risk_score": proposed["risk_score"],
        "evaluation_status": "not_configured",
        "cache_status": "bypass",
        "cost_benefit": _cost_benefit(original_tokens, proposed["tokens_saved"], normalized_mode),
    }


def _build_compile(
    original_segments: list[Segment],
    raw_input: str,
    model: str,
    mode: str,
    target_token_budget: int | None,
    semantic_policy: dict[str, Any] | None,
) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    diff: list[dict[str, object]] = []
    retained: list[tuple[Segment, str]] = []
    seen: dict[str, str] = {}
    actions: list[dict[str, Any]] = []
    warnings: list[str] = []
    query = _derive_current_query(original_segments)
    semantic = build_semantic_report(
        original_segments,
        query=query,
        mode=mode,
        semantic_policy=semantic_policy,
    )
    semantic_decisions = {
        str(decision["segment_ids"][0]): decision for decision in semantic["decisions"]
    }
    semantic_removed_segment_ids = set(semantic["removed_segment_ids"])

    for index, segment in enumerate(original_segments):
        if segment.id in semantic_removed_segment_ids:
            decision = semantic_decisions[segment.id]
            changes.append(
                {
                    "type": "rag_chunk_pruned",
                    "segment_id": segment.id,
                    "chunk_ids": decision["chunk_ids"],
                    "retained_chunk_id": decision["retained_chunk_id"],
                    "tokens": segment.tokens,
                }
            )
            actions.append(decision)
            diff.append(removed_diff(segment, decision["reason"]))
            continue

        normalized = _normalize(segment.text)
        if not segment.pinned and normalized in seen:
            changes.append(
                {
                    "type": "duplicate_removed",
                    "segment_id": segment.id,
                    "kept_segment_id": seen[normalized],
                    "tokens": segment.tokens,
                }
            )
            actions.append(
                {
                    "action": "dedupe",
                    "segment_ids": [segment.id],
                    "reason": "Exact duplicate of retained unpinned segment.",
                    "estimated_tokens_saved": segment.tokens,
                }
            )
            diff.append(removed_diff(segment, "Exact duplicate of retained unpinned segment."))
            continue

        seen[normalized] = segment.id
        compiled_text = segment.text
        if not segment.pinned:
            compiled_text, compaction_change, compaction_actions = _compact_segment(
                segment,
                mode=mode,
                segment_index=index,
                segment_count=len(original_segments),
            )
            if compaction_change:
                changes.append(compaction_change)
                actions.extend(compaction_actions)
        retained.append((segment, compiled_text))
        diff.append(kept_diff(segment, compiled_text))

    optimized_text = "\n\n".join(text for _, text in retained)
    original_tokens = sum(segment.tokens for segment in original_segments)
    optimized_tokens, tokens_saved = _token_metrics_for_output(
        raw_input,
        original_tokens,
        optimized_text,
    )
    protected_entities = extract_entities(raw_input)
    missing_entities = [entity for entity in protected_entities if entity not in optimized_text]

    if target_token_budget and optimized_tokens > target_token_budget:
        warnings.append(
            (
                f"Target budget {target_token_budget} tokens could not be met safely; "
                f"optimized prompt is {optimized_tokens} estimated tokens."
            )
        )

    warnings.extend(_semantic_warnings(semantic, protected_entities, optimized_text))
    warnings.extend(_domain_term_warnings(raw_input, optimized_text, protected_entities))
    risk_score = _risk_score(mode, warnings, bool(missing_entities))
    return {
        "optimized_text": optimized_text,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "changes": changes,
        "diff": diff,
        "retained_segment_ids": [segment.id for segment, _ in retained],
        "preservation": {
            "ok": not missing_entities,
            "checked_entities": protected_entities,
            "missing_entities": missing_entities,
        },
        "plan": {
            "mode": mode,
            "target_token_budget": target_token_budget,
            "estimated_original_tokens": original_tokens,
            "estimated_optimized_tokens": optimized_tokens,
            "estimated_tokens_saved": tokens_saved,
            "risk_level": _risk_level(risk_score),
            "actions": actions,
        },
        "semantic": semantic,
        "warnings": warnings,
        "risk_score": risk_score,
    }


def _derive_current_query(segments: list[Segment]) -> str:
    for segment in reversed(segments):
        lower = segment.text.lower()
        if "task:" in lower or "goal:" in lower or "objective:" in lower or "instruction:" in lower:
            return segment.text
    for segment in reversed(segments):
        if segment.type not in {"rag", "tool"} and not segment.pinned:
            return segment.text
    for segment in reversed(segments):
        if segment.type not in {"rag", "tool"}:
            return segment.text
    return ""


def _semantic_warnings(
    semantic: dict[str, Any],
    protected_entities: list[str],
    optimized_text: str,
) -> list[str]:
    if not semantic.get("removed_chunk_ids"):
        return []

    missing_entities = [entity for entity in protected_entities if entity not in optimized_text]
    if not missing_entities:
        return []

    return [
        "Semantic pruning was applied, but protected values are missing from the optimized prompt."
    ]


_DOMAIN_TERMS = [
    "HIPAA", "GDPR", "PCI DSS", "FHIR", "HL7", "OAuth", "JWT",
    "AES", "TLS", "SSL", "BAA", "PHI", "CME", "NPI",
    "p95", "p99", "RPO", "RTO",
]


def _domain_term_warnings(
    raw_input: str,
    optimized_text: str,
    protected_entities: list[str],
) -> list[str]:
    warnings: list[str] = []
    missing = []
    for term in _DOMAIN_TERMS:
        term_lower = term.lower()
        if term_lower in raw_input.lower() and term_lower not in optimized_text.lower():
            missing.append(term)
    if missing:
        warnings.append(
            f"Compressed prompt may be missing critical domain terms: {', '.join(missing[:5])}. "
            "Consider using lossless mode or adjusting the compression policy."
        )
    return warnings


def _compact_segment(
    segment: Segment,
    mode: str,
    segment_index: int,
    segment_count: int,
) -> tuple[str, dict[str, Any] | None, list[dict[str, Any]]]:
    actions: list[dict[str, Any]] = []
    normalized_text, minify_action = maybe_compact_text(segment.text)
    minify_removed = max(
        0,
        estimate_text_tokens(segment.text) - estimate_text_tokens(normalized_text),
    )
    if minify_action and mode != "lossless":
        actions.append(
            {
                "action": minify_action,
                "segment_ids": [segment.id],
                "reason": "Compacted structured or markdown input before model injection.",
                "estimated_tokens_saved": minify_removed,
            }
        )
    else:
        normalized_text = segment.text
        minify_removed = 0

    compacted, repeated_removed = _compact_repeated_lines(normalized_text)
    truncated, truncated_lines = _truncate_large_tool_output(compacted, segment, mode)
    tool_summarized, tool_summary_removed = _summarize_tool_segment(truncated, segment, mode)
    summarized, summary_removed = _summarize_history_segment(
        tool_summarized,
        segment,
        mode=mode,
        segment_index=segment_index,
        segment_count=segment_count,
    )

    removed = minify_removed + repeated_removed + truncated_lines + tool_summary_removed + summary_removed
    if repeated_removed:
        actions.append(
            {
                "action": "repeat_collapse",
                "segment_ids": [segment.id],
                "reason": "Collapsed adjacent repeated lines.",
                "estimated_lines_removed": repeated_removed,
            }
        )
    if truncated_lines:
        actions.append(
            {
                "action": "tool_summary",
                "segment_ids": [segment.id],
                "reason": f"Compacted verbose {segment.type} output in {mode} mode.",
                "estimated_lines_removed": truncated_lines,
            }
        )
    if tool_summary_removed:
        actions.append(
            {
                "action": "tool_summary",
                "segment_ids": [segment.id],
                "reason": "Summarized verbose tool output locally while preserving entities.",
                "estimated_tokens_saved": tool_summary_removed,
            }
        )
    if summary_removed:
        actions.append(
            {
                "action": "history_summary",
                "segment_ids": [segment.id],
                "reason": "Summarized older unpinned context while preserving entities.",
                "estimated_tokens_saved": summary_removed,
            }
        )

    if removed == 0 and summarized == segment.text:
        return segment.text, None, actions

    return (
        summarized,
        {
            "type": "segment_compacted",
            "segment_id": segment.id,
            "lines_removed": repeated_removed + truncated_lines,
            "tokens_before": segment.tokens,
            "tokens_after": estimate_text_tokens(summarized),
        },
        actions,
    )


def _compact_repeated_lines(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    if len(lines) < 2:
        return text, 0

    output: list[str] = []
    removed = 0
    index = 0
    while index < len(lines):
        current = lines[index]
        repeat_count = 1
        while index + repeat_count < len(lines) and lines[index + repeat_count] == current:
            repeat_count += 1

        output.append(current)
        if repeat_count > 1:
            extra = repeat_count - 1
            removed += extra
            output.append(f"[repeated {extra} more times]")
        index += repeat_count

    return "\n".join(output), removed


def _truncate_large_tool_output(text: str, segment: Segment, mode: str) -> tuple[str, int]:
    lines = text.splitlines()
    if segment.type not in {"tool", "rag"}:
        return text, 0

    if mode == "lossless":
        max_lines, head_count, tail_count = 80, 45, 10
    elif mode == "balanced":
        max_lines, head_count, tail_count = 36, 18, 6
    else:
        max_lines, head_count, tail_count = 22, 10, 4

    if len(lines) <= max_lines:
        return text, 0

    head = lines[:head_count]
    middle = lines[head_count:-tail_count]
    tail = lines[-tail_count:] if tail_count else []
    protected_middle = [
        line for line in middle if extract_entities(line) and line not in head and line not in tail
    ]
    omitted = len(lines) - len(head) - len(protected_middle) - len(tail)
    marker = f"[omitted {omitted} middle lines in {mode} mode]"
    return "\n".join([*head, *protected_middle, marker, *tail]), max(0, omitted)


def _summarize_tool_segment(text: str, segment: Segment, mode: str) -> tuple[str, int]:
    if mode == "lossless" or segment.type not in {"tool", "rag"}:
        return text, 0

    tokens = estimate_text_tokens(text)
    threshold = 18 if mode == "balanced" else 12
    if tokens <= threshold:
        return text, 0

    protected_lines = [line for line in text.splitlines() if extract_entities(line)]
    summary_lines = [
        f"[{segment.type} summary]",
        *protected_lines,
    ]
    summary = "\n".join(dict.fromkeys(line for line in summary_lines if line.strip()))
    return summary, max(0, tokens - estimate_text_tokens(summary))


def _summarize_history_segment(
    text: str,
    segment: Segment,
    mode: str,
    segment_index: int,
    segment_count: int,
) -> tuple[str, int]:
    if mode == "lossless" or segment.type in {"system", "developer", "tool", "rag"}:
        return text, 0
    if segment_index >= max(0, segment_count - 2):
        return text, 0

    tokens = estimate_text_tokens(text)
    threshold = 90 if mode == "balanced" else 45
    if tokens <= threshold:
        return text, 0

    sentences = _sentence_fragments(text)
    kept = sentences[:2] if mode == "balanced" else sentences[:1]
    protected_lines = [line for line in text.splitlines() if extract_entities(line)]
    parts = [part for part in [*kept, *protected_lines] if part.strip()]
    summary = "\n".join(dict.fromkeys(parts))
    if not summary:
        summary = text[:240].strip()
    summary = f"[summarized older {segment.type} context]\n{summary}"
    summary_tokens = estimate_text_tokens(summary)
    if summary_tokens >= tokens:
        return text, 0
    return summary, max(0, tokens - summary_tokens)


def _sentence_fragments(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    fragments = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        if re.match(r"^\d+\.$", stripped) or re.match(r"^\d+\.\s", stripped):
            continue
        fragments.append(stripped)
    return fragments


def _validate_mode(mode: str) -> str:
    normalized = (mode or "lossless").strip().lower()
    if normalized not in _ALLOWED_MODES:
        raise CompilePolicyError(
            f"Unsupported compression mode '{mode}'. Choose lossless, balanced, or aggressive.",
            status_code=400,
            error_code="INVALID_COMPRESSION_MODE",
            details={"allowed_modes": sorted(_ALLOWED_MODES)},
        )
    return normalized


def _normalize_budget(value: int | None) -> int | None:
    if value is None:
        return None
    try:
        budget = int(value)
    except (TypeError, ValueError) as exc:
        raise CompilePolicyError(
            "target_token_budget must be a positive integer.",
            status_code=400,
            error_code="INVALID_TARGET_BUDGET",
        ) from exc
    if budget <= 0:
        raise CompilePolicyError(
            "target_token_budget must be a positive integer.",
            status_code=400,
            error_code="INVALID_TARGET_BUDGET",
        )
    return budget


def _enforce_pinned_budget(
    segments: list[Segment],
    target_token_budget: int | None,
    original_tokens: int,
) -> None:
    if target_token_budget is None:
        return

    pinned_tokens = sum(segment.tokens for segment in segments if segment.pinned)
    pinned_limit = max(1, int(target_token_budget * _PINNED_BUDGET_RATIO))
    if pinned_tokens > pinned_limit:
        raise CompilePolicyError(
            (
                f"Pinned content uses {pinned_tokens} estimated tokens, above the "
                f"{pinned_limit} token pinned budget for this request."
            ),
            status_code=413,
            error_code="PINNED_BUDGET_EXCEEDED",
            details={
                "pinned_tokens": pinned_tokens,
                "pinned_budget_limit": pinned_limit,
                "target_token_budget": target_token_budget,
                "original_tokens": original_tokens,
            },
        )


def _cost_benefit(original_tokens: int, tokens_saved: int, mode: str) -> dict[str, Any]:
    summarization_cost_proxy = 0 if mode == "lossless" else round(original_tokens * 0.2)
    should_summarize = mode != "lossless" and tokens_saved > summarization_cost_proxy * 1.5
    return {
        "estimated_input_tokens_saved": tokens_saved,
        "summarization_cost_proxy_tokens": summarization_cost_proxy,
        "should_use_active_summarization": should_summarize,
    }


def _token_metrics_for_output(
    raw_input: str,
    original_tokens: int,
    optimized_text: str,
) -> tuple[int, int]:
    if optimized_text == raw_input:
        return original_tokens, 0
    optimized_tokens = estimate_text_tokens(optimized_text)
    return optimized_tokens, max(0, original_tokens - optimized_tokens)


def _risk_score(mode: str, warnings: list[str], missing_entities: bool) -> float:
    base = {"lossless": 0.05, "balanced": 0.28, "aggressive": 0.58}[mode]
    if warnings:
        base += 0.15
    if missing_entities:
        base += 0.35
    return round(min(1.0, base), 2)


def _risk_level(score: float) -> str:
    if score < 0.25:
        return "low"
    if score < 0.6:
        return "medium"
    return "high"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()
