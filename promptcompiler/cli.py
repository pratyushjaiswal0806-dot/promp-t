"""Command line interface for PromptCompiler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .analyzer import analyze_prompt
from .compiler import compile_prompt
from .models import DEFAULT_NIM_MODEL, list_models


def run_cli(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "models":
        print(json.dumps({"default_model": DEFAULT_NIM_MODEL, "models": list_models()}, indent=2))
        return 0

    text = Path(args.input).read_text(encoding="utf-8")

    if args.command == "analyze":
        print(json.dumps(analyze_prompt(text, model=args.model), indent=2))
        return 0

    if args.command == "compile":
        result = compile_prompt(text, model=args.model)
        if args.out:
            Path(args.out).write_text(result["optimized_text"], encoding="utf-8")
        else:
            print(json.dumps(result, indent=2))
        return 0

    parser.error(f"unknown command {args.command}")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="promptcompiler")
    subcommands = parser.add_subparsers(dest="command", required=True)

    analyze = subcommands.add_parser("analyze", help="Analyze a prompt file")
    analyze.add_argument("input", help="Path to a text or JSON prompt file")
    analyze.add_argument("--model", default=DEFAULT_NIM_MODEL)

    compile_cmd = subcommands.add_parser("compile", help="Compile a prompt file")
    compile_cmd.add_argument("input", help="Path to a text or JSON prompt file")
    compile_cmd.add_argument("--model", default=DEFAULT_NIM_MODEL)
    compile_cmd.add_argument("--out", help="Write optimized text to this file")

    subcommands.add_parser("models", help="List configured model ids")
    return parser


def main() -> None:
    raise SystemExit(run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
