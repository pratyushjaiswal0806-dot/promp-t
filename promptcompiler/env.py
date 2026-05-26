"""Folder-local environment loading for PromptCompiler."""

from __future__ import annotations

import os
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT / ".env"
_VALID_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_local_env(path: str | Path = DEFAULT_ENV_FILE) -> dict[str, str]:
    """Load key=value pairs from a local .env file without overriding shell env."""

    if os.environ.get("PROMPTCOMPILER_DISABLE_DOTENV"):
        return {}

    env_path = Path(path)
    if not env_path.exists():
        return {}

    loaded: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(raw_line)
        if parsed is None:
            continue
        key, value = parsed
        if value == "":
            continue
        if key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded


def _parse_env_line(raw_line: str) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export ") :].strip()
    if "=" not in line:
        return None

    key, value = line.split("=", 1)
    key = key.strip()
    if not _VALID_KEY.match(key):
        return None

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return key, value
