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
  if (!Boolean(result.dry_run || compile.dry_run)) return "";
  const proposed = result.proposed_optimized_prompt || compile.proposed_optimized_text || "";
  const active = result.optimized_prompt || compile.optimized_text || "";
  return proposed && proposed !== active ? proposed : "";
}

function riskLabel(score) {
  if (score === undefined || score === null) return "unknown";
  const value = Number(score);
  if (value >= 0.6) return "high";
  if (value >= 0.25) return "medium";
  return "low";
}
