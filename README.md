# PromptCompiler

PromptCompiler is a local-first workbench for LLM context analysis and safe deterministic prompt compilation. It works without paid API keys and can optionally use NVIDIA NIM APIs when `NVIDIA_API_KEY` is configured.

## Run

```bash
python3 -m promptcompiler.server
```

Open `http://127.0.0.1:8765`.

## Optional NVIDIA NIM

```bash
export NVIDIA_API_KEY="your_key"
python3 -m promptcompiler.server
```

The app uses `NVIDIA_API_KEY` to load available models from NVIDIA's OpenAI-compatible `/v1/models` endpoint. The default is a non-OSS NVIDIA model when available, and you can override it with `PROMPTCOMPILER_DEFAULT_MODEL`.

```bash
export PROMPTCOMPILER_DEFAULT_MODEL="nvidia/nemotron-3-nano-30b-a3b"
```

If you paste a key into a chat or public log, revoke it and create a new one.

## CLI

```bash
python3 -m promptcompiler.cli models
python3 -m promptcompiler.cli analyze prompt.json
python3 -m promptcompiler.cli compile prompt.json --out optimized.txt
```

## Current Features

- Local prompt analysis with token estimates, role/type breakdown, duplicate groups, and protected entities.
- Deterministic compile with pinned segment preservation, duplicate removal, repeated-line compaction, and segment-level diff.
- Large tool/log truncation that preserves lines containing protected entities.
- Optional NVIDIA NIM summarization with TLS certificate handling and protected-entity preservation warnings.
- Live NVIDIA model picker with local registry fallback.
- Built-in samples.
- Import local prompt files from the browser.
- Export optimized text or the full JSON compile report.

## Test

```bash
python3 -m unittest discover -s tests
```

## Documents

- [PRD](prd.md)
- [TRD](trd.md)
