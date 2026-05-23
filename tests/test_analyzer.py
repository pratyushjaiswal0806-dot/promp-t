import unittest

from promptcompiler.analyzer import analyze_prompt


class AnalyzerTests(unittest.TestCase):
    def test_analyze_openai_messages_breaks_down_roles_and_pins(self):
        payload = (
            '{"messages":['
            '{"role":"system","content":"@pin Follow policy CASE-123."},'
            '{"role":"user","content":"Hello Hello"}'
            "]}"
        )

        result = analyze_prompt(payload)

        self.assertEqual(result["segment_count"], 2)
        self.assertGreater(result["by_role"]["system"], 0)
        self.assertGreater(result["by_role"]["user"], 0)
        self.assertTrue(result["segments"][0]["pinned"])
        self.assertIn("CASE-123", result["protected_entities"])

    def test_analyze_detects_duplicate_plain_text_paragraphs(self):
        result = analyze_prompt("repeat me\n\nrepeat me\n\nunique")

        self.assertEqual(result["segment_count"], 3)
        self.assertEqual(result["duplicate_groups"][0]["count"], 2)


if __name__ == "__main__":
    unittest.main()
