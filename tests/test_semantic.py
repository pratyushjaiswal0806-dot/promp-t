import unittest

from promptcompiler.parser import parse_prompt
from promptcompiler.semantic import build_semantic_report, chunk_segment, score_chunks


class SemanticTests(unittest.TestCase):
    def test_chunk_segment_uses_windows_overlap_and_source_metadata(self):
        segment = parse_prompt(
            "Source: doc-a\n"
            "Alpha refund policy sentence. "
            "Beta manager approval sentence. "
            "Gamma shipping sentence. "
            "Delta warranty sentence. "
            "Epsilon escalation sentence."
        )[0]

        chunks = chunk_segment(segment, window_tokens=12, overlap_tokens=3)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk["source"] == "doc-a" for chunk in chunks))
        self.assertTrue(chunks[0]["id"].endswith("_1_chunk_1"))
        self.assertEqual(chunks[1]["overlap_tokens"], 3)
        self.assertLessEqual(chunks[0]["tokens"], 18)

    def test_score_chunks_rewards_query_relevance_and_penalizes_duplicates(self):
        chunks = [
            {
                "id": "a",
                "text": "Refunds over $500 require manager approval.",
                "entities": ["$500"],
                "pinned": False,
            },
            {
                "id": "b",
                "text": "Shipping labels can be reprinted by support.",
                "entities": [],
                "pinned": False,
            },
            {
                "id": "c",
                "text": "Refunds over $500 require manager approval.",
                "entities": ["$500"],
                "pinned": False,
            },
        ]

        scored = {item["id"]: item for item in score_chunks(chunks, "refund manager approval")}

        self.assertGreater(scored["a"]["query_relevance_score"], scored["b"]["query_relevance_score"])
        self.assertGreater(scored["a"]["inter_chunk_similarity_score"], 0.8)
        self.assertLess(scored["c"]["novelty_score"], scored["b"]["novelty_score"])

    def test_embedding_scorer_scores_paraphrases_as_similar(self):
        chunks = [
            {
                "id": "a",
                "text": "Refunds over 500 require manager approval.",
                "entities": [],
                "pinned": False,
            },
            {
                "id": "b",
                "text": "Reimbursements greater than 500 dollars need supervisor review.",
                "entities": [],
                "pinned": False,
            },
        ]

        lexical = {item["id"]: item for item in score_chunks(chunks, "refund manager approval")}
        embedded = {
            item["id"]: item
            for item in score_chunks(
                chunks,
                "refund manager approval",
                semantic_policy={"scorer": "embedding", "provider": "deterministic"},
            )
        }

        self.assertLess(lexical["a"]["inter_chunk_similarity_score"], 0.78)
        self.assertGreater(embedded["a"]["inter_chunk_similarity_score"], 0.78)
        self.assertEqual(embedded["a"]["scorer"], "embedding")

    def test_embedding_semantic_report_keeps_pinned_paraphrase(self):
        segments = parse_prompt(
            "Question: Do refunds over 500 need manager approval?\n\n"
            "Source: doc-a\nRefunds over 500 require manager approval.\n\n"
            "@pin Source: doc-b\nReimbursements greater than 500 dollars need supervisor review."
        )

        report = build_semantic_report(
            segments,
            query="refund manager approval",
            mode="balanced",
            semantic_policy={"scorer": "embedding", "provider": "deterministic"},
        )

        self.assertFalse(report["removed_chunk_ids"])
        self.assertEqual(report["scorer"], "embedding")


if __name__ == "__main__":
    unittest.main()
