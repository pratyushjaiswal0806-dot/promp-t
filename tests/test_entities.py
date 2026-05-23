import unittest

from promptcompiler.entities import extract_entities


class EntityTests(unittest.TestCase):
    def test_extract_entities_finds_values_that_should_survive_compile(self):
        text = "Visit https://example.com on 2026-05-23 for CASE-123, $49.99, and 95%."

        entities = extract_entities(text)

        self.assertIn("https://example.com", entities)
        self.assertIn("2026-05-23", entities)
        self.assertIn("CASE-123", entities)
        self.assertIn("$49.99", entities)
        self.assertIn("95%", entities)


if __name__ == "__main__":
    unittest.main()
