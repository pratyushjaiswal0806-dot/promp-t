"""Deterministic prompt compilation via v2 pass pipeline.

This module wraps the v2 CompilerRuntime to provide the public compile_prompt()
API with backward-compatible response shape.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .diff import kept_diff, removed_diff
from .entities import extract_entities
from .models import DEFAULT_NIM_MODEL
from .parser import Segment, parse_prompt
from .runtime import CompilerRuntime
from .semantic import build_semantic_report
from .tokenizer import estimate_text_tokens, set_active_model


_COMPILE_CACHE: dict[str, dict[str, Any]] = {}
_COMPILE_CACHE_MAX = 128


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


_runtime = CompilerRuntime()


def compile_prompt(
    raw_input: str,
    model: str = DEFAULT_NIM_MODEL,
    mode: str = "lossless",
    target_token_budget: int | None = None,
    dry_run: bool = False,
    semantic_policy: dict[str, Any] | None = None,
    use_cache: bool = False,
) -> dict[str, Any]:
    normalized_mode = _validate_mode(mode)
    normalized_budget = _normalize_budget(target_token_budget)
    set_active_model(model)

    cache_key = _compile_cache_key(raw_input, model, normalized_mode, normalized_budget, dry_run) if use_cache else None
    if cache_key and cache_key in _COMPILE_CACHE:
        cached = dict(_COMPILE_CACHE[cache_key])
        cached["cache_status"] = "hit"
        return cached

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
        original_tokens=original_tokens,
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

    result = {
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
        "cache_status": "miss" if cache_key else "bypass",
        "cost_benefit": _cost_benefit(original_tokens, proposed["tokens_saved"], normalized_mode),
    }

    if cache_key and not dry_run:
        if len(_COMPILE_CACHE) >= _COMPILE_CACHE_MAX:
            oldest = next(iter(_COMPILE_CACHE))
            del _COMPILE_CACHE[oldest]
        _COMPILE_CACHE[cache_key] = result

    return result


def _build_compile(
    original_segments: list[Segment],
    raw_input: str,
    model: str,
    mode: str,
    target_token_budget: int | None,
    semantic_policy: dict[str, Any] | None,
    original_tokens: int,
) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    diff: list[dict[str, object]] = []
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

    # Build pruned input (remove semantically redundant segments before v2 pipeline)
    pruned_texts: list[str] = []
    for segment in original_segments:
        if segment.id in semantic_removed_segment_ids:
            decision = semantic_decisions[segment.id]
            changes.append({
                "type": "rag_chunk_pruned",
                "segment_id": segment.id,
                "chunk_ids": decision["chunk_ids"],
                "retained_chunk_id": decision["retained_chunk_id"],
                "tokens": segment.tokens,
            })
            actions.append(decision)
            diff.append(removed_diff(segment, decision["reason"]))
        else:
            pruned_texts.append(segment.text)

    pruned_input = "\n\n".join(pruned_texts) if pruned_texts else raw_input

    # Run v2 pipeline on pruned input
    v2_result = None
    try:
        v2_result = _runtime.compile(
            pruned_input,
            mode=mode,
            target_token_budget=target_token_budget,
        )
    except Exception:
        pass

    if v2_result and v2_result.output_graph:
        optimized_text = v2_result.output_graph.data.get("output_text", pruned_input)
    else:
        optimized_text = raw_input

    # Deduce changes by comparing pruned input sections to optimized output
    pruned_sections = pruned_input.split("\n\n")
    opt_sections = optimized_text.split("\n\n")

    # Track which pruned sections map to which opt sections
    opt_used = [False] * len(opt_sections)
    for psec in pruned_sections:
        pnorm = _normalize(psec)
        found = False
        for j, osec in enumerate(opt_sections):
            if not opt_used[j] and _normalize(osec) == pnorm:
                opt_used[j] = True
                found = True
                break
        if not found:
            # Check if partially present (compacted)
            for j, osec in enumerate(opt_sections):
                if not opt_used[j] and pnorm.startswith(_normalize(osec)[:40]):
                    opt_used[j] = True
                    found = True
                    # Segment was compacted
                    changes.append({
                        "type": "segment_compacted",
                        "segment_id": "",
                        "lines_removed": 0,
                        "tokens_before": estimate_text_tokens(psec),
                        "tokens_after": estimate_text_tokens(osec),
                    })
                    break
        if not found:
            # Segment was fully removed (dedup or budget)
            changes.append({
                "type": "duplicate_removed",
                "segment_id": "",
                "kept_segment_id": "",
                "tokens": estimate_text_tokens(psec),
            })

    # Extract actions from v2 per-segment transforms (map to v1 action names)
    if v2_result:
        for seg in v2_result.output_graph.segments.values():
            for tr in seg.transforms:
                base = tr.pass_id.split(".")[0]
                # Derive action name from pass_id or reason string
                if base == "normalize":
                    # Extract specific minify action from reason
                    reason_lower = tr.reason.lower()
                    if "json_minify" in reason_lower or "json" in reason_lower:
                        action_name = "json_minify"
                    elif "markdown_plaintext" in reason_lower or "markdown" in reason_lower:
                        action_name = "markdown_plaintext"
                    else:
                        action_name = "normalize"
                elif base == "dedup":
                    action_name = "dedupe"
                elif base == "summarize":
                    action_name = "tool_summary"
                else:
                    action_name = base
                token_delta = tr.metadata.get("token_delta", tr.metadata.get("tokens_saved", 0))
                if token_delta != 0:
                    saved = abs(token_delta)
                    actions.append({
                        "action": action_name,
                        "segment_ids": [seg.id],
                        "reason": tr.reason,
                        "estimated_tokens_saved": saved,
                    })

    # Build diff by comparing each original segment against optimized text
    # Count occurrences of each text in optimized output to handle duplicates
    from collections import Counter
    opt_seg_counts = Counter(optimized_text.split("\n\n"))
    kept_text_counts: dict[str, int] = {}
    for segment in original_segments:
        seg_text = segment.text
        if segment.id in semantic_removed_segment_ids:
            decision = semantic_decisions.get(segment.id, {})
            diff.append(removed_diff(segment, decision.get("reason", "Semantic pruning")))
        elif kept_text_counts.get(seg_text, 0) < opt_seg_counts.get(seg_text, 0):
            kept_text_counts[seg_text] = kept_text_counts.get(seg_text, 0) + 1
            diff.append(kept_diff(segment, segment.text))
        else:
            diff.append(removed_diff(segment, "Removed by compression pipeline"))

    optimized_tokens, tokens_saved = _token_metrics_for_output(
        raw_input,
        original_tokens,
        optimized_text,
    )
    protected_entities = extract_entities(raw_input)
    missing_entities = [entity for entity in protected_entities if entity not in optimized_text]

    if target_token_budget:
        if optimized_tokens > target_token_budget:
            warnings.append(
                f"Target budget {target_token_budget} tokens could not be met safely; "
                f"optimized prompt is {optimized_tokens} estimated tokens."
            )
        elif v2_result and any(d.code == "BUDGET_ENFORCED" for d in v2_result.diagnostics):
            warnings.append(
                f"Target budget {target_token_budget} tokens was enforced by removing "
                f"{sum(1 for d in v2_result.diagnostics if d.code == 'BUDGET_ENFORCED')} segments."
            )

    warnings.extend(_semantic_warnings(semantic, protected_entities, optimized_text))
    warnings.extend(_domain_term_warnings(raw_input, optimized_text, protected_entities))
    risk_score = _risk_score(mode, warnings, bool(missing_entities))
    retained_ids = [
        seg.id for seg in original_segments
        if seg.id not in semantic_removed_segment_ids
    ]
    return {
        "optimized_text": optimized_text,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "changes": changes,
        "diff": diff,
        "retained_segment_ids": retained_ids,
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
    raw_lower = raw_input.lower()
    optimized_lower = optimized_text.lower()
    for term in _DOMAIN_TERMS:
        term_lower = term.lower()
        if term_lower in raw_lower and term_lower not in optimized_lower:
            missing.append(term)
    if missing:
        warnings.append(
            f"Compressed prompt may be missing critical domain terms: {', '.join(missing[:5])}. "
            "Consider using lossless mode or adjusting the compression policy."
        )
    return warnings


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


def _compile_cache_key(
    raw_input: str,
    model: str,
    mode: str,
    target_token_budget: int | None,
    dry_run: bool,
) -> str | None:
    payload = {
        "raw_input": raw_input,
        "model": model,
        "mode": mode,
        "target_token_budget": target_token_budget,
        "dry_run": dry_run,
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:32]
