import unittest

from promptcompiler.routing import choose_model_route


class RoutingTests(unittest.TestCase):
    def test_routes_simple_formatting_to_small_model(self):
        route = choose_model_route({"task_type": "formatting", "total_tokens": 200})

        self.assertEqual(route["tier"], "small")
        self.assertEqual(route["reason"], "simple_task")

    def test_routes_large_complex_prompt_to_primary_model(self):
        route = choose_model_route({"task_type": "analysis", "total_tokens": 12000})

        self.assertEqual(route["tier"], "primary")
        self.assertEqual(route["reason"], "complex_or_large_task")


if __name__ == "__main__":
    unittest.main()
