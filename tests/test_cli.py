import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from promptcompiler.cli import run_cli
from promptcompiler.models import DEFAULT_NIM_MODEL


class CliTests(unittest.TestCase):
    def test_cli_analyze_prints_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.txt"
            path.write_text("repeat\n\nrepeat", encoding="utf-8")
            out = StringIO()

            with redirect_stdout(out):
                code = run_cli(["analyze", str(path)])

        payload = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["duplicate_groups"][0]["count"], 2)

    def test_cli_compile_can_write_output_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "prompt.txt"
            target = Path(directory) / "optimized.txt"
            source.write_text("@pin Keep CASE-123.\n\nx\n\nx", encoding="utf-8")

            code = run_cli(["compile", str(source), "--out", str(target)])

            self.assertEqual(code, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "@pin Keep CASE-123.\n\nx")

    def test_cli_models_uses_non_oss_default(self):
        out = StringIO()

        with redirect_stdout(out):
            code = run_cli(["models"])

        payload = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["default_model"], DEFAULT_NIM_MODEL)
        self.assertNotEqual(payload["default_model"], "openai/gpt-oss-20b")

    def test_cli_compile_with_mode_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.txt"
            path.write_text("Hello " * 30, encoding="utf-8")
            out = StringIO()

            with redirect_stdout(out):
                code = run_cli(["compile", str(path), "--mode", "aggressive"])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["mode"], "aggressive")

    def test_cli_compile_with_target_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.txt"
            path.write_text("Hello world " * 50, encoding="utf-8")
            out = StringIO()

            with redirect_stdout(out):
                code = run_cli(["compile", str(path), "--mode", "aggressive", "--target-token-budget", "50"])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["target_token_budget"], 50)
        self.assertTrue(payload["warnings"])

    def test_cli_compile_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.txt"
            source_text = "Hello there " * 20 + "\n\nGoodbye " * 20
            path.write_text(source_text, encoding="utf-8")
            out = StringIO()

            with redirect_stdout(out):
                code = run_cli(["compile", str(path), "--dry-run"])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["optimized_text"], source_text)

    def test_cli_lint_subcommand(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.txt"
            path.write_text("Analyze this code, explain it, optimize it, write tests", encoding="utf-8")
            out = StringIO()

            with redirect_stdout(out):
                code = run_cli(["lint", str(path)])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertIn("findings", payload)

    def test_cli_retrieve_subcommand(self):
        with tempfile.TemporaryDirectory() as directory:
            chunks_file = Path(directory) / "chunks.json"
            chunks_data = [
                {"id": "c1", "text": "Refunds over $500 require manager approval."},
                {"id": "c2", "text": "Standard refunds are processed within 5 business days."},
            ]
            chunks_file.write_text(json.dumps(chunks_data), encoding="utf-8")
            out = StringIO()

            with redirect_stdout(out):
                code = run_cli(["retrieve", "--query", "refund approval", "--chunks", str(chunks_file), "--top-k", "2"])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertIn("chunks", payload)

    def test_cli_compile_rejects_invalid_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.txt"
            path.write_text("Hello world", encoding="utf-8")
            with self.assertRaises(SystemExit):
                run_cli(["compile", str(path), "--mode", "invalid"])
