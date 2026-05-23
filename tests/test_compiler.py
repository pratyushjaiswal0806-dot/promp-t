import unittest

from promptcompiler.compiler import compile_prompt


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


if __name__ == "__main__":
    unittest.main()
