"""Token waste linting rules."""

from __future__ import annotations

from .tokenizer import estimate_text_tokens


def lint_token_waste(text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    lowered = text.lower()
    tokens = estimate_text_tokens(text)
    if tokens > 1200 and ("you are" in lowered or "assistant" in lowered[:500]):
        findings.append(
            {
                "code": "HUGE_SYSTEM_PROMPT",
                "severity": "high",
                "message": "Large reusable instruction block should move to a prompt_ref or server-side policy.",
            }
        )
    multi_markers = sum(
        1
        for marker in ("analyze", "explain", "optimize", "write tests", "generate docs")
        if marker in lowered
    )
    if multi_markers >= 3:
        findings.append(
            {
                "code": "MULTI_TASK_REQUEST",
                "severity": "medium",
                "message": "Split this request into sequential compile/analyze/test/doc steps.",
            }
        )
    if any(marker in lowered for marker in ("reflection:", "self critique", "self-critique", "thought:")):
        findings.append(
            {
                "code": "AGENT_REFLECTION_OVERHEAD",
                "severity": "medium",
                "message": "Remove recursive agent reasoning and reflection blocks before provider calls.",
            }
        )
    if lowered.count("source:") > 10:
        findings.append(
            {
                "code": "TOO_MANY_RETRIEVED_RESULTS",
                "severity": "high",
                "message": "Apply top-k retrieval and chunk compression before injection.",
            }
        )
    return findings
