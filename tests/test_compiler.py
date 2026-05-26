import unittest

from promptcompiler.compiler import CompilePolicyError, compile_prompt


class CompilerTests(unittest.TestCase):
    def test_compile_removes_duplicate_unpinned_segments_but_preserves_pin(self):
        payload = "@pin Keep CASE-123 exactly.\n\nremove me\n\nremove me"

        result = compile_prompt(payload)

        self.assertIn("@pin Keep CASE-123 exactly.", result["optimized_text"])
        self.assertEqual(result["optimized_text"].count("remove me"), 1)
        self.assertGreater(result["tokens_saved"], 0)
        self.assertTrue(
            any(change["type"] == "duplicate_removed" for change in result["changes"])
        )
        self.assertIn("diff", result)
        self.assertTrue(any(item["status"] == "removed" for item in result["diff"]))

    def test_compile_compacts_repeated_log_lines(self):
        payload = "ERROR same failure\nERROR same failure\nERROR same failure\nnext line"

        result = compile_prompt(payload)

        self.assertIn("[repeated 2 more times]", result["optimized_text"])
        self.assertIn("next line", result["optimized_text"])

    def test_compile_preserves_unique_entities_in_large_tool_output(self):
        lines = ["ERROR noise"] * 90
        lines.insert(50, "Important tracking URL https://example.com/keep/CASE-999")
        payload = "\n".join(lines)

        result = compile_prompt(payload)

        self.assertIn("https://example.com/keep/CASE-999", result["optimized_text"])
        self.assertIn("CASE-999", result["optimized_text"])

    def test_compile_reports_protected_entity_preservation(self):
        result = compile_prompt("@pin Keep CASE-123 and 2026-05-23.\n\nrepeat\n\nrepeat")

        self.assertTrue(result["preservation"]["ok"])
        self.assertIn("CASE-123", result["preservation"]["checked_entities"])
        self.assertEqual(result["preservation"]["missing_entities"], [])

    def test_compile_defaults_to_lossless_mode_and_returns_plan_metadata(self):
        result = compile_prompt("@pin Keep CASE-123.\n\nrepeat\n\nrepeat")

        self.assertEqual(result["mode"], "lossless")
        self.assertFalse(result["dry_run"])
        self.assertIn("plan", result)
        self.assertEqual(result["plan"]["mode"], "lossless")
        self.assertTrue(any(action["action"] == "dedupe" for action in result["plan"]["actions"]))

    def test_lossless_mode_reports_no_savings_when_text_is_unchanged(self):
        payload = (
            "Analyze this code, explain it, optimize it, write tests, generate docs for CASE-123.\n\n"
            "Source: doc-a\nRefunds over $500 require manager approval.\n\n"
            "Source: doc-b\nRefunds over $500 require manager approval."
        )

        result = compile_prompt(payload, mode="lossless")

        self.assertEqual(result["optimized_text"], payload)
        self.assertEqual(result["optimized_tokens"], result["original_tokens"])
        self.assertEqual(result["tokens_saved"], 0)
        self.assertEqual(result["savings_ratio"], 0)

    def test_compile_dry_run_returns_plan_without_activating_output(self):
        result = compile_prompt("alpha\n\nalpha", dry_run=True)

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["optimized_text"], "alpha\n\nalpha")
        self.assertGreater(result["proposed_tokens_saved"], 0)
        self.assertTrue(any(action["action"] == "dedupe" for action in result["plan"]["actions"]))

    def test_compile_rejects_pinned_content_over_target_budget_cap(self):
        with self.assertRaises(CompilePolicyError) as raised:
            compile_prompt("@pin one two three four five six seven eight", target_token_budget=8)

        self.assertEqual(raised.exception.status_code, 413)
        self.assertEqual(raised.exception.error_code, "PINNED_BUDGET_EXCEEDED")

    def test_balanced_mode_compacts_tool_output_more_than_lossless(self):
        payload = "ERROR noisy line\n" * 95 + "CASE-123 must stay\n" + "tail line\n" * 20

        lossless = compile_prompt(payload, mode="lossless")
        balanced = compile_prompt(payload, mode="balanced")

        self.assertIn("CASE-123", balanced["optimized_text"])
        self.assertLess(balanced["optimized_tokens"], lossless["optimized_tokens"])
        self.assertTrue(any(action["action"] == "tool_summary" for action in balanced["plan"]["actions"]))

    def test_aggressive_mode_returns_warning_when_target_cannot_be_met_safely(self):
        result = compile_prompt(
            "@pin Keep CASE-123 exactly.\n\n" + ("word " * 80),
            mode="aggressive",
            target_token_budget=60,
        )

        self.assertIn("@pin Keep CASE-123 exactly.", result["optimized_text"])
        self.assertTrue(result["warnings"])

    def test_balanced_mode_prunes_redundant_rag_and_reports_semantic_metadata(self):
        payload = (
            "Question: Does a refund over $500 require manager approval?\n\n"
            "Source: doc-a\nRefunds over $500 require manager approval for CASE-345.\n\n"
            "Source: doc-b\nRefunds over $500 require manager approval for CASE-345.\n\n"
            "Source: doc-c\nRefunds over $500 for CASE-999 also require finance review."
        )

        result = compile_prompt(payload, mode="balanced")

        self.assertIn("Source: doc-a", result["optimized_text"])
        self.assertNotIn("Source: doc-b", result["optimized_text"])
        self.assertIn("Source: doc-c", result["optimized_text"])
        self.assertIn("CASE-999", result["optimized_text"])
        self.assertTrue(result["semantic"]["removed_chunk_ids"])
        self.assertTrue(result["semantic"]["retained_chunk_ids"])
        self.assertTrue(
            any(action["action"] == "rag_prune" for action in result["plan"]["actions"])
        )

    def test_embedding_semantic_policy_prunes_paraphrased_rag_that_lexical_keeps(self):
        payload = (
            "Question: Do refunds over 500 need manager approval?\n\n"
            "Source: doc-a\nRefunds over 500 require manager approval.\n\n"
            "Source: doc-b\nReimbursements greater than 500 dollars need supervisor review."
        )

        lexical = compile_prompt(payload, mode="balanced")
        embedded = compile_prompt(
            payload,
            mode="balanced",
            semantic_policy={"scorer": "embedding", "provider": "deterministic"},
        )

        self.assertIn("Source: doc-b", lexical["optimized_text"])
        self.assertIn("Source: doc-a", embedded["optimized_text"])
        self.assertNotIn("Source: doc-b", embedded["optimized_text"])
        self.assertEqual(embedded["semantic"]["scorer"], "embedding")
        self.assertEqual(embedded["semantic"]["provider"], "deterministic")
        self.assertTrue(
            any(action["action"] == "rag_prune" for action in embedded["plan"]["actions"])
        )

    def test_balanced_mode_minifies_json_and_markdown_segments(self):
        payload = (
            '{ "user_information": { "current_project_name": "HospiFlo" } }\n\n'
            "# Heading\n- Keep CASE-123"
        )

        result = compile_prompt(payload, mode="balanced")

        self.assertIn('"current_project_name":"HospiFlo"', result["optimized_text"])
        self.assertIn("Heading\nKeep CASE-123", result["optimized_text"])
        self.assertTrue(
            any(
                action["action"] in {"json_minify", "markdown_plaintext"}
                for action in result["plan"]["actions"]
            )
        )


if __name__ == "__main__":
    unittest.main()
