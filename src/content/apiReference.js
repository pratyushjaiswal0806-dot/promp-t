export const apiReference = {
  hero: {
    eyebrow: "HTTP Surface",
    title: "API Reference",
    intro: "A practical guide to the local analyze, compile, retrieve, lint, session, metrics, and proxy endpoints.",
  },
  endpoints: [
    {
      method: "POST", path: "/v1/analyze", description: "Analyze prompt structure without modifying it.",
      requestSchema: '{\n  "input": "string (required)",\n  "model": "string (optional)"\n}',
      responseSchema: '{\n  "total_tokens": "number",\n  "segment_count": "number",\n  "compression_opportunity": "number",\n  "segments": "Segment[]",\n  "protected_entities": "Entity[]"\n}',
      example: 'curl -X POST http://127.0.0.1:8765/v1/analyze -H \'Content-Type: application/json\' -d \'{"input":"Hello world"}\'',
      statusCodes: [{ code: 200, description: "Analysis complete" }, { code: 400, description: "Invalid input" }, { code: 422, description: "Validation error" }],
    },
    {
      method: "POST", path: "/v1/compile", description: "Compile a prompt with policy controls.",
      requestSchema: '{\n  "input": "string (required)",\n  "model": "string",\n  "mode": "lossless | balanced | aggressive",\n  "target_token_budget": "number | null",\n  "dry_run": "boolean"\n}',
      responseSchema: '{\n  "optimized_prompt": "string",\n  "original_token_count": "number",\n  "optimized_token_count": "number",\n  "token_reduction_percent": "number",\n  "diff": "DiffItem[]",\n  "warnings": "string[]"\n}',
      example: 'curl -X POST http://127.0.0.1:8765/v1/compile -H \'Content-Type: application/json\' -d \'{"input":"...","mode":"balanced"}\'',
      statusCodes: [{ code: 200, description: "Compilation complete" }, { code: 400, description: "Invalid input" }, { code: 422, description: "Validation error" }],
    },
    {
      method: "POST", path: "/v1/retrieve", description: "Score and rank retrieval chunks.",
      requestSchema: '{\n  "input": "string (required)",\n  "top_k": "number"\n}',
      responseSchema: '{\n  "chunks": "ScoredChunk[]",\n  "total_chunks": "number"\n}',
      example: 'curl -X POST http://127.0.0.1:8765/v1/retrieve -H \'Content-Type: application/json\' -d \'{"input":"...","top_k":5}\'',
      statusCodes: [{ code: 200, description: "Retrieval scored" }],
    },
    {
      method: "POST", path: "/v1/lint", description: "Flag prompt quality issues.",
      requestSchema: '{\n  "input": "string (required)"\n}',
      responseSchema: '{\n  "findings": "LintFinding[]"\n}',
      example: 'curl -X POST http://127.0.0.1:8765/v1/lint -H \'Content-Type: application/json\' -d \'{"input":"..."}\'',
      statusCodes: [{ code: 200, description: "Lint complete" }],
    },
    {
      method: "POST", path: "/v1/proxy/openai/chat/completions", description: "OpenAI-compatible proxy with prompt compilation.",
      requestSchema: '{\n  "model": "string",\n  "messages": "Message[]",\n  "temperature": "number (optional)"\n}',
      responseSchema: '{\n  "id": "string",\n  "choices": "Choice[]",\n  "usage": "Usage"\n}\nHeader: X-PromptCompiler-Trace',
      example: 'curl -X POST http://127.0.0.1:8765/v1/proxy/openai/chat/completions -H \'Content-Type: application/json\' -d \'{"model":"gpt-4","messages":[{"role":"user","content":"Hello"}]}\'',
      statusCodes: [{ code: 200, description: "Completion returned" }, { code: 502, description: "Upstream failure" }],
    },
    {
      method: "GET", path: "/v1/sessions/{id}", description: "Retrieve session context.",
      requestSchema: 'Path parameter: id (string)',
      responseSchema: '{\n  "session_id": "string",\n  "context": "string",\n  "turns": "number"\n}',
      example: 'curl http://127.0.0.1:8765/v1/sessions/session_123',
      statusCodes: [{ code: 200, description: "Session found" }, { code: 404, description: "Session not found" }],
    },
  ],
};
