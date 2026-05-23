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
