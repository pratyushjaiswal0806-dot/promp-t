export const howItWorks = {
  hero: {
    eyebrow: "Pipeline",
    title: "How It Works",
    intro: "7 deterministic passes transform raw context into optimized prompts. Every transformation is auditable — no black boxes.",
  },
  pipeline: [
    { step: "01", title: "Parse", body: "Splits raw input into structured segments with roles, RAG chunks, tool output, and repeated blocks. Output: ContextGraph with typed segments.", signal: "Parse" },
    { step: "02", title: "Normalize", body: "Canonicalizes whitespace, trims segments, and normalizes line endings for consistent downstream processing.", signal: "Normalize" },
    { step: "03", title: "Dedup", body: "Identifies and removes duplicate or near-duplicate segments using content-addressed hashing.", signal: "Dedup" },
    { step: "04", title: "Entity Resolve", body: "Scans for pinned instructions, case IDs, URLs, names, and other protected entities. Tracks them for warning generation.", signal: "Entity" },
    { step: "05", title: "Summarize", body: "Semantic scoring removes low-value RAG chunks while preserving protected entities and critical context.", signal: "Summarize" },
    { step: "06", title: "Budget", body: "Applies token budget constraints: lossless (no reduction), balanced (moderate), aggressive (maximum).", signal: "Budget" },
    { step: "07", title: "Emit", body: "Serializes the optimized context graph back to text with trace metadata, diffs, and savings report.", signal: "Emit" },
  ],
  flowNodes: [
    { id: "parse", label: "Parse", type: "pass" },
    { id: "normalize", label: "Normalize", type: "pass" },
    { id: "dedup", label: "Dedup", type: "pass" },
    { id: "entity", label: "Entity Resolve", type: "pass" },
    { id: "summarize", label: "Summarize", type: "pass" },
    { id: "budget", label: "Budget", type: "pass" },
    { id: "emit", label: "Emit", type: "pass" },
  ],
  faq: [
    { title: "What does lossless mean?", body: "Lossless mode passes all segments through without removal. It only normalizes whitespace and structure. No tokens are dropped." },
    { title: "Are my prompts sent anywhere?", body: "No. Everything runs locally on your machine. The only opt-in remote path is NVIDIA NIM, which requires explicit confirmation before any data leaves." },
    { title: "Can I use it offline?", body: "Yes. The full pipeline runs locally with no internet dependency. NIM features require connectivity, but core compile/analyze/lint work fully offline." },
    { title: "How do I run it?", body: "Start the Python server, then open the workbench in your browser. See the Docs page for setup commands." },
    { title: "What models are supported?", body: "Any model string can be passed. The compiler uses the model name for token accounting and route metadata, not for inference." },
  ],
};
