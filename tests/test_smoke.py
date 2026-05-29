"""Tests for promptcompiler.smoke."""

from __future__ import annotations

import unittest

from promptcompiler.smoke import smoke_test


class SmokeTests(unittest.TestCase):
    def test_smoke_ok_on_simple_input(self):
        result = smoke_test("Hello world", mode="lossless")
        self.assertEqual(result["failed"], [])
        self.assertGreater(len(result["passed"]), 0)
        self.assertIn("optimized_text", result)

    def test_smoke_ok_with_pinned_entity(self):
        result = smoke_test("@pin Keep CASE-123.\n\nDuplicate\n\nDuplicate", mode="aggressive")
        self.assertEqual(result["failed"], [])
        self.assertIn("optimized_text", result)
        self.assertTrue(result["preservation_ok"])

    def test_smoke_reports_missing_entity(self):
        text = "@pin Keep CASE-123.\nAlso mention CASE-999."
        result = smoke_test(text, mode="lossless")
        # lossless should preserve by default
        self.assertEqual(result["failed"], [])
        self.assertTrue(result["preservation_ok"])

    def test_smoke_output_not_empty(self):
        result = smoke_test("Short.", mode="balanced")
        self.assertTrue(result["optimized_text"])
        self.assertNotIn("optimized_text is empty",
                         [f for f in result["failed"] if f == "optimized_text is empty"])

    def test_token_count_does_not_increase(self):
        result = smoke_test("Some text here to test.", mode="balanced")
        self.assertLessEqual(result["optimized_tokens"], result["original_tokens"])
