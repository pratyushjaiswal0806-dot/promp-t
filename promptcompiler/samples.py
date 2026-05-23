"""Built-in prompt samples for the local workbench."""

from __future__ import annotations

import json


def list_samples() -> list[dict[str, str]]:
    return [
        {
            "id": "support-rma",
            "name": "Support RMA Chat",
            "input": json.dumps(
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": "@pin Follow policy CASE-123. Never remove this instruction.",
                        },
                        {
                            "role": "user",
                            "content": "The customer reported device failure on 2026-05-23.",
                        },
                        {
                            "role": "tool",
                            "content": (
                                "ERROR same failure\nERROR same failure\nERROR same failure\n"
                                "Shipping URL: https://example.com/rma/CASE-123"
                            ),
                        },
                        {
                            "role": "assistant",
                            "content": "I will check the RMA status.",
                        },
                        {
                            "role": "assistant",
                            "content": "I will check the RMA status.",
                        },
                    ]
                },
                indent=2,
            ),
        },
        {
            "id": "agent-logs",
            "name": "Agent Error Logs",
            "input": (
                "@pin Keep build target macOS and ticket BUILD-882.\n\n"
                "ERROR compile failed at step 4\n"
                "ERROR compile failed at step 4\n"
                "ERROR compile failed at step 4\n"
                "Retried with same flags on 2026-05-23.\n"
                "Retried with same flags on 2026-05-23."
            ),
        },
        {
            "id": "rag-overlap",
            "name": "RAG Overlap",
            "input": (
                "Source: doc-a\nThe refund policy allows returns within 30 days for CASE-345.\n\n"
                "Source: doc-b\nThe refund policy allows returns within 30 days for CASE-345.\n\n"
                "Source: doc-c\nRefunds over $500 require manager approval."
            ),
        },
    ]
