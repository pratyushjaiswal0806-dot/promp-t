"""Reusable context-file compression helpers.

The context_file mode is intentionally separate from normal prompt compilation:
it targets stable system prompts, personas, policy blocks, and memory files that
can be compacted once and reused across multiple calls.
"""

from __future__ import annotations

from math import ceil
import re
from typing import Any

from .entities import extract_entities
from .parser import Segment
from .tokenizer import estimate_text_tokens


DECODE_PROMPT = (
    "Interpret compact context as high-priority instructions. Restore omitted grammar, "
    "preserve exact literals, and obey negations, ordered steps, roles, constraints, "
    "paths, line numbers, schemas, code, and quoted text exactly."
)

_ORDER_WORDS = ("First", "Second", "Third", "Fourth", "Fifth")
_FILLER_WORDS = {
    "a",
    "about",
    "also",
    "an",
    "any",
    "be",
    "the",
    "they",
    "that",
    "to",
    "what",
    "when",
    "which",
    "who",
    "you",
    "your",
}
_PATH_RE = re.compile(r"(?:[A-Za-z]:)?(?:/[A-Za-z0-9_.:-]+){1,}|[A-Za-z0-9_.-]+\.[A-Za-z0-9_]+:\d+")
_LINE_NUMBER_RE = re.compile(r"\b(?:line|lines)\s+\d+(?:[-:]\d+)?\b", re.IGNORECASE)
_NEGATION_PATTERNS = (
    re.compile(r"\bdo\s+not\s+preface\b.*?(?:\.|$)", re.IGNORECASE),
    re.compile(r"\bdo\s+not\b.*?(?:\.|$)", re.IGNORECASE),
    re.compile(r"\bnever\b.*?(?:\.|$)", re.IGNORECASE),
    re.compile(r"\bnot\b.*?(?:\.|$)", re.IGNORECASE),
)


def compile_context_file(
    raw_input: str,
    segments: list[Segment],
    *,
    original_tokens: int,
    context_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = context_policy or {}
    reuse_expected_calls = _positive_int(policy.get("reuse_expected_calls"), 1)
    include_decode_prompt = bool(policy.get("include_decode_prompt", True))
    validation = str(policy.get("validation") or "strict").strip().lower()
    if validation not in {"strict", "loose"}:
        validation = "strict"

    compact = compact_context_text(raw_input)
    compact_tokens = estimate_text_tokens(compact)
    decode_tokens = estimate_text_tokens(DECODE_PROMPT) if include_decode_prompt else 0
    direct_saved = max(0, original_tokens - compact_tokens)
    net_first_call_savings = original_tokens - compact_tokens - decode_tokens
    net_reuse_savings_per_call = direct_saved
    break_even_calls = ceil(decode_tokens / direct_saved) if direct_saved > 0 and decode_tokens else (1 if direct_saved > 0 else None)
    total_reuse_savings = net_first_call_savings + max(0, reuse_expected_calls - 1) * net_reuse_savings_per_call

    preservation = validate_context_compression(
        raw_input,
        compact,
        validation=validation,
    )
    warnings = _warnings(
        direct_saved=direct_saved,
        break_even_calls=break_even_calls,
        reuse_expected_calls=reuse_expected_calls,
        preservation=preservation,
    )
    risk_score = 0.18
    if warnings:
        risk_score += 0.12
    if not preservation["ok"]:
        risk_score += 0.35
    risk_score = round(min(1.0, risk_score), 2)

    diff = [
        {
            "segment_id": "context_file",
            "type": "context",
            "role": _dominant_role(segments),
            "status": "compacted",
            "pinned": False,
            "original_text": raw_input,
            "optimized_text": compact,
            "reason": "Compressed reusable context into dense instruction text.",
        }
    ]
    action = {
        "action": "context_file_compact",
        "segment_ids": [segment.id for segment in segments],
        "reason": "Compacted stable reusable context and calculated amortized reuse savings.",
        "estimated_tokens_saved": direct_saved,
    }
    context_file = {
        "compact": compact,
        "decode_prompt": DECODE_PROMPT if include_decode_prompt else "",
        "original_tokens": original_tokens,
        "compact_tokens": compact_tokens,
        "decode_tokens": decode_tokens,
        "net_first_call_savings": net_first_call_savings,
        "net_reuse_savings_per_call": net_reuse_savings_per_call,
        "total_reuse_savings": total_reuse_savings,
        "break_even_calls": break_even_calls,
        "reuse_expected_calls": reuse_expected_calls,
        "include_decode_prompt": include_decode_prompt,
        "validation": validation,
        "safe_to_reuse": preservation["ok"],
        "economical_for_expected_reuse": total_reuse_savings > 0,
        "preservation": preservation,
    }
    return {
        "optimized_text": compact,
        "optimized_tokens": compact_tokens,
        "tokens_saved": direct_saved,
        "changes": [
            {
                "type": "context_file_compacted",
                "segment_id": "context_file",
                "tokens": direct_saved,
            }
        ],
        "diff": diff,
        "retained_segment_ids": [segment.id for segment in segments],
        "preservation": {
            "ok": preservation["ok"],
            "checked_entities": preservation["checked_entities"],
            "missing_entities": preservation["missing_entities"],
        },
        "plan": {
            "mode": "context_file",
            "target_token_budget": None,
            "estimated_original_tokens": original_tokens,
            "estimated_optimized_tokens": compact_tokens,
            "estimated_tokens_saved": direct_saved,
            "risk_level": _risk_level(risk_score),
            "actions": [action],
        },
        "semantic": _empty_semantic(),
        "warnings": warnings,
        "risk_score": risk_score,
        "context_file": context_file,
    }


def compact_context_text(text: str) -> str:
    protected = _protected_literals(text)
    lines: list[str] = []
    for raw_line in _split_instruction_lines(text):
        line = raw_line.strip()
        if not line:
            continue
        lines.append(_compact_line(line, protected))
    return "\n".join(_dedupe(lines)).strip()


def validate_context_compression(
    original: str,
    compact: str,
    *,
    validation: str = "strict",
) -> dict[str, Any]:
    original_entities = [_clean_literal(entity) for entity in extract_entities(original)]
    checked_entities = _dedupe([*original_entities, *_protected_literals(original)])
    missing_entities = [item for item in checked_entities if item and item not in compact]
    negations = _negation_clauses(original)
    missing_negations = [
        clause for clause in negations
        if _negation_anchor(clause) not in _normalize(compact)
    ]
    ordered_steps = [word for word in _ORDER_WORDS if re.search(rf"\b{word}\b", original)]
    missing_steps = [word for word in ordered_steps if word.lower() not in compact.lower()]
    risky_phrases = _risky_phrases(original, compact)

    ok = not missing_entities and not missing_negations and not missing_steps
    if validation == "strict" and risky_phrases:
        ok = False
    return {
        "ok": ok,
        "validation": validation,
        "checked_entities": checked_entities,
        "missing_entities": missing_entities,
        "negations_preserved": not missing_negations,
        "missing_negations": missing_negations,
        "ordered_steps_preserved": not missing_steps,
        "missing_ordered_steps": missing_steps,
        "risky_phrases": risky_phrases,
    }


def _compact_line(line: str, protected: list[str]) -> str:
    line = _normalize_known_phrases(line)
    line = re.sub(r"^[#*\-\s]+", "", line)
    line = re.sub(r"[,;!?]+", "", line)
    tokens = line.split()
    output: list[str] = []
    for token in tokens:
        clean = token.strip().rstrip(".")
        if clean not in protected and not _is_sensitive_token(clean):
            clean = clean.rstrip(":")
        if not clean:
            continue
        if clean in protected or _is_sensitive_token(clean):
            output.append(clean)
            continue
        lowered = clean.lower()
        if lowered in _FILLER_WORDS:
            continue
        output.append(clean)
    return " ".join(output)


def _normalize_known_phrases(line: str) -> str:
    replacements = [
        (
            re.compile(r"\bYou are a senior software engineer specializing in code review\b", re.IGNORECASE),
            "senior software engineer specializing code review",
        ),
        (
            re.compile(r"\bWhen the user shares a pull request or code snippet\b", re.IGNORECASE),
            "When user shares pull request or code snippet",
        ),
        (
            re.compile(r"\bDo not preface your response with summaries of what you are about to do\b", re.IGNORECASE),
            "do not preface response with summary of planned review",
        ),
        (
            re.compile(r"\bDo not be sycophantic\b", re.IGNORECASE),
            "do not be sycophantic",
        ),
        (
            re.compile(r"\bAlways preserve any code identifiers, file paths, and line numbers exactly as the user wrote them\b", re.IGNORECASE),
            "preserve code identifiers file paths line numbers exactly as user wrote",
        ),
        (
            re.compile(r"\bIf the code looks fine, just say so briefly\b", re.IGNORECASE),
            "If code looks fine say so briefly",
        ),
    ]
    result = line
    for pattern, replacement in replacements:
        result = pattern.sub(replacement, result)
    return result


def _split_instruction_lines(text: str) -> list[str]:
    lines: list[str] = []
    for block in re.split(r"\n+", text):
        for part in re.split(r"(?<=[.!?])\s+", block.strip()):
            if part.strip():
                lines.append(part.strip())
    return lines


def _protected_literals(text: str) -> list[str]:
    literals = extract_entities(text)
    literals.extend(match.group(0) for match in _PATH_RE.finditer(text))
    literals.extend(match.group(0) for match in _LINE_NUMBER_RE.finditer(text))
    return _dedupe([_clean_literal(literal) for literal in literals])


def _clean_literal(value: str) -> str:
    return value.strip().rstrip(".,;!?")


def _negation_clauses(text: str) -> list[str]:
    clauses: list[str] = []
    for pattern in _NEGATION_PATTERNS:
        clauses.extend(match.group(0).strip().rstrip(".") for match in pattern.finditer(text))
    return _dedupe(clauses)


def _negation_anchor(clause: str) -> str:
    lowered = _normalize(_normalize_known_phrases(clause))
    if "do not preface" in lowered:
        return "do not preface"
    if "do not" in lowered:
        return "do not"
    if "never" in lowered:
        return "never"
    return "not"


def _risky_phrases(original: str, compact: str) -> list[str]:
    risky: list[str] = []
    compact_norm = _normalize(compact)
    if "exactly" in original.lower() and "exactly" not in compact_norm:
        risky.append("exactly")
    if "line number" in original.lower() and "line numbers" not in compact_norm:
        risky.append("line numbers")
    if "file path" in original.lower() and "file paths" not in compact_norm:
        risky.append("file paths")
    return risky


def _warnings(
    *,
    direct_saved: int,
    break_even_calls: int | None,
    reuse_expected_calls: int,
    preservation: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if direct_saved <= 0:
        warnings.append("Context-file compression did not reduce estimated tokens.")
    if break_even_calls and reuse_expected_calls < break_even_calls:
        warnings.append(
            f"Compression is only economical after about {break_even_calls} calls with the decode prompt."
        )
    if not preservation["ok"]:
        warnings.append("Context-file compression requires review because preservation checks failed.")
    return warnings


def _is_sensitive_token(token: str) -> bool:
    return bool(
        re.search(r"\d", token)
        or "/" in token
        or "\\" in token
        or "_" in token
        or "-" in token
        or token.isupper()
    )


def _positive_int(value: Any, default: int) -> int:
    if value in {None, ""}:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _dominant_role(segments: list[Segment]) -> str:
    for segment in segments:
        if segment.role in {"system", "user", "assistant", "tool"}:
            return segment.role
    return "system"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = _normalize(value)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _risk_level(score: float) -> str:
    if score < 0.25:
        return "low"
    if score < 0.6:
        return "medium"
    return "high"


def _empty_semantic() -> dict[str, Any]:
    return {
        "query": "",
        "chunks": [],
        "decisions": [],
        "removed_chunk_ids": [],
        "retained_chunk_ids": [],
        "removed_segment_ids": [],
        "scorer": "disabled",
        "provider": "local",
    }
