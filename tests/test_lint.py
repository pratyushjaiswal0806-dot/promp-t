import unittest

from promptcompiler.lint import lint_token_waste


class LintTests(unittest.TestCase):
    def test_detects_multi_task_prompt(self):
        findings = lint_token_waste("Analyze this code, explain it, optimize it, write tests, generate docs")

        self.assertTrue(any(item["code"] == "MULTI_TASK_REQUEST" for item in findings))

    def test_detects_agent_reflection_loops(self):
        findings = lint_token_waste("Thought: check\nReflection: maybe retry\nSelf critique: retry again")

        self.assertTrue(any(item["code"] == "AGENT_REFLECTION_OVERHEAD" for item in findings))

    def test_detects_large_system_prompt(self):
        findings = lint_token_waste("You are the world's best AI assistant. " * 200)

        self.assertTrue(any(item["code"] == "HUGE_SYSTEM_PROMPT" for item in findings))


if __name__ == "__main__":
    unittest.main()
