"""Command line interface for PromptCompiler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .analyzer import analyze_prompt
from .compiler import CompilePolicyError, compile_prompt
from .models import DEFAULT_NIM_MODEL, list_models
from .smoke import smoke_test
from .v1 import lint_v1, retrieve_v1


def run_cli(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "models":
        print(json.dumps({"default_model": DEFAULT_NIM_MODEL, "models": list_models()}, indent=2))
        return 0

    if args.command == "verify":
        return _run_verify()

    if args.command == "serve":
        _start_server(args.host, args.port)
        return 0

    if args.command == "retrieve":
        payload: dict[str, Any] = {"query": args.query or "", "rag_chunks": _read_chunks_file(args.chunks) if args.chunks else [], "top_k": args.top_k, "max_tokens": args.max_tokens}
        result = retrieve_v1(payload)
        print(json.dumps(result, indent=2))
        return 0

    text = Path(args.input).read_text(encoding="utf-8")

    if args.command == "analyze":
        print(json.dumps(analyze_prompt(text, model=args.model), indent=2))
        return 0

    if args.command == "compile":
        if args.smoke_test:
            result = smoke_test(text, model=args.model, mode=args.mode, target_token_budget=args.target_token_budget)
            passed = len(result["passed"])
            failed = len(result["failed"])
            print(json.dumps({k: v for k, v in result.items() if k != "optimized_text"}, indent=2))
            if failed:
                print(f"SMOKE TEST FAILED ({failed} failures, {passed} passed)")
                return 1
            print(f"SMOKE TEST PASSED ({passed} checks)")
            return 0
        try:
            result = compile_prompt(text, model=args.model, mode=args.mode, target_token_budget=args.target_token_budget, dry_run=args.dry_run)
        except CompilePolicyError as exc:
            print(json.dumps({"error": str(exc), "code": exc.error_code, "details": exc.details}, indent=2))
            return 1
        if args.out:
            Path(args.out).write_text(result["optimized_text"], encoding="utf-8")
        else:
            print(json.dumps(result, indent=2))
        return 0

    if args.command == "lint":
        payload: dict[str, Any] = {"input": text}
        result = lint_v1(payload)
        print(json.dumps(result, indent=2))
        return 0

    parser.error(f"unknown command {args.command}")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="promptcompiler")
    subcommands = parser.add_subparsers(dest="command", required=True)

    server = subcommands.add_parser("serve", help="Start the FastAPI server")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8765)

    analyze = subcommands.add_parser("analyze", help="Analyze a prompt file")
    analyze.add_argument("input", help="Path to a text or JSON prompt file")
    analyze.add_argument("--model", default=DEFAULT_NIM_MODEL)

    compile_cmd = subcommands.add_parser("compile", help="Compile a prompt file")
    compile_cmd.add_argument("input", help="Path to a text or JSON prompt file")
    compile_cmd.add_argument("--model", default=DEFAULT_NIM_MODEL)
    compile_cmd.add_argument("--mode", choices=["lossless", "balanced", "aggressive", "context_file"], default="lossless")
    compile_cmd.add_argument("--target-token-budget", type=int, default=None, help="Target token budget for compression")
    compile_cmd.add_argument("--dry-run", action="store_true", help="Show compression plan without mutating")
    compile_cmd.add_argument("--smoke-test", action="store_true", help="Run smoke-test validation instead of normal compilation")
    compile_cmd.add_argument("--out", help="Write optimized text to this file")

    lint_cmd = subcommands.add_parser("lint", help="Lint a prompt for token waste")
    lint_cmd.add_argument("input", help="Path to a text or JSON prompt file")

    retrieve_cmd = subcommands.add_parser("retrieve", help="Retrieve relevant RAG chunks")
    retrieve_cmd.add_argument("--query", help="Search query")
    retrieve_cmd.add_argument("--chunks", help="Path to JSON file with rag_chunks array")
    retrieve_cmd.add_argument("--top-k", type=int, default=5)
    retrieve_cmd.add_argument("--max-tokens", type=int, default=1200)

    subcommands.add_parser("models", help="List configured model ids")
    verify = subcommands.add_parser("verify", help="Run self-verification: health check, smoke test, and module import check")
    return parser


def _run_verify() -> int:
    """Run a self-verification health check."""
    import traceback as _tb

    checks: list[tuple[str, str]] = []

    # 1. Import all core modules
    core_modules = [
        "promptcompiler.analyzer",
        "promptcompiler.compiler",
        "promptcompiler.context_compression",
        "promptcompiler.embeddings",
        "promptcompiler.entities",
        "promptcompiler.models",
        "promptcompiler.nim",
        "promptcompiler.policies",
        "promptcompiler.semantic",
        "promptcompiler.storage",
        "promptcompiler.tokenizer",
        "promptcompiler.v1",
        "promptcompiler.lint",
        "promptcompiler.cache",
        "promptcompiler.runtime",
    ]
    for module_name in core_modules:
        try:
            __import__(module_name)
            checks.append((f"import:{module_name}", "ok"))
        except Exception as exc:  # noqa: BLE001
            checks.append((f"import:{module_name}", f"FAIL: {exc}"))

    # 2. NIM configuration check
    try:
        from .nim import nim_is_configured
        nim_ok = nim_is_configured()
        checks.append(("nvidia_nim_configured", "ok" if nim_ok else "not configured (optional)"))
    except Exception as exc:
        checks.append(("nvidia_nim_configured", f"FAIL: {exc}"))

    # 3. Storage initialization check
    try:
        from .storage import SQLiteStore
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "verify.sqlite3")
            store.record_trace({
                "trace_id": "verify_tr",
                "endpoint": "verify",
                "provider": "local",
                "model": "test",
                "session_id": None,
                "mode": "lossless",
                "original_token_count": 1,
                "optimized_token_count": 1,
                "token_reduction_percent": 0.0,
                "estimated_cost_before_usd": 0.0,
                "estimated_cost_after_usd": 0.0,
                "cache_status": "bypass",
                "evaluation_status": "not_configured",
                "zero_retention": True,
                "latency_ms": 1,
                "transformations": [],
                "retention": {"raw_payload_stored": False},
            })
            store.close()
        checks.append(("storage_init", "ok"))
    except Exception as exc:
        checks.append(("storage_init", f"FAIL: {exc}"))

    # 4. Smoke test on a built-in sample
    sample_prompt = (
        "Analyze this code. Explain it. Optimize it. Write tests.\n"
        "@pin CASE-123\n"
        "The code handles user authentication for the support portal."
    )
    try:
        result = smoke_test(sample_prompt, model=DEFAULT_NIM_MODEL, mode="balanced")
        passed = len(result["passed"])
        failed = len(result["failed"])
        if failed:
            checks.append(("smoke_test", f"FAILED ({failed} failures)"))
        else:
            checks.append(("smoke_test", f"ok ({passed} checks passed)"))
    except Exception as exc:
        checks.append(("smoke_test", f"FAIL: {exc}"))

    # Print report
    print("PromptCompiler verify report")
    print("=" * 40)
    max_len = max(len(k) for k, _ in checks)
    for key, status in checks:
        pad = " " * (max_len - len(key))
        icon = "✅" if status == "ok" or "optional" in status or "checks" in status else "❌"
        print(f"  {icon}  {key}{pad}  {status}")
    print("=" * 40)

    failures = [k for k, v in checks if v.startswith("FAIL")]
    if failures:
        print(f"FAILED: {len(failures)} check(s) — {' '.join(failures)}")
        return 1
    print("All checks passed.")
    return 0


def _start_server(host: str, port: int) -> None:
    from .fastapi_server import run

    run(host=host, port=port)


def _read_chunks_file(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("rag_chunks", data.get("chunks", data.get("documents", [])))
    return []


def main() -> None:
    raise SystemExit(run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
