import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from promptcompiler.embeddings import cache_key_for_embedding, embed_texts


class EmbeddingTests(unittest.TestCase):
    def test_cache_key_changes_when_model_or_dimensions_change(self):
        text = "Refunds over 500 require manager approval."

        base = cache_key_for_embedding(
            text,
            {
                "scorer": "embedding",
                "provider": "deterministic",
                "model": "local-deterministic-v1",
                "dimensions": 64,
            },
        )
        different_model = cache_key_for_embedding(
            text,
            {
                "scorer": "embedding",
                "provider": "deterministic",
                "model": "local-deterministic-v2",
                "dimensions": 64,
            },
        )
        different_dimensions = cache_key_for_embedding(
            text,
            {
                "scorer": "embedding",
                "provider": "deterministic",
                "model": "local-deterministic-v1",
                "dimensions": 32,
            },
        )

        self.assertTrue(base.startswith("embcache_"))
        self.assertNotEqual(base, different_model)
        self.assertNotEqual(base, different_dimensions)

    def test_embed_texts_reuses_sqlite_cache_for_repeated_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = patch.dict(
                os.environ,
                {
                    "PROMPTCOMPILER_DB_PATH": str(Path(tmp) / "embeddings.sqlite3"),
                    "PROMPTCOMPILER_DISABLE_DOTENV": "1",
                },
                clear=False,
            )
            with env, patch("promptcompiler.embeddings._vector_for_text") as vector_for_text:
                vector_for_text.return_value = [1.0, 0.0, 0.0]
                first = embed_texts(
                    ["Refunds over 500 require manager approval."],
                    {"scorer": "embedding", "provider": "deterministic", "dimensions": 3},
                )
                second = embed_texts(
                    ["Refunds over 500 require manager approval."],
                    {"scorer": "embedding", "provider": "deterministic", "dimensions": 3},
                )

        self.assertEqual(first, second)
        self.assertEqual(vector_for_text.call_count, 1)


if __name__ == "__main__":
    unittest.main()
