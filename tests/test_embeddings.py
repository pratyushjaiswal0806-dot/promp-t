import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from promptcompiler import embeddings as emb_module
from promptcompiler.embeddings import cache_key_for_embedding, embed_texts, FingerprintStore


class EmbeddingTests(unittest.TestCase):
    def test_cache_key_changes_when_model_or_dimensions_change(self):
        text = "Refunds over 500 require manager approval."

        base = cache_key_for_embedding(
            text,
            {"scorer": "embedding", "provider": "deterministic",
             "model": "local-deterministic-v1", "dimensions": 64},
        )
        different_model = cache_key_for_embedding(
            text,
            {"scorer": "embedding", "provider": "deterministic",
             "model": "local-deterministic-v2", "dimensions": 64},
        )
        different_dimensions = cache_key_for_embedding(
            text,
            {"scorer": "embedding", "provider": "deterministic",
             "model": "local-deterministic-v1", "dimensions": 32},
        )

        self.assertTrue(base.startswith("fp_"))
        self.assertNotEqual(base, different_model)
        self.assertNotEqual(base, different_dimensions)

    def test_embed_texts_reuses_sqlite_cache_for_repeated_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "fingerprints.sqlite3")
            env = patch.dict(
                os.environ,
                {
                    "PROMPTCOMPILER_DB_PATH": db_path,
                    "PROMPTCOMPILER_DISABLE_DOTENV": "1",
                },
                clear=False,
            )
            with env, patch("promptcompiler.embeddings._simhash_weights") as simhash:
                simhash.return_value = (0x0123456789ABCDEF, [3, -1, 2, 1, -2, 0, 4, -3] * 8)
                first = embed_texts(
                    ["Refunds over 500 require manager approval."],
                    {"scorer": "embedding", "provider": "deterministic", "dimensions": 3},
                )
                second = embed_texts(
                    ["Refunds over 500 require manager approval."],
                    {"scorer": "embedding", "provider": "deterministic", "dimensions": 3},
                )

        self.assertEqual(first, second)
        self.assertEqual(simhash.call_count, 1)

    def test_fingerprint_store_get_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FingerprintStore(db_path=Path(tmp) / "test.sqlite3")
            store.set("my_key", 0x1234, [1, -1, 1, 1, -1])
            fp, weights = store.get("my_key")
            self.assertEqual(fp, 0x1234)
            self.assertEqual(weights, [1, -1, 1, 1, -1])
            self.assertIsNone(store.get("nonexistent"))


if __name__ == "__main__":
    unittest.main()
