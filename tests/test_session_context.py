import unittest

from promptcompiler.session_context import build_compact_session_context


class SessionContextTests(unittest.TestCase):
    def test_keeps_pinned_recent_and_summary_within_budget(self):
        turns = [
            {
                "id": "1",
                "role": "system",
                "content": "@pin Keep CASE-123.",
                "token_count": 8,
                "pinned": 1,
                "is_summary": 0,
            },
            {
                "id": "2",
                "role": "user",
                "content": "old detail " * 20,
                "token_count": 40,
                "pinned": 0,
                "is_summary": 0,
            },
            {
                "id": "3",
                "role": "assistant",
                "content": "older reply " * 20,
                "token_count": 40,
                "pinned": 0,
                "is_summary": 0,
            },
            {
                "id": "4",
                "role": "system",
                "content": "[session summary] user wants compact prompts",
                "token_count": 10,
                "pinned": 0,
                "is_summary": 1,
            },
            {
                "id": "5",
                "role": "user",
                "content": "current question",
                "token_count": 6,
                "pinned": 0,
                "is_summary": 0,
            },
        ]

        context = build_compact_session_context(
            turns,
            target_token_budget=55,
            sliding_window_turns=1,
        )

        text = "\n".join(item["content"] for item in context["messages"])
        self.assertIn("CASE-123", text)
        self.assertIn("[session summary]", text)
        self.assertIn("current question", text)
        self.assertLessEqual(context["token_count"], 55)
        self.assertEqual(context["strategy"], "pinned_summary_recent")


if __name__ == "__main__":
    unittest.main()
