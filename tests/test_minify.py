import unittest

from promptcompiler.minify import compact_json_text, compact_markdown_text, structured_input_to_text


class MinifyTests(unittest.TestCase):
    def test_compact_json_text_minifies_and_aliases_keys(self):
        raw = '{ "user_information": { "current_project_name": "HospiFlo" } }'

        compacted = compact_json_text(
            raw,
            aliases={"user_information": "user", "current_project_name": "project"},
        )

        self.assertEqual(compacted, '{"user":{"project":"HospiFlo"}}')

    def test_compact_markdown_text_removes_internal_heading_markup(self):
        raw = "# Heading\n## Subheading\n- One\n- Two"

        compacted = compact_markdown_text(raw)

        self.assertEqual(compacted, "Heading\nSubheading\nOne\nTwo")

    def test_structured_input_to_text_uses_minified_json(self):
        text = structured_input_to_text({"age_gt": 20, "product": "shoes", "month": "last"})

        self.assertEqual(text, '{"age_gt":20,"month":"last","product":"shoes"}')


if __name__ == "__main__":
    unittest.main()
