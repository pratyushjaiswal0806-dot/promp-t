import unittest

from promptcompiler.policies import normalize_context_policy, normalize_output_policy
from promptcompiler.prompt_registry import expand_system_prompt_ref, list_system_prompts


class PolicyTests(unittest.TestCase):
    def test_output_policy_normalizes_compact_defaults(self):
        policy = normalize_output_policy({"max_words": "80", "format": "json", "explain": False})

        self.assertEqual(policy["max_words"], 80)
        self.assertEqual(policy["format"], "json")
        self.assertEqual(
            policy["instruction"],
            "Answer in <=80 words. Return JSON only. No explanation unless asked.",
        )

    def test_context_policy_accepts_system_prompt_ref(self):
        policy = normalize_context_policy({"system_prompt_ref": "json_only", "cache_static_prefix": True})

        self.assertEqual(policy["system_prompt_ref"], "json_only")
        self.assertTrue(policy["cache_static_prefix"])


class PromptRegistryTests(unittest.TestCase):
    def test_builtin_prompt_ref_expands_to_short_instruction(self):
        expanded = expand_system_prompt_ref("json_only")

        self.assertEqual(expanded["id"], "json_only")
        self.assertIn("Return JSON only", expanded["content"])
        self.assertLess(len(expanded["content"].split()), 10)

    def test_registry_lists_builtin_prompt_ids(self):
        prompts = list_system_prompts()

        self.assertTrue(any(item["id"] == "concise" for item in prompts))
        self.assertTrue(any(item["id"] == "json_only" for item in prompts))


if __name__ == "__main__":
    unittest.main()
