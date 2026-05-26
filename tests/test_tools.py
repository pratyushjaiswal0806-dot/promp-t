import unittest

from promptcompiler.tools import compact_tool_schema, select_tools_for_query


class ToolTests(unittest.TestCase):
    def test_compact_tool_schema_removes_verbose_fields(self):
        tool = {
            "name": "lookup_refund_policy",
            "description": "Use this tool to look up the refund policy. " * 8,
            "examples": ["example " * 20],
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "Ticket id such as CASE-123."},
                },
            },
        }

        compacted = compact_tool_schema(tool)

        self.assertIn("name", compacted)
        self.assertIn("parameters", compacted)
        self.assertNotIn("examples", compacted)
        self.assertLess(len(str(compacted)), len(str(tool)))

    def test_select_tools_for_query_keeps_relevant_names(self):
        tools = [
            {"name": "lookup_refund_policy", "description": "refund manager approval"},
            {"name": "book_flight", "description": "travel booking"},
        ]

        selected = select_tools_for_query("Can we approve this refund?", tools, max_tools=1)

        self.assertEqual(selected[0]["name"], "lookup_refund_policy")


if __name__ == "__main__":
    unittest.main()
