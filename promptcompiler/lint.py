"""Token waste linting rules."""

from __future__ import annotations

import re

from .tokenizer import estimate_text_tokens


def lint_token_waste(text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    lowered = text.lower()
    tokens = estimate_text_tokens(text)

    # Large system prompt
    if tokens > 1200 and ("you are" in lowered or "assistant" in lowered[:500]):
        findings.append(
            {
                "code": "HUGE_SYSTEM_PROMPT",
                "severity": "high",
                "message": "Large reusable instruction block should move to a prompt_ref or server-side policy.",
            }
        )

    # Multi-task request
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

    # Agent reflection overhead
    if any(marker in lowered for marker in ("reflection:", "self critique", "self-critique", "thought:")):
        findings.append(
            {
                "code": "AGENT_REFLECTION_OVERHEAD",
                "severity": "medium",
                "message": "Remove recursive agent reasoning and reflection blocks before provider calls.",
            }
        )

    # Too many retrieved results
    if lowered.count("source:") > 10:
        findings.append(
            {
                "code": "TOO_MANY_RETRIEVED_RESULTS",
                "severity": "high",
                "message": "Apply top-k retrieval and chunk compression before injection.",
            }
        )

    # Vague instructions
    vague_patterns = [
        (r"\b(?:make it better|improve this|fix this|handle this)\b", "VAGUE_INSTRUCTION"),
        (r"\b(?:etc\.?|and so on|and more|and other things)\b", "ETC_MARKERS"),
        (r"\b(?:as needed|when necessary|if applicable|optional)\b", "CONDITIONAL_VAGUE"),
    ]
    for pattern, code in vague_patterns:
        matches = re.findall(pattern, lowered)
        if len(matches) >= 2:
            findings.append(
                {
                    "code": code,
                    "severity": "medium",
                    "message": f"Found {len(matches)} vague instructions. Replace with specific success criteria.",
                }
            )

    # Missing success criteria
    success_markers = ["success criteria", "acceptance criteria", "definition of done", "expected output", "output format"]
    if tokens > 500 and not any(m in lowered for m in success_markers):
        findings.append(
            {
                "code": "NO_SUCCESS_CRITERIA",
                "severity": "medium",
                "message": "No success criteria defined. Add expected output format or acceptance criteria.",
            }
        )

    # Overly broad scope
    scope_markers = ["full-stack", "production-ready", "enterprise", "comprehensive", "complete"]
    scope_count = sum(1 for m in scope_markers if m in lowered)
    if scope_count >= 3:
        findings.append(
            {
                "code": "OVERLY_BROAD_SCOPE",
                "severity": "medium",
                "message": f"Prompt requests {scope_count} broad capabilities. Consider splitting into focused tasks.",
            }
        )

    # Repetitive phrasing
    words = lowered.split()
    if len(words) > 50:
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        bigram_counts = {}
        for b in bigrams:
            bigram_counts[b] = bigram_counts.get(b, 0) + 1
        repeats = {k: v for k, v in bigram_counts.items() if v >= 4 and len(k) > 5}
        if repeats:
            top = sorted(repeats.items(), key=lambda x: x[1], reverse=True)[:3]
            findings.append(
                {
                    "code": "REPETITIVE_PHRASING",
                    "severity": "low",
                    "message": f"Repeated phrases: {', '.join(f'{k} ({v}x)' for k, v in top)}.",
                }
            )

    # Too many bullet points
    bullet_count = len(re.findall(r"^[-*]\s", text, re.MULTILINE))
    if bullet_count > 30:
        findings.append(
            {
                "code": "EXCESSIVE_BULLETS",
                "severity": "low",
                "message": f"{bullet_count} bullet points detected. Group related items into paragraphs.",
            }
        )

    # Missing context for code
    if "```" in text and "language" not in lowered and "lang:" not in lowered:
        code_blocks = text.count("```")
        if code_blocks >= 2:
            findings.append(
                {
                    "code": "UNSPECIFIED_CODE_LANGUAGE",
                    "severity": "low",
                    "message": f"{code_blocks} code blocks found without language specification.",
                }
            )

    return findings
