const input = document.querySelector("#promptInput");
const modelInput = document.querySelector("#modelInput");
const analyzeButton = document.querySelector("#analyzeButton");
const compileButton = document.querySelector("#compileButton");
const sampleButton = document.querySelector("#sampleButton");
const sampleSelect = document.querySelector("#sampleSelect");
const importInput = document.querySelector("#importInput");
const nimButton = document.querySelector("#nimButton");
const copyButton = document.querySelector("#copyButton");
const exportJsonButton = document.querySelector("#exportJsonButton");
const exportTextButton = document.querySelector("#exportTextButton");
const errorBox = document.querySelector("#errorBox");
const nimStatus = document.querySelector("#nimStatus");
const modelSource = document.querySelector("#modelSource");
const metrics = document.querySelector("#metrics");
const breakdown = document.querySelector("#breakdown");
const entities = document.querySelector("#entities");
const segmentsBody = document.querySelector("#segmentsBody");
const optimizedOutput = document.querySelector("#optimizedOutput");
const changes = document.querySelector("#changes");
const diffView = document.querySelector("#diffView");

let lastCompile = null;
let samples = [];
const fallbackModel = "nvidia/llama-3.1-nemotron-nano-8b-v1";

sampleButton.addEventListener("click", () => {
  const sample = samples.find((item) => item.id === sampleSelect.value) || samples[0];
  if (sample) {
    input.value = sample.input;
  }
  clearError();
});

importInput.addEventListener("change", async () => {
  const file = importInput.files?.[0];
  if (!file) return;
  input.value = await file.text();
  clearError();
  importInput.value = "";
});

analyzeButton.addEventListener("click", async () => {
  await runAction(analyzeButton, async () => {
    const result = await postJson("/api/analyze", requestPayload("input"));
    renderAnalysis(result);
    optimizedOutput.textContent = "";
    changes.innerHTML = "";
    diffView.innerHTML = "";
  });
});

compileButton.addEventListener("click", async () => {
  await runAction(compileButton, async () => {
    const result = await postJson("/api/compile", requestPayload("input"));
    lastCompile = result;
    renderCompile(result);
  });
});

nimButton.addEventListener("click", async () => {
  const text = lastCompile?.optimized_text || input.value;
  await runAction(nimButton, async () => {
    const result = await postJson("/api/nim/summarize", {
      text,
      model: modelInput.value.trim(),
    });
    optimizedOutput.textContent = result.summary;
    renderChanges([
      {
        type: "nim_summary",
        model: result.model,
        preservation: result.preservation,
      },
    ]);
    renderPreservation(result.preservation);
  });
});

copyButton.addEventListener("click", async () => {
  const text = optimizedOutput.textContent;
  if (!text) return;
  await navigator.clipboard.writeText(text);
  copyButton.textContent = "Copied";
  setTimeout(() => {
    copyButton.textContent = "Copy";
  }, 900);
});

exportTextButton.addEventListener("click", () => {
  if (!lastCompile?.optimized_text) return;
  download("promptcompiler-optimized.txt", lastCompile.optimized_text, "text/plain");
});

exportJsonButton.addEventListener("click", () => {
  if (!lastCompile) return;
  download("promptcompiler-report.json", JSON.stringify(lastCompile, null, 2), "application/json");
});

async function boot() {
  const health = await refreshHealth();
  await loadModels(health);
  await loadSamples();
  if (samples[0]) input.value = samples[0].input;
  const result = await postJson("/api/analyze", requestPayload("input"));
  renderAnalysis(result);
}

async function refreshHealth() {
  try {
    const response = await fetch("/api/health");
    const payload = await response.json();
    nimStatus.textContent = payload.nim_configured ? "NIM ready" : "NIM key missing";
    nimStatus.className = `status-chip ${payload.nim_configured ? "ready" : "missing"}`;
    return payload;
  } catch (error) {
    nimStatus.textContent = "Server offline";
    nimStatus.className = "status-chip missing";
    return { default_model: fallbackModel, nim_configured: false };
  }
}

async function loadModels(health) {
  try {
    const response = await fetch("/api/models");
    const payload = await response.json();
    const models = payload.models || [];
    modelInput.innerHTML = models
      .map(
        (model) =>
          `<option value="${escapeHtml(model.id)}">${escapeHtml(model.label)} (${escapeHtml(model.id)})</option>`,
      )
      .join("");
    modelInput.value = payload.default_model || health.default_model || fallbackModel;
    modelSource.textContent = payload.source === "nvidia-live" ? "NVIDIA models" : "Local models";
    modelSource.className = `status-chip ${payload.source === "nvidia-live" ? "ready" : "missing"}`;
  } catch (error) {
    modelInput.innerHTML = `<option value="${fallbackModel}">${fallbackModel}</option>`;
    modelSource.textContent = "Model fallback";
    modelSource.className = "status-chip missing";
  }
}

async function loadSamples() {
  const response = await fetch("/api/samples");
  const payload = await response.json();
  samples = payload.samples || [];
  sampleSelect.innerHTML = samples
    .map((sample) => `<option value="${escapeHtml(sample.id)}">${escapeHtml(sample.name)}</option>`)
    .join("");
}

function requestPayload(field) {
  return {
    [field]: input.value,
    model: modelInput.value.trim() || fallbackModel,
  };
}

async function postJson(url, payload) {
  clearError();
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch (error) {
    data = { error: text || `Request failed with ${response.status}` };
  }
  if (!response.ok) {
    const message = data.error || `Request failed with ${response.status}`;
    throw new Error(data.code ? `${data.code}: ${message}` : message);
  }
  return data;
}

async function runAction(button, action) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = "Working";
  try {
    await action();
  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

function renderAnalysis(result) {
  renderMetrics([
    ["Tokens", result.total_tokens],
    ["Segments", result.segment_count],
    ["Duplicates", result.duplicate_groups.length],
    ["Opportunity", `${Math.round(result.compression_opportunity * 100)}%`],
  ]);
  renderBreakdown(result);
  renderEntities(result.protected_entities);
  renderSegments(result.segments);
}

function renderCompile(result) {
  renderMetrics([
    ["Original", result.original_tokens],
    ["Optimized", result.optimized_tokens],
    ["Saved", result.tokens_saved],
    ["Savings", `${Math.round(result.savings_ratio * 100)}%`],
  ]);
  optimizedOutput.textContent = result.optimized_text;
  renderChanges(result.changes);
  renderDiff(result.diff || []);
}

function renderMetrics(items) {
  metrics.innerHTML = items
    .map(
      ([label, value]) => `
        <div class="metric">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(String(value))}</strong>
        </div>
      `,
    )
    .join("");
}

function renderBreakdown(result) {
  const rows = [
    ...Object.entries(result.by_type || {}).map(([key, value]) => [`type:${key}`, value]),
    ...Object.entries(result.by_role || {}).map(([key, value]) => [`role:${key}`, value]),
  ];
  breakdown.innerHTML = rows.length
    ? rows
        .map(
          ([key, value]) => `
            <div class="row-pill">
              <span>${escapeHtml(key)}</span>
              <strong>${escapeHtml(String(value))}</strong>
            </div>
          `,
        )
        .join("")
    : `<div class="row-pill"><span>No segments</span><strong>0</strong></div>`;
}

function renderEntities(values) {
  entities.innerHTML = values.length
    ? values.map((value) => `<div class="entity">${escapeHtml(value)}</div>`).join("")
    : `<div class="row-pill"><span>No protected values</span><strong>0</strong></div>`;
}

function renderSegments(segments) {
  segmentsBody.innerHTML = segments
    .map(
      (segment) => `
        <tr>
          <td>${escapeHtml(segment.id)}</td>
          <td>${escapeHtml(segment.type)}</td>
          <td>${escapeHtml(segment.role)}</td>
          <td>${escapeHtml(String(segment.tokens))}</td>
          <td class="${segment.pinned ? "pin" : ""}">${segment.pinned ? "Pinned" : ""}</td>
          <td><div class="preview">${escapeHtml(segment.text)}</div></td>
        </tr>
      `,
    )
    .join("");
}

function renderChanges(items) {
  changes.innerHTML = items.length
    ? items
        .map((item) => {
          if (item.type === "duplicate_removed") {
            return `<div class="change">Removed duplicate ${escapeHtml(item.segment_id)}; kept ${escapeHtml(item.kept_segment_id)}.</div>`;
          }
          if (item.type === "segment_compacted") {
            return `<div class="change">Compacted ${escapeHtml(item.segment_id)} and removed ${escapeHtml(String(item.lines_removed))} repeated or omitted lines.</div>`;
          }
          if (item.type === "nim_summary") {
            const missing = item.preservation?.missing_entities || [];
            const warning = missing.length
              ? ` Missing protected values: ${missing.map(escapeHtml).join(", ")}.`
              : "";
            return `<div class="change ${missing.length ? "warning" : ""}">NIM summary generated with ${escapeHtml(item.model)}.${warning}</div>`;
          }
          return `<div class="change">${escapeHtml(item.type)}</div>`;
        })
        .join("")
    : `<div class="row-pill"><span>No changes</span><strong>0</strong></div>`;
}

function renderDiff(items) {
  diffView.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <div class="diff-item ${escapeHtml(item.status)}">
              <div class="diff-meta">
                <div>${escapeHtml(item.segment_id)}</div>
                <div>${escapeHtml(item.status)}</div>
                <div>${escapeHtml(item.type)} / ${escapeHtml(item.role)}</div>
              </div>
              <div>
                <h3>Original</h3>
                <div class="diff-text">${escapeHtml(item.original_text || "")}</div>
              </div>
              <div>
                <h3>Optimized</h3>
                <div class="diff-text">${escapeHtml(item.optimized_text || item.reason || "")}</div>
              </div>
            </div>
          `,
        )
        .join("")
    : `<div class="row-pill"><span>No diff yet</span><strong>0</strong></div>`;
}

function renderPreservation(preservation) {
  if (!preservation || preservation.ok) return;
  showError(`NIM summary is missing protected values: ${preservation.missing_entities.join(", ")}`);
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearError() {
  errorBox.hidden = true;
  errorBox.textContent = "";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function download(filename, text, type) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

boot();
