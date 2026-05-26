import unittest

from promptcompiler.retrieval import select_retrieval_context


class RetrievalTests(unittest.TestCase):
    def test_selects_top_k_under_token_budget_and_dedupes(self):
        chunks = [
            {"id": "a", "source": "doc-a", "text": "refund approval over 500 manager", "tokens": 20},
            {"id": "b", "source": "doc-b", "text": "refund approval over 500 manager", "tokens": 20},
            {"id": "c", "source": "doc-c", "text": "shipping delay policy", "tokens": 20},
        ]

        result = select_retrieval_context(
            query="refund over 500",
            chunks=chunks,
            top_k=3,
            max_tokens=35,
            similarity_threshold=0.8,
        )

        ids = [item["id"] for item in result["chunks"]]
        self.assertEqual(ids, ["a"])
        self.assertEqual(result["tokens"], 20)
        self.assertIn("b", result["removed_chunk_ids"])


if __name__ == "__main__":
    unittest.main()
