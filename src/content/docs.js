export const docs = {
  hero: {
    eyebrow: "Operator Notes",
    title: "Docs",
    intro: "Installation, quick-start, CLI reference, API reference, and configuration — everything you need to run and integrate PromptCompiler.",
  },
  sections: [
    { title: "Installation", body: "Clone the repo and install dependencies. Requires Python 3.11+ and Node.js 18+.", commands: ["git clone https://github.com/your-org/promptcompiler", "cd promptcompiler", "pip install -r requirements.txt", "npm install"] },
    { title: "Quick Start", body: "Start the Python server, then open the workbench in your browser.", commands: ["python3 -m promptcompiler.server", "npm run dev", "# open http://127.0.0.1:5173"] },
    { title: "CLI Reference", body: "Use the CLI for scripted compilation without the workbench UI.", commands: ["promptcompiler compile --input prompt.txt --mode balanced", "promptcompiler analyze --input prompt.txt", "promptcompiler lint --input prompt.txt", "promptcompiler serve --port 8765"] },
    { title: "Compile API", body: "Post raw input, model, mode, and optional semantic policy to /v1/compile.", commands: ["curl -X POST http://127.0.0.1:8765/v1/compile -H 'Content-Type: application/json' -d '{\"input\":\"...\",\"mode\":\"balanced\"}'"] },
    { title: "Python SDK", body: "Use PromptCompilerClient when an agent or script needs analyze and compile calls.", commands: ["from promptcompiler import PromptCompilerClient", "client = PromptCompilerClient()", "result = client.compile('your prompt here', mode='balanced')"] },
    { title: "Proxy Route", body: "Send chat-completion shaped requests through the local proxy.", commands: ["curl -X POST http://127.0.0.1:8765/v1/proxy/openai/chat/completions -H 'Content-Type: application/json' -d '{\"model\":\"gpt-4\",\"messages\":[...]}'", "# Response includes X-PromptCompiler-Trace header"] },
    { title: "Configuration", body: "Configure via environment variables or JSON config file.", commands: ["PROMPTCOMPILER_HOST=0.0.0.0", "PROMPTCOMPILER_PORT=8765", "PROMPTCOMPILER_DB_PATH=./data/store.db", "# Or use config.json: { \"host\": \"0.0.0.0\", \"port\": 8765 }"] },
    { title: "Changelog", body: "Recent changes and version history.", commands: ["v0.2.0 — Pass pipeline, modular frontend, FastAPI server", "v0.1.0 — Initial release: analyze, compile, lint"] },
  ],
};
