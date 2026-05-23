import json
import os
import unittest
from unittest.mock import patch

from promptcompiler.server import handle_api_request


class ServerTests(unittest.TestCase):
    def test_health_reports_nim_status(self):
        with patch.dict(os.environ, {}, clear=True):
            status, body = handle_api_request("GET", "/api/health", b"")

        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertFalse(payload["nim_configured"])

    def test_analyze_endpoint_returns_segments(self):
        body = json.dumps({"input": "repeat\n\nrepeat"}).encode("utf-8")

        status, response = handle_api_request("POST", "/api/analyze", body)

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["segment_count"], 2)
        self.assertEqual(payload["duplicate_groups"][0]["count"], 2)

    def test_nim_summarize_without_key_returns_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            status, response = handle_api_request(
                "POST",
                "/api/nim/summarize",
                json.dumps({"text": "hello"}).encode("utf-8"),
            )

        payload = json.loads(response)
        self.assertEqual(status, 400)
        self.assertEqual(payload["code"], "NIM_API_KEY_MISSING")


if __name__ == "__main__":
    unittest.main()
