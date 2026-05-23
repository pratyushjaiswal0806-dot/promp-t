const input = document.querySelector("#promptInput");
const modelInput = document.querySelector("#modelInput");
const analyzeButton = document.querySelector("#analyzeButton");
const compileButton = document.querySelector("#compileButton");
const sampleButton = document.querySelector("#sampleButton");
const nimButton = document.querySelector("#nimButton");
const copyButton = document.querySelector("#copyButton");
const errorBox = document.querySelector("#errorBox");
const nimStatus = document.querySelector("#nimStatus");
const metrics = document.querySelector("#metrics");
const breakdown = document.querySelector("#breakdown");
const entities = document.querySelector("#entities");
const segmentsBody = document.querySelector("#segmentsBody");
const optimizedOutput = document.querySelector("#optimizedOutput");
const changes = document.querySelector("#changes");

let lastCompile = null;

const samplePayload = {
  messages: [
    {
      role: "system",
      content: "@pin Follow policy CASE-123. Never remove this instruction.",
    },
    {
      role: "user",
      content: "The customer reported device failure on 2026-05-23.",
    },
    {
      role: "tool",
      content:
        "ERROR same failure\nERROR same failure\nERROR same failure\nShipping URL: https://example.com/rma/CASE-123",
    },
    {
      role: "assistant",
      content: "I will check the RMA status.",
    },
    {
      role: "assistant",
      content: "I will check the RMA status.",
    },
  ],
};

sampleButton.addEventListener("click", () => {
  input.value = JSON.stringify(samplePayload, null, 2);
  clearError();
});

analyzeButton.addEventListener("click", async () => {
  await runAction(analyzeButton, async () => {
    const result = await postJson("/api/analyze", requestPayload("input"));
    renderAnalysis(result);
    optimizedOutput.textContent = "";
    changes.innerHTML = "";
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
      },
    ]);
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

async function boot() {
  input.value = JSON.stringify(samplePayload, null, 2);
  await refreshHealth();
  const result = await postJson("/api/analyze", requestPayload("input"));
  renderAnalysis(result);
}

async function refreshHealth() {
  try {
    const response = await fetch("/api/health");
    const payload = await response.json();
    nimStatus.textContent = payload.nim_configured ? "NIM ready" : "NIM key missing";
    nimStatus.className = `status-chip ${payload.nim_configured ? "ready" : "missing"}`;
  } catch (error) {
    nimStatus.textContent = "Server offline";
    nimStatus.className = "status-chip missing";
  }
}

function requestPayload(field) {
  return {
    [field]: input.value,
    model: modelInput.value.trim() || "openai/gpt-oss-20b",
  };
}

async function postJson(url, payload) {
  clearError();
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
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
            return `<div class="change">NIM summary generated with ${escapeHtml(item.model)}.</div>`;
          }
          return `<div class="change">${escapeHtml(item.type)}</div>`;
        })
        .join("")
    : `<div class="row-pill"><span>No changes</span><strong>0</strong></div>`;
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
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

boot();
