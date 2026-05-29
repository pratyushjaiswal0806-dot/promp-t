"""Benchmark runner for PromptCompiler.

Usage:
    python benchmarks/evaluate.py               # run all prompts, write baseline.json
    python benchmarks/evaluate.py --check        # check current results against baseline.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from promptcompiler.compiler import compile_prompt


BENCHMARKS_DIR = Path(__file__).resolve().parent
PROMPTS_PATH = BENCHMARKS_DIR / "prompts.json"
BASELINE_PATH = BENCHMARKS_DIR / "baseline.json"

_DEFAULT_SCORERS = {"lossless": "lexical", "balanced": "lexical", "aggressive": "lexical"}


def load_prompts() -> list[dict[str, Any]]:
    with open(PROMPTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_single(prompt: dict[str, Any], mode: str) -> dict[str, Any]:
    opts = dict(prompt.get("compile_opts") or {})
    budget = opts.pop("target_token_budget", None)
    semantic_policy = opts.pop("semantic_policy", None)
    start = time.perf_counter()
    result = compile_prompt(
        prompt["input"],
        mode=mode,
        target_token_budget=budget,
        semantic_policy=semantic_policy,
        **opts,
    )
    elapsed = time.perf_counter() - start

    tokens_saved = result.get("tokens_saved", 0)
    original_tokens = result.get("original_tokens", 0)
    savings_ratio = tokens_saved / original_tokens if original_tokens else 0.0

    preserved = result.get("preservation", {})
    entities_checked = len(preserved.get("checked_entities", []))
    entities_missing = len(preserved.get("missing_entities", []))

    return {
        "mode": mode,
        "original_tokens": original_tokens,
        "optimized_tokens": result.get("optimized_tokens", 0),
        "tokens_saved": tokens_saved,
        "savings_ratio": round(savings_ratio, 4),
        "elapsed_seconds": round(elapsed, 4),
        "entity_entities_checked": entities_checked,
        "entity_entities_missing": entities_missing,
        "entity_preservation_ok": preserved.get("ok", True),
        "changes_count": len(result.get("changes", [])),
        "risk_score": result.get("risk_score", 0.0),
        "warnings": result.get("warnings", []),
        "optimized_text": result.get("optimized_text", ""),
    }


def run_benchmark() -> dict[str, Any]:
    prompts = load_prompts()
    results: dict[str, Any] = {}

    for prompt in prompts:
        pid = prompt["id"]
        modes = prompt.get("modes", ["lossless"])
        entry: dict[str, Any] = {
            "name": prompt["name"],
            "category": prompt["category"],
            "tags": prompt.get("tags", []),
            "modes": {},
        }
        for mode in modes:
            entry["modes"][mode] = run_single(prompt, mode)
        results[pid] = entry

    return {
        "prompt_count": len(prompts),
        "results": results,
    }


def write_baseline(data: dict[str, Any]) -> None:
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Baseline written to {BASELINE_PATH}")


def load_baseline() -> dict[str, Any]:
    with open(BASELINE_PATH, encoding="utf-8") as f:
        return json.load(f)


def check_against_baseline() -> bool:
    current = run_benchmark()
    baseline = load_baseline()

    errors: list[str] = []
    for pid, cur_entry in current["results"].items():
        base_entry = baseline["results"].get(pid)
        if base_entry is None:
            errors.append(f"  {pid}: missing in baseline")
            continue
        for mode, cur_mode in cur_entry["modes"].items():
            base_mode = base_entry["modes"].get(mode)
            if base_mode is None:
                errors.append(f"  {pid}/{mode}: missing in baseline")
                continue
            for key in ("original_tokens", "optimized_tokens", "entity_preservation_ok",
                        "risk_score", "savings_ratio"):
                cv = cur_mode.get(key)
                bv = base_mode.get(key)
                if key in ("entity_preservation_ok",):
                    if cv != bv:
                        errors.append(f"  {pid}/{mode}: {key} changed {bv} -> {cv}")
                elif key == "risk_score":
                    if abs((cv or 0.0) - (bv or 0.0)) > 0.01:
                        errors.append(f"  {pid}/{mode}: {key} changed {bv} -> {cv}")
                else:
                    if cv != bv:
                        errors.append(f"  {pid}/{mode}: {key} changed {bv} -> {cv}")

    if errors:
        print(f"BASELINE MISMATCH ({len(errors)} differences):")
        for err in errors:
            print(err)
        return False
    print("All checks passed against baseline.")
    return True


def main() -> None:
    os.environ.setdefault("PROMPTCOMPILER_DISABLE_DOTENV", "1")

    if "--check" in sys.argv:
        success = check_against_baseline()
        sys.exit(0 if success else 1)
    else:
        data = run_benchmark()
        write_baseline(data)
        total = data["prompt_count"]
        mode_counts: dict[str, int] = {}
        mode_savings: dict[str, list[float]] = {}
        for entry in data["results"].values():
            for mode, m in entry["modes"].items():
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
                mode_savings.setdefault(mode, []).append(m["savings_ratio"])

        print(f"Ran {total} prompts.")
        for mode in sorted(mode_counts):
            savings = mode_savings[mode]
            avg = sum(savings) / len(savings) if savings else 0.0
            print(f"  {mode}: {mode_counts[mode]} runs, avg savings {avg:.2%}")


if __name__ == "__main__":
    main()
