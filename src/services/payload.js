export const WORKFLOW_PRESETS = [
  {
    id: "reusable-context",
    label: "Reusable Context",
    mode: "context_file",
    patch: {
      targetTokenBudget: "",
      reuseExpectedCalls: "100",
      includeDecodePrompt: true,
      validationMode: "strict",
      cacheStaticPrefix: true,
      cacheEnabled: true,
      zeroRetention: true,
    },
  },
  {
    id: "long-chat-history",
    label: "Long Chat History",
    mode: "balanced",
    patch: {
      targetTokenBudget: "1200",
      dryRun: false,
      zeroRetention: true,
      outputFormat: "plain",
      maxWords: "",
      retrievalTopK: "",
      toolCompact: false,
      deterministicSemantic: false,
    },
  },
  {
    id: "rag-overlap",
    label: "RAG Overlap",
    mode: "balanced",
    patch: {
      targetTokenBudget: "",
      retrievalTopK: "3",
      autoSemantic: true,
      deterministicSemantic: true,
      cacheEnabled: true,
    },
  },
  {
    id: "tool-logs",
    label: "Tool Logs",
    mode: "aggressive",
    patch: {
      targetTokenBudget: "900",
      toolCompact: true,
      maxTools: "3",
      dryRun: false,
      deterministicSemantic: false,
    },
  },
  {
    id: "json-schema-bloat",
    label: "JSON / Schema Bloat",
    mode: "lossless",
    patch: {
      outputFormat: "json",
      explain: false,
      targetTokenBudget: "",
      toolCompact: false,
    },
  },
  {
    id: "support-ticket-context",
    label: "Support Ticket Context",
    mode: "balanced",
    patch: {
      targetTokenBudget: "700",
      systemPromptRef: "concise",
      outputFormat: "bullets",
      maxWords: "160",
      zeroRetention: true,
      deterministicSemantic: true,
    },
  },
  {
    id: "prompt-generation-cleanup",
    label: "Prompt Generation Cleanup",
    mode: "balanced",
    patch: {
      outputFormat: "plain",
      maxWords: "",
      explain: true,
      dryRun: false,
      cacheEnabled: false,
    },
  },
];

export function createDefaultControls() {
  return {
    targetTokenBudget: "",
    dryRun: false,
    zeroRetention: true,
    cacheStaticPrefix: false,
    cacheEnabled: false,
    outputFormat: "plain",
    maxWords: "",
    explain: true,
    systemPromptRef: "",
    reuseExpectedCalls: "10",
    includeDecodePrompt: true,
    validationMode: "strict",
    retrievalTopK: "",
    toolCompact: false,
    maxTools: "",
    deterministicSemantic: false,
    autoSemantic: true,
    sessionId: "",
  };
}

export function controlsFromPreset(presetId, currentControls = createDefaultControls()) {
  const preset = WORKFLOW_PRESETS.find((item) => item.id === presetId);
  if (!preset) return { ...currentControls };
  return {
    ...currentControls,
    ...preset.patch,
    mode: preset.mode,
  };
}

export function buildCompilePayload({ inputValue, selectedModel, mode, controls }) {
  const current = { ...createDefaultControls(), ...(controls || {}) };
  const targetBudget = positiveIntOrNull(current.targetTokenBudget);
  const retrievalTopK = positiveIntOrNull(current.retrievalTopK);
  const maxWords = positiveIntOrNull(current.maxWords);
  const maxTools = positiveIntOrNull(current.maxTools);
  const systemPromptRef = optionalString(current.systemPromptRef);
  const sessionId = optionalString(current.sessionId);
  const reuseExpectedCalls = positiveIntOrNull(current.reuseExpectedCalls) || 1;
  const validationMode = optionalString(current.validationMode) || "strict";

  const payload = {
    input: inputValue,
    model: selectedModel,
    mode,
    target_token_budget: targetBudget,
    dry_run: Boolean(current.dryRun),
    zero_retention: Boolean(current.zeroRetention),
    context_policy: {
      cache_static_prefix: Boolean(current.cacheStaticPrefix),
      retrieval_top_k: retrievalTopK,
      system_prompt_ref: systemPromptRef,
      reuse_expected_calls: reuseExpectedCalls,
      include_decode_prompt: Boolean(current.includeDecodePrompt),
      validation: validationMode,
    },
    output_policy: {
      explain: Boolean(current.explain),
      format: current.outputFormat || "plain",
      max_words: maxWords,
    },
    tool_policy: {
      compact: Boolean(current.toolCompact),
      max_tools: maxTools,
    },
    cache_policy: {
      enabled: Boolean(current.cacheEnabled),
    },
    semantic_policy: semanticPolicyForInput(inputValue, mode, current),
  };

  if (sessionId) payload.session_id = sessionId;
  return payload;
}

function positiveIntOrNull(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number.parseInt(String(value), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function optionalString(value) {
  const text = String(value ?? "").trim();
  return text || null;
}

function semanticPolicyForInput(inputValue, mode, controls) {
  if (controls.deterministicSemantic) {
    return { provider: "deterministic", scorer: "embedding", reason: "explicit_user_enabled" };
  }
  if (controls.autoSemantic && supportsSemanticCompression(inputValue, mode)) {
    return { provider: "deterministic", scorer: "embedding", reason: "auto_rag_source_detected" };
  }
  return { provider: "deterministic", scorer: "lexical" };
}

function supportsSemanticCompression(inputValue, mode) {
  if (!["balanced", "aggressive"].includes(mode)) return false;
  return /(^|\n)\s*(source|citation|cite)\s*:/i.test(String(inputValue || ""));
}
