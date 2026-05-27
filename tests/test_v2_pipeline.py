"""Tests for the v2 pass pipeline."""

from __future__ import annotations

import json
import unittest

from promptcompiler.ir import ContextGraph
from promptcompiler.passes import (
    CompilerPipeline,
    Diagnostic,
    PassContext,
    PassRegistry,
    ParsePass,
    NormalizePass,
    DedupPass,
    EntityResolutionPass,
    SummarizePass,
    BudgetPass,
    EmitPass,
)
from promptcompiler.runtime import CompilerRuntime
from promptcompiler.settings import CompilerSettings


def _make_ctx() -> PassContext:
    return PassContext(compiler_version="test", settings=CompilerSettings())


def _make_pipeline(*ids: str) -> CompilerPipeline:
    return PassRegistry.build_pipeline("test", list(ids))


def _make_graph(raw: str, **kw: object) -> ContextGraph:
    g = ContextGraph(compiler_version="test", pipeline_config=dict(kw))
    g.data["raw_input"] = raw
    return g


class TestParsePass(unittest.TestCase):
    def test_plain_text_splits_at_blank_lines(self) -> None:
        graph = _make_graph("Hello\n\nWorld")
        result = _make_pipeline("parse.v1").execute(graph, _make_ctx())
        self.assertEqual(len(result.output_graph.segments), 2)
        segs = list(result.output_graph.traverse("dfs"))
        self.assertEqual(segs[0].text, "Hello")
        self.assertEqual(segs[1].text, "World")

    def test_empty_input(self) -> None:
        graph = _make_graph("")
        result = _make_pipeline("parse.v1").execute(graph, _make_ctx())
        self.assertEqual(len(result.output_graph.segments), 0)

    def test_messages_array(self) -> None:
        raw = json.dumps({
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hi"},
            ]
        })
        graph = _make_graph(raw)
        result = _make_pipeline("parse.v1").execute(graph, _make_ctx())
        self.assertEqual(len(result.output_graph.segments), 2)
        roles = [s.context_role.name for s in result.output_graph.traverse("dfs")]
        self.assertEqual(roles, ["SYSTEM", "USER"])


class TestNormalizePass(unittest.TestCase):
    def test_normalizes_whitespace(self) -> None:
        graph = _make_graph("Hi\n\n\n\nThere")
        result = _make_pipeline("parse.v1", "normalize.v1").execute(graph, _make_ctx())
        segs = list(result.output_graph.traverse("dfs"))
        self.assertEqual(segs[0].text, "Hi")
        self.assertEqual(segs[1].text, "There")


class TestDedupPass(unittest.TestCase):
    def test_removes_exact_duplicates(self) -> None:
        graph = _make_graph("Hello\n\nGoodbye\n\nHello")
        result = _make_pipeline("parse.v1", "normalize.v1", "dedup.v1").execute(graph, _make_ctx())
        self.assertEqual(len(result.output_graph.segments), 2)

    def test_pinned_are_not_deduped(self) -> None:
        graph = _make_graph("Hello\n\n@pin Hello")
        result = _make_pipeline("parse.v1", "normalize.v1", "dedup.v1").execute(graph, _make_ctx())
        self.assertEqual(len(result.output_graph.segments), 2)


class TestEntityResolutionPass(unittest.TestCase):
    def test_detects_urls_and_dates(self) -> None:
        graph = _make_graph("Visit https://example.com\n\nDate: 2026-05-28")
        result = _make_pipeline("parse.v1", "normalize.v1", "entity_resolve.v1").execute(graph, _make_ctx())
        self.assertGreater(len(result.output_graph.entities.entities), 0)
        etypes = {e.entity_type for e in result.output_graph.entities.entities.values()}
        self.assertIn("url", etypes)
        self.assertIn("date", etypes)


class TestSummarizePass(unittest.TestCase):
    def test_repeated_lines_collapsed(self) -> None:
        text = "line\nline\nline"
        graph = _make_graph(text, mode="aggressive")
        result = _make_pipeline("parse.v1", "normalize.v1", "summarize.v1").execute(graph, _make_ctx())
        segs = result.output_graph.traverse("dfs")
        self.assertGreater(len(segs), 0)
        self.assertIn("repeated", segs[0].text)

    def test_tool_truncation_in_aggressive(self) -> None:
        """Simulate a long tool output with >22 lines."""
        lines = [f"line {i}" for i in range(30)]
        text = "\n".join(lines)
        graph = _make_graph(text, mode="aggressive")
        result = _make_pipeline("parse.v1", "normalize.v1", "summarize.v1").execute(graph, _make_ctx())
        segs = result.output_graph.traverse("dfs")
        self.assertGreater(len(segs), 0)
        self.assertIn("omitted", segs[0].text)


class TestBudgetPass(unittest.TestCase):
    def test_drops_low_priority_segments(self) -> None:
        graph = _make_graph("A\n\nBB\n\nCCC", target_token_budget=8)
        result = _make_pipeline("parse.v1", "normalize.v1", "budget.v1").execute(graph, _make_ctx())
        # budget=8 should drop some segments
        self.assertLess(len(result.output_graph.segments), 3)


class TestEmitPass(unittest.TestCase):
    def test_produces_output_text(self) -> None:
        graph = _make_graph("Hello\n\nWorld")
        result = _make_pipeline("parse.v1", "normalize.v1", "emit.v1").execute(graph, _make_ctx())
        self.assertIn("output_text", result.output_graph.data)
        self.assertIn("Hello", result.output_graph.data["output_text"])
        self.assertIn("World", result.output_graph.data["output_text"])


class TestCompilerRuntime(unittest.TestCase):
    def test_compile_to_text_roundtrip(self) -> None:
        runtime = CompilerRuntime()
        text = runtime.compile_to_text("Hello\n\nWorld")
        self.assertEqual(text, "Hello\n\nWorld")

    def test_compile_with_budget(self) -> None:
        runtime = CompilerRuntime()
        result = runtime.compile("A\n\nBB\n\nCCC\n\nDDDD", target_token_budget=10)
        self.assertIn("output_text", result.output_graph.data)
        self.assertLessEqual(len(result.output_graph.data["output_text"].split("\n\n")), 2)

    def test_all_diagnostics_present(self) -> None:
        runtime = CompilerRuntime()
        result = runtime.compile("Hi")
        self.assertGreaterEqual(len(result.diagnostics), 1)


if __name__ == "__main__":
    unittest.main()
