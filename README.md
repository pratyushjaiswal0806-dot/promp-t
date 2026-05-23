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

The default model is `openai/gpt-oss-20b`. You can change the model in the workbench.

## Test

```bash
python3 -m unittest discover -s tests
```

## Documents

- [PRD](prd.md)
- [TRD](trd.md)
