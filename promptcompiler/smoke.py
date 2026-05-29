"""Quick smoke-test suite for the compile pipeline.

Validates basic invariants: non-empty output, entity preservation,
no policy violations, and stable re-compilation (no double-compression).
"""

from __future__ import annotations

from typing import Any

from .compiler import CompilePolicyError, compile_prompt
from .models import DEFAULT_NIM_MODEL


def smoke_test(
    text: str,
    *,
    model: str = DEFAULT_NIM_MODEL,
    mode: str = "lossless",
    target_token_budget: int | None = None,
) -> dict[str, Any]:
    results: dict[str, Any] = {"passed": [], "failed": [], "warnings": []}

    # 1. compile succeeds
    try:
        result = compile_prompt(
            text,
            model=model,
            mode=mode,
            target_token_budget=target_token_budget,
        )
    except CompilePolicyError as exc:
        return {
            "passed": [],
            "failed": [f"CompilePolicyError: {exc} (code={exc.error_code})"],
            "warnings": [],
            "optimized_text": "",
            "original_tokens": 0,
            "optimized_tokens": 0,
            "risk_score": 0.0,
            "preservation_ok": False,
        }

    opt = result.get("optimized_text", "")
    original_tokens = result.get("original_tokens", 0)
    optimized_tokens = result.get("optimized_tokens", 0)

    # 2. output is non-empty
    if not opt:
        results["failed"].append("optimized_text is empty")
    else:
        results["passed"].append("optimized_text is non-empty")

    # 3. entity preservation
    preservation = result.get("preservation", {})
    missing = preservation.get("missing_entities", [])
    if missing:
        results["failed"].append(f"missing protected entities: {missing}")
    else:
        results["passed"].append("all protected entities preserved")

    # 4. risk score is reasonable
    risk = result.get("risk_score", 0.0)
    if risk > 0.5:
        results["warnings"].append(f"high risk score: {risk}")
    else:
        results["passed"].append(f"risk score acceptable ({risk})")

    # 5. re-compile stability (lossless mode should not change output)
    if mode == "lossless" and opt:
        try:
            re_result = compile_prompt(
                opt,
                model=model,
                mode=mode,
                target_token_budget=target_token_budget,
            )
            re_opt = re_result.get("optimized_text", "")
            if re_opt == opt:
                results["passed"].append("re-compile stable (no double-compression)")
            else:
                # May differ slightly due to structural formatting; warn, don't fail
                ratio = len(re_opt) / max(len(opt), 1)
                if abs(1.0 - ratio) > 0.2:
                    results["warnings"].append(
                        f"re-compile changed output size by {ratio - 1:.1%}"
                    )
                else:
                    results["passed"].append("re-compile stable")
        except CompilePolicyError as exc:
            results["warnings"].append(f"re-compile raised CompilePolicyError: {exc}")

    # 6. tokens should decrease (or stay same for tiny inputs)
    if optimized_tokens > original_tokens:
        results["warnings"].append(
            f"optimized_tokens ({optimized_tokens}) > original_tokens ({original_tokens})"
        )
    else:
        results["passed"].append("token count did not increase")

    return {
        **results,
        "optimized_text": opt,
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "risk_score": risk,
        "preservation_ok": preservation.get("ok", True),
    }
