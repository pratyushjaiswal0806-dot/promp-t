"""PromptCompiler cache helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def cache_key_for_compile(raw_input: str, policy: dict[str, Any]) -> str:
    payload = {
        "raw_input": raw_input,
        "policy": policy,
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "pcache_" + hashlib.sha256(encoded).hexdigest()
