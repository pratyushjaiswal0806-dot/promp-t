export function deriveUsabilityVerdict(result = {}) {
  const compile = result.compile || result || {};
  const preservation = result.preservation || compile.preservation || {};
  const missingEntities = preservation.missing_entities || preservation.missingEntities || [];
  const warnings = compile.warnings || result.warnings || [];
  const riskLevel = String(compile.plan?.risk_level || riskLabel(compile.risk_score ?? result.risk_score)).toLowerCase();
  const dryRun = Boolean(result.dry_run || compile.dry_run);

  if (missingEntities.length || preservation.ok === false) {
    return {
      label: "Do not use",
      status: "blocked",
      reason: missingEntities.length
        ? `Missing protected values: ${missingEntities.join(", ")}.`
        : "Protected value preservation failed.",
    };
  }

  if (dryRun) {
    return {
      label: "Preview only",
      status: "preview",
      reason: "Dry run keeps the active output unchanged. Review the proposed prompt before exporting.",
    };
  }

  if (riskLevel === "high" || Number(compile.risk_score ?? result.risk_score ?? 0) >= 0.6) {
    return {
      label: "Review first",
      status: "review",
      reason: warnings[0] ? `High risk: ${warnings[0]}` : "High-risk optimization needs human review before use.",
    };
  }

  if (warnings.length) {
    return {
      label: "Review first",
      status: "review",
      reason: warnings[0],
    };
  }

  return {
    label: "Ready to use",
    status: "ready",
    reason: "Protected values survived and no warnings were reported.",
  };
}

export function proposedPromptForDryRun(result = {}) {
  const compile = result.compile || result || {};
  if (!(result.dry_run || compile.dry_run)) return "";
  const proposed = result.proposed_optimized_prompt || compile.proposed_optimized_text || "";
  const active = result.optimized_prompt || compile.optimized_text || "";
  return proposed && proposed !== active ? proposed : "";
}

export function optimizationInsight(result = {}) {
  const compile = result.compile || result || {};
  const original = Number(result.original_token_count ?? compile.original_tokens ?? 0);
  const optimized = Number(result.optimized_token_count ?? compile.optimized_tokens ?? 0);
  const tokensSaved = Number(compile.tokens_saved ?? Math.max(0, original - optimized));
  const semantic = result.semantic || compile.semantic || {};
  const semanticSummary = semantic.summary || {};
  const removedChunks = Number(semanticSummary.removed_chunks ?? semantic.removed_chunk_ids?.length ?? 0);
  const ragChunks = Number(semanticSummary.rag_chunks ?? 0);
  const scorer = semantic.scorer || "lexical";

  if (removedChunks > 0) {
    return {
      status: "semantic",
      title: "Semantic compression applied",
      body: `${scorer} scoring removed ${removedChunks} redundant RAG chunk${removedChunks === 1 ? "" : "s"} while preserving protected values.`,
    };
  }

  if (tokensSaved <= 0) {
    if (ragChunks > 0 && scorer !== "embedding") {
      return {
        status: "unchanged",
        title: "No safe compression found",
        body: "The compiler found RAG/source context, but lexical scoring did not identify a redundant chunk. Enable semantic scoring for paraphrase-aware pruning.",
      };
    }
    return {
      status: "unchanged",
      title: "No safe compression found",
      body: "This prompt did not contain duplicate blocks, budget pressure, compactable tool/log output, or redundant RAG chunks, so the safe output matches the input.",
    };
  }

  return null;
}

export function buildTrustProfile({ inputValue = "", mode = "balanced", result = {} } = {}) {
  const compile = result.compile || result || {};
  const accounting = result.token_accounting || compile.token_accounting || {};
  const semantic = result.semantic || compile.semantic || {};
  const warnings = compile.warnings || result.warnings || [];
  const changes = compile.changes || result.changes || [];
  const original = Number(result.original_token_count ?? compile.original_tokens ?? 0);
  const optimized = Number(result.optimized_token_count ?? compile.optimized_tokens ?? 0);
  const tokensSaved = Number(compile.tokens_saved ?? Math.max(0, original - optimized));
  const removedChunks = Number(semantic.summary?.removed_chunks ?? semantic.removed_chunk_ids?.length ?? 0);
  const promptType = classifyPromptType(inputValue, compile);
  const safeCompressionPotential = compressionPotential({
    promptType,
    tokensSaved,
    removedChunks,
    text: inputValue,
    changes,
  });
  const bestOptimization = promptType === "Creative build prompt" && safeCompressionPotential === "low"
    ? "Distill"
    : "Compress";
  const confidence = trustConfidence({ tokensSaved, warnings, removedChunks, promptType, changes });
  const accountingSummary = accountingProfile(accounting);

  return {
    promptType,
    safeCompressionPotential,
    bestOptimization,
    confidence,
    accounting: accountingSummary,
    explanationRows: explanationRows({
      promptType,
      tokensSaved,
      warnings,
      removedChunks,
      semantic,
      bestOptimization,
      safeCompressionPotential,
      changes,
      mode,
    }),
  };
}

function riskLabel(score) {
  if (score === undefined || score === null) return "unknown";
  const value = Number(score);
  if (value >= 0.6) return "high";
  if (value >= 0.25) return "medium";
  return "low";
}

function classifyPromptType(inputValue, compile) {
  const text = String(inputValue || "").toLowerCase();
  if (/(^|\n)\s*(source|citation|cite)\s*:/i.test(inputValue) || compile.semantic?.summary?.rag_chunks > 0) {
    return "RAG/source prompt";
  }
  if (/\b(error|traceback|exception|stderr|tool log|http [45]\d\d)\b/i.test(inputValue)) {
    return "Tool/log prompt";
  }
  if (/^\s*[[{]/.test(inputValue) && /["']?(messages|tools|schema|properties)["']?\s*:/i.test(inputValue)) {
    return "JSON/schema prompt";
  }
  if (
    /\b(create|build|design|generate)\b/.test(text)
    && /\b(website|portfolio|landing page|homepage|app|interface)\b/.test(text)
  ) {
    return "Creative build prompt";
  }
  if (/\b(user|assistant|system):/i.test(inputValue)) {
    return "Chat history prompt";
  }
  return "General prompt";
}

function compressionPotential({ promptType, tokensSaved, removedChunks, text, changes }) {
  if (removedChunks > 0 || tokensSaved >= 25) return "high";
  if (changes.some((change) => change.type === "duplicate_removed")) return "medium";
  if (promptType === "Creative build prompt" && tokensSaved < 10) return "low";
  if (/(^|\n).+\n\n\1/i.test(text)) return "medium";
  if (tokensSaved > 0) return "medium";
  return "low";
}

function trustConfidence({ tokensSaved, warnings, removedChunks, promptType, changes }) {
  if (warnings.length) {
    return {
      label: "Review first",
      tone: "review",
      reason: warnings[0],
    };
  }
  if (removedChunks > 0) {
    return {
      label: "Verified semantic savings",
      tone: "semantic",
      reason: "Redundant RAG/source chunks were removed with semantic evidence.",
    };
  }
  if (promptType === "Creative build prompt" && tokensSaved < 10) {
    return {
      label: "No safe savings",
      tone: "unchanged",
      reason: "This is mostly unique creative requirements, so safe compression is naturally low.",
    };
  }
  if (changes.some((change) => change.type === "duplicate_removed") || tokensSaved > 0) {
    return {
      label: "Verified deterministic savings",
      tone: "verified",
      reason: "Savings came from deterministic compiler transforms.",
    };
  }
  return {
    label: "No safe savings",
    tone: "unchanged",
    reason: "The compiler did not find redundant content it could safely remove.",
  };
}

function accountingProfile(accounting) {
  if (!accounting || !Object.keys(accounting).length) {
    return {
      method: "unknown",
      label: "Token accounting unavailable",
      note: "Run compile again to receive token-accounting metadata.",
      optimizedReuseTokens: null,
      segmentOverheadTokens: null,
    };
  }
  const methodLabel = accounting.method === "segmented_prompt_estimate"
    ? "Segmented prompt estimate"
    : String(accounting.method || "Estimated tokens");
  const optimizedReuseTokens = accounting.optimized_reuse_tokens ?? accounting.optimizedTokens ?? null;
  return {
    method: accounting.method || "estimated",
    label: methodLabel,
    note: accounting.note || (
      accounting.method === "segmented_prompt_estimate"
        ? "Counts use segmented prompt estimates so pasted-back output is compared fairly."
        : "Token counts are estimated and can vary by provider tokenizer."
    ),
    originalTokens: accounting.original_tokens ?? null,
    optimizedTokens: accounting.optimized_tokens ?? null,
    optimizedReuseTokens,
    segmentOverheadTokens: accounting.segment_overhead_tokens ?? null,
    optimizedSegmentOverheadTokens: accounting.optimized_segment_overhead_tokens ?? null,
  };
}

function explanationRows({
  promptType,
  tokensSaved,
  warnings,
  removedChunks,
  semantic,
  bestOptimization,
  safeCompressionPotential,
  changes,
  mode,
}) {
  const rows = [];
  if (tokensSaved > 0) {
    rows.push({
      label: "Changed",
      body: removedChunks > 0
        ? `Removed ${removedChunks} redundant RAG/source chunk${removedChunks === 1 ? "" : "s"}.`
        : "Applied deterministic compression without changing protected values.",
    });
  } else {
    rows.push({
      label: "Changed",
      body: "No content was removed because the compiler did not find safe redundancy.",
    });
  }
  rows.push({
    label: "Kept",
    body: promptType === "Creative build prompt"
      ? "Preserved the creative requirements so the generated site brief stays complete."
      : "Preserved protected values and required context.",
  });
  rows.push({
    label: "Skipped",
    body: skippedReason({ promptType, semantic, bestOptimization, safeCompressionPotential, mode, changes }),
  });
  rows.push({
    label: "Trust",
    body: warnings.length
      ? `Review before use: ${warnings[0]}`
      : "No compiler warnings were reported for this output.",
  });
  return rows;
}

function skippedReason({ promptType, semantic, bestOptimization, safeCompressionPotential, mode }) {
  const ragChunks = Number(semantic.summary?.rag_chunks ?? 0);
  if (promptType === "Creative build prompt" && bestOptimization === "Distill") {
    return "Safe compression is low; use distillation if you want a shorter rewrite of the brief.";
  }
  if (ragChunks === 0) {
    return "Semantic RAG pruning was not applicable because no source/citation chunks were detected.";
  }
  if (semantic.scorer !== "embedding") {
    return "Embedding semantic scoring was not used; lexical scoring only removes near-exact source overlap.";
  }
  if (safeCompressionPotential === "low") {
    return `Mode ${mode} found little safe redundancy to remove.`;
  }
  return "No higher-risk lossy rewrite was applied.";
}
