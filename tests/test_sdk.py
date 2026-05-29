import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import os

import promptcompiler
from promptcompiler.sdk import PromptCompilerClient
from promptcompiler.fastapi_server import PromptCompilerHandler


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return {"model": kwargs["model"], "messages": kwargs["messages"]}


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeOpenAIClient:
    def __init__(self):
        self.chat = FakeChat()


class SDKTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "PROMPTCOMPILER_DB_PATH": str(Path(self.tmp.name) / "sdk.sqlite3"),
                "PROMPTCOMPILER_DISABLE_DOTENV": "1",
            },
            clear=False,
        )
        self.env.start()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), PromptCompilerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.env.stop()
        self.tmp.cleanup()

    def test_client_analyze_and_compile(self):
        client = PromptCompilerClient(self.base_url)
        messages = [{"role": "user", "content": "repeat\n\nrepeat"}]

        analysis = client.analyze(messages=messages, model="gpt-4o-mini")
        compiled = client.compile(messages=messages, model="gpt-4o-mini", mode="balanced")

        self.assertTrue(analysis["trace_id"].startswith("tr_"))
        self.assertGreater(analysis["total_tokens"], 0)
        self.assertTrue(compiled["trace_id"].startswith("tr_"))
        self.assertLess(compiled["optimized_token_count"], compiled["original_token_count"])

    def test_wrap_compiles_messages_before_calling_openai_like_client(self):
        fake = FakeOpenAIClient()
        wrapped = promptcompiler.wrap(fake, base_url=self.base_url, mode="balanced")

        response = wrapped.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "repeat"},
                {"role": "assistant", "content": "repeat"},
            ],
            promptcompiler={"mode": "balanced", "session_id": "sess_sdk"},
        )

        self.assertEqual(response["model"], "gpt-4o-mini")
        self.assertEqual(len(fake.chat.completions.calls), 1)
        forwarded = fake.chat.completions.calls[0]
        self.assertNotIn("promptcompiler", forwarded)
        self.assertTrue(forwarded["messages"])
        self.assertTrue(hasattr(response, "promptcompiler"))
        self.assertTrue(response.promptcompiler["trace_id"].startswith("tr_"))

    def test_wrap_forwards_policy_options_to_promptcompiler(self):
        fake = FakeOpenAIClient()
        wrapped = promptcompiler.wrap(fake, base_url=self.base_url, mode="balanced")

        response = wrapped.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Give short JSON for CASE-123."}],
            promptcompiler={
                "context_policy": {"system_prompt_ref": "json_only"},
                "output_policy": {"max_words": 20, "format": "json", "explain": False},
            },
        )

        forwarded = fake.chat.completions.calls[0]
        self.assertIn("Return JSON only", forwarded["messages"][0]["content"])
        self.assertEqual(response.promptcompiler["output_policy"]["max_words"], 20)

    def test_wrap_forwards_semantic_policy_to_promptcompiler(self):
        fake = FakeOpenAIClient()
        wrapped = promptcompiler.wrap(fake, base_url=self.base_url, mode="balanced")

        response = wrapped.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "Do refunds over 500 need manager approval?",
                }
            ],
            promptcompiler={
                "semantic_policy": {"scorer": "embedding", "provider": "deterministic"},
                "rag_chunks": [
                    {
                        "id": "policy-a",
                        "source": "policy-a",
                        "text": "Refunds over 500 require manager approval.",
                    },
                    {
                        "id": "policy-b",
                        "source": "policy-b",
                        "text": "Reimbursements greater than 500 dollars need supervisor review.",
                    },
                ],
            },
        )

        self.assertEqual(response.promptcompiler["semantic_policy"]["scorer"], "embedding")
        self.assertGreater(response.promptcompiler["token_reduction_percent"], 0)


if __name__ == "__main__":
    unittest.main()
