import unittest

from promptcompiler.cache import cache_key_for_compile


class CacheTests(unittest.TestCase):
    def test_cache_key_is_stable_for_same_compile_inputs(self):
        first = cache_key_for_compile("hello", {"mode": "balanced", "model": "gpt-4o-mini"})
        second = cache_key_for_compile("hello", {"model": "gpt-4o-mini", "mode": "balanced"})

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("pcache_"))


if __name__ == "__main__":
    unittest.main()
