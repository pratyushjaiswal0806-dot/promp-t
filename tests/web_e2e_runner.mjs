import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const baseUrl = process.argv[2];
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 11500 + Math.floor(Math.random() * 1000);
const profileDir = path.join(os.tmpdir(), `promptcompiler-e2e-${Date.now()}`);
const visualWidths = [1440, 1024, 768, 390, 320];
const visualRoutes = ["home", "workbench", "docs", "api-reference", "observability"];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function requestJson(pathname, method = "GET") {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: "127.0.0.1", port, path: pathname, method }, (res) => {
      let data = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => { data += chunk; });
      res.on("end", () => {
        try { resolve(JSON.parse(data)); } catch (error) { reject(error); }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

async function waitForChrome() {
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    try { return await requestJson("/json/version"); }
    catch { await new Promise((resolve) => setTimeout(resolve, 100)); }
  }
  throw new Error("Chrome debugging endpoint did not start");
}

function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  const events = [];
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(`${msg.error.message}: ${msg.error.data || ""}`)) : resolve(msg.result || {});
      return;
    }
    if (msg.method) events.push(msg);
  });
  return new Promise((resolve, reject) => {
    ws.addEventListener("open", () => {
      resolve({
        events,
        send(method, params = {}) {
          const callId = ++id;
          ws.send(JSON.stringify({ id: callId, method, params }));
          return new Promise((resolveCall, rejectCall) => {
            pending.set(callId, { resolve: resolveCall, reject: rejectCall });
          });
        },
        close() { ws.close(); },
      });
    });
    ws.addEventListener("error", reject);
  });
}

async function evalExpr(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
    timeout: 20000,
  });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || "Runtime evaluation failed");
  return result.result.value;
}

async function waitFor(cdp, expression, label, timeout = 20000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await evalExpr(cdp, expression).catch(() => false)) return;
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function clickDrawerTab(cdp, label) {
  const selected = await evalExpr(
    cdp,
    `(() => {
      const button = [...document.querySelectorAll('.drawer-tab')].find((item) => item.textContent.trim() === ${JSON.stringify(label)});
      if (button) {
        button.click();
        return true;
      }
      const more = document.querySelector('#drawerMoreSelect');
      if (!more) return false;
      const option = [...more.options].find((item) => item.textContent.trim() === ${JSON.stringify(label)});
      if (!option) return false;
      more.value = option.value;
      more.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    })()`,
  );
  if (!selected) throw new Error(`Drawer panel not found: ${label}`);
}

async function setInputValue(cdp, selector, value, eventName = "input") {
  await evalExpr(
    cdp,
    `(() => {
      const el = document.querySelector(${JSON.stringify(selector)});
      if (!el) return false;
      const isCheckbox = el.type === 'checkbox';
      if (isCheckbox) {
        const desired = Boolean(${JSON.stringify(value)});
        if (el.checked !== desired) el.click();
        else el.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        const prototype = el.tagName === 'TEXTAREA'
          ? HTMLTextAreaElement.prototype
          : el.tagName === 'SELECT'
            ? HTMLSelectElement.prototype
            : HTMLInputElement.prototype;
        const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');
        if (descriptor?.set) descriptor.set.call(el, ${JSON.stringify(value)});
        else el.value = ${JSON.stringify(value)};
        el.dispatchEvent(new Event(${JSON.stringify(eventName)}, { bubbles: true }));
      }
      return true;
    })()`,
  );
}

async function compileAndWait(cdp, label) {
  const beforeReport = await evalExpr(cdp, `document.querySelector('#optimizationReport')?.innerText || ''`);
  await evalExpr(cdp, `document.querySelector('#compileButton').click()`);
  await waitFor(
    cdp,
    `document.querySelector('#compileButton')?.textContent === 'Compile & Optimize' && !document.querySelector('.error-box') && (document.querySelector('#optimizationReport')?.innerText || '') !== ${JSON.stringify(beforeReport)}`,
    `${label} compile complete`,
  );
}

async function setViewport(cdp, width, height = 980) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: width <= 390 ? 2 : 1,
    mobile: false,
  });
  await new Promise((resolve) => setTimeout(resolve, 250));
}

async function navigateToPage(cdp, pageId) {
  await evalExpr(
    cdp,
    `(() => {
      const target = document.querySelector('[data-page-target="${pageId}"]');
      if (!target) return false;
      target.click();
      return true;
    })()`,
  );
  await waitFor(
    cdp,
    `location.pathname === document.querySelector('[data-page-target="${pageId}"]')?.getAttribute('data-page-path') && Boolean(document.querySelector('[data-page-id="${pageId}"]'))`,
    `${pageId} visual page`,
  );
}

async function assertVisualContract(cdp, label, options = {}) {
  const result = JSON.parse(await evalExpr(cdp, `JSON.stringify((() => {
    const options = ${JSON.stringify(options)};
    const issues = [];
    const viewportWidth = window.innerWidth;
    const docWidth = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
    if (docWidth > viewportWidth + 1) {
      issues.push('page overflow ' + docWidth + ' > ' + viewportWidth);
    }

    const isVisible = (el) => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
    };
    const rectOf = (el) => {
      const rect = el.getBoundingClientRect();
      return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom, width: rect.width, height: rect.height };
    };
    const overlaps = (a, b) => a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1;
    const labelFor = (el) => {
      if (el.id) return '#' + el.id;
      if (el.getAttribute('data-page-target')) return '[data-page-target=' + el.getAttribute('data-page-target') + ']';
      if (el.className && typeof el.className === 'string') return '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.');
      return el.tagName.toLowerCase();
    };

    const containedSelectors = [
      '.topbar',
      '.brand-lockup',
      '.brand-title',
      '.status-chip',
      '.theme-toggle',
      '.topnav',
      '#controlPanel',
      '#outputPanel',
      '#analyticsPanel',
      '.drawer',
      '.drawer-tabs',
      '.table-wrap',
      '.optimization-report',
      '.usability-verdict',
      '.proposed-prompt-panel',
    ];

    for (const selector of containedSelectors) {
      for (const el of document.querySelectorAll(selector)) {
        if (!isVisible(el)) continue;
        const rect = rectOf(el);
        if (rect.left < -1 || rect.right > viewportWidth + 1) {
          issues.push(selector + ' escapes viewport: ' + Math.round(rect.left) + '..' + Math.round(rect.right) + ' of ' + viewportWidth);
        }
      }
    }

    const clipSelectors = [
      '.brand-title',
      '.status-chip',
      '.theme-toggle',
      '.topnav button',
      '#compileButton',
      '#exportTextButton',
      '#exportJsonButton',
      '.btn',
      '.editor-panel-header .eyebrow',
      '.savings-badge',
      '.drawer-tab',
      '.report-metric span',
      '.report-metric strong',
      '.risk-pill',
      '.history-card > button',
      '.history-actions button',
      '.usability-verdict strong',
      '.usability-verdict span',
      '.proposed-prompt-heading strong',
      '.proposed-prompt-heading span',
    ];

    for (const selector of clipSelectors) {
      for (const el of document.querySelectorAll(selector)) {
        if (!isVisible(el)) continue;
        if (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2) {
          issues.push(labelFor(el) + ' clips text: ' + el.scrollWidth + 'x' + el.scrollHeight + ' > ' + el.clientWidth + 'x' + el.clientHeight);
        }
      }
    }

    const overlapGroups = [
      ['topbar children', [...document.querySelectorAll('.topbar > *')]],
      ['editor panels', [...document.querySelectorAll('.workbench-editors > *')]],
      ['report cards', [...document.querySelectorAll('.report-grid > .report-metric')]],
    ];
    for (const [group, rawItems] of overlapGroups) {
      const items = rawItems.filter(isVisible);
      for (let i = 0; i < items.length; i += 1) {
        for (let j = i + 1; j < items.length; j += 1) {
          if (overlaps(rectOf(items[i]), rectOf(items[j]))) {
            issues.push(group + ' overlap: ' + labelFor(items[i]) + ' / ' + labelFor(items[j]));
          }
        }
      }
    }

    if (options.expectWorkbenchDetails) {
      for (const selector of ['#optimizationReport .report-metric', '#usabilityVerdict', '#historyList .history-card']) {
        if (!document.querySelector(selector)) issues.push('missing visual target ' + selector);
      }
    }

    if (options.expectDryRun) {
      for (const selector of ['#proposedPromptPanel', '#optimizationReport .report-metric', '#usabilityVerdict']) {
        if (!document.querySelector(selector)) issues.push('missing visual target ' + selector);
      }
    }

    return { issues, docWidth, viewportWidth };
  })())`));
  assert(result.issues.length === 0, `${label} visual issues: ${result.issues.join("; ")}`);
}

async function assertVisualSweep(cdp) {
  for (const width of visualWidths) {
    await setViewport(cdp, width);
    await assertVisualContract(cdp, `populated workbench ${width}px`, { expectWorkbenchDetails: true });
  }

  for (const width of visualWidths) {
    await setViewport(cdp, width);
    for (const route of visualRoutes) {
      await navigateToPage(cdp, route);
      await assertVisualContract(cdp, `${route} ${width}px`);
    }
  }
}

const chrome = spawn(
  chromePath,
  [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=1440,1100",
    "about:blank",
  ],
  { stdio: ["ignore", "ignore", "pipe"] },
);

try {
  await waitForChrome();
  const target = await requestJson("/json/new?about:blank", "PUT");
  const cdp = await connect(target.webSocketDebuggerUrl);
  await cdp.send("Runtime.enable");
  await cdp.send("Page.enable");
  await cdp.send("Network.enable");

  await cdp.send("Page.navigate", { url: baseUrl });
  await waitFor(cdp, `document.readyState === "complete"`, "page load");
  await waitFor(cdp, `Boolean(document.querySelector('[data-page-target="workbench"]'))`, "navigation boot");
  await evalExpr(cdp, `document.querySelector('[data-page-target="workbench"]').click()`);
  await waitFor(
    cdp,
    `location.pathname === '/workbench' && Boolean(document.querySelector('#promptInput') && document.querySelector('#compileButton'))`,
    "workbench boot",
  );

  const boot = JSON.parse(await evalExpr(cdp, `JSON.stringify((() => ({
    requiredSelectors: [
      '#promptInput', '#compileButton', '#analyzeButton', '#lintButton', '#nimButton',
      '#modelSelect', '#sampleSelect', '#workflowPresetSelect', '#targetBudgetInput',
      '#dryRunInput', '#zeroRetentionInput', '#cacheEnabled', '#outputFormat',
      '#maxWordsInput', '#explainToggle', '#systemPromptRef', '#retrievalTopKInput',
      '#toolCompactInput', '#autoSemanticInput', '#deterministicSemanticInput',
      '.optimized-output-scroll', '#optimizedOutput', '#optimizationReport',
      '#exportTextButton', '#exportJsonButton'
    ].filter((selector) => !document.querySelector(selector)),
    semanticControls: {
      autoVisible: document.querySelector('#autoSemanticInput')?.getBoundingClientRect().height > 0,
      forceVisible: document.querySelector('#deterministicSemanticInput')?.getBoundingClientRect().height > 0,
      scrollRegion: Boolean(document.querySelector('.optimized-output-scroll'))
    },
    primaryText: document.querySelector('#compileButton')?.textContent.trim(),
    outputTop: document.querySelector('#outputPanel')?.getBoundingClientRect().top,
    analyticsTop: document.querySelector('#analyticsPanel')?.getBoundingClientRect().top,
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }))())`));
  assert(boot.requiredSelectors.length === 0, `missing selectors: ${boot.requiredSelectors.join(", ")}`);
  assert(boot.semanticControls.autoVisible, "auto semantic control is not visible");
  assert(boot.semanticControls.forceVisible, "force semantic control is not visible");
  assert(boot.semanticControls.scrollRegion, "optimized output scroll region missing");
  assert(boot.primaryText === "Compile & Optimize", "primary action label changed");
  assert(boot.outputTop < boot.analyticsTop, "optimized output must appear before analytics");
  assert(boot.scrollWidth <= boot.innerWidth, "desktop workbench overflowed horizontally");

  await evalExpr(cdp, `localStorage.removeItem('promptcompiler.history.v1')`);

  await setInputValue(cdp, "#sampleSelect", "support-rma", "change");
  await evalExpr(cdp, `document.querySelector('#loadSampleButton').click()`);
  await waitFor(cdp, `document.querySelector('#promptInput')?.value.includes('CASE-123')`, "support sample load");
  await setInputValue(cdp, "#targetBudgetInput", "80");
  await setInputValue(cdp, "#cacheEnabled", true);
  await compileAndWait(cdp, "support RMA");
  const support = JSON.parse(await evalExpr(cdp, `JSON.stringify((() => ({
    optimized: document.querySelector('#optimizedOutput')?.textContent || '',
    report: document.querySelector('#optimizationReport')?.innerText || '',
    verdict: document.querySelector('#usabilityVerdict')?.innerText || '',
    jsonDisabled: document.querySelector('#exportJsonButton')?.disabled,
    historyCards: document.querySelectorAll('#historyList .history-card').length
  }))())`));
  assert(support.optimized.includes("CASE-123"), "protected entity missing from optimized output");
  assert(support.report.includes("Optimization Report"), "optimization report did not render");
  assert(/Ready to use|Review first|Do not use/.test(support.verdict), "usability verdict did not render");
  assert(support.report.includes("Cache"), "route/cache status missing from report");
  assert(support.jsonDisabled === false, "JSON export did not enable after compile");

  const longPrompt = Array.from(
    { length: 140 },
    (_, index) => `Unique requirement ${index + 1}: preserve detail-${index + 1} and explain it clearly.`,
  ).join(" ");
  await setInputValue(cdp, "#promptInput", longPrompt);
  await setInputValue(cdp, "#targetBudgetInput", "");
  await setInputValue(cdp, "#modeSelect", "balanced", "change");
  await compileAndWait(cdp, "long unchanged prompt");
  const scrollState = JSON.parse(await evalExpr(cdp, `JSON.stringify((() => {
    const el = document.querySelector('.optimized-output-scroll');
    return {
      scrollHeight: el?.scrollHeight || 0,
      clientHeight: el?.clientHeight || 0,
      overflowY: el ? getComputedStyle(el).overflowY : '',
      insight: document.querySelector('#optimizationInsight')?.innerText || ''
    };
  })())`));
  assert(scrollState.scrollHeight > scrollState.clientHeight, "optimized output does not have vertical overflow");
  assert(scrollState.overflowY === "auto", "optimized output scroll region should use overflow auto");
  assert(scrollState.insight.includes("No safe compression found"), "unchanged prompt insight did not render");

  const creativePrompt = [
    "Create a modern, professional, responsive portfolio website for a developer named Alex Rivera.",
    "Include a hero section, about section, skills, featured projects, experience, testimonials, blog cards, and contact form.",
    "Use elegant visual design, strong typography, responsive behavior, accessible buttons, subtle motion, SEO metadata, and polished placeholder copy.",
  ].join("\n\n");
  await setInputValue(cdp, "#promptInput", creativePrompt);
  await compileAndWait(cdp, "creative portfolio prompt");
  const trustState = JSON.parse(await evalExpr(cdp, `JSON.stringify((() => ({
    badge: document.querySelector('#trustBadge')?.innerText || '',
    recommendation: document.querySelector('#promptRecommendation')?.innerText || '',
    accounting: document.querySelector('#tokenAccountingPanel')?.innerText || '',
    rows: document.querySelector('#trustExplanationRows')?.innerText || '',
    metrics: document.querySelector('#trustMetrics')?.innerText || ''
  }))())`));
  assert(trustState.badge.includes("No safe savings"), "trust badge did not explain low safe savings");
  assert(trustState.recommendation.includes("Creative build prompt"), "prompt type recommendation missing");
  assert(trustState.recommendation.includes("Distill"), "distillation recommendation missing");
  assert(/Segmented|segmented/.test(trustState.accounting), "token accounting panel did not mention segmented counting");
  assert(/distillation/i.test(trustState.rows), "trust explanation rows did not explain distillation");

  await clickDrawerTab(cdp, "History");
  await waitFor(cdp, `document.querySelectorAll('#historyList .history-card').length >= 1`, "history record");

  await clickDrawerTab(cdp, "Segments");
  await waitFor(cdp, `document.querySelectorAll('#segmentsTable tbody tr').length > 0`, "segment heatmap");
  await clickDrawerTab(cdp, "Diff");
  await waitFor(cdp, `document.querySelector('#diffList')?.innerText.length > 0`, "diff list");

  await setInputValue(cdp, "#sampleSelect", "rag-overlap", "change");
  await evalExpr(cdp, `document.querySelector('#loadSampleButton').click()`);
  await waitFor(cdp, `document.querySelector('#promptInput')?.value.includes('Source: doc-a')`, "rag sample load");
  await setInputValue(cdp, "#targetBudgetInput", "");
  await setInputValue(cdp, "#autoSemanticInput", true);
  await setInputValue(cdp, "#deterministicSemanticInput", false);
  await compileAndWait(cdp, "RAG overlap");
  await clickDrawerTab(cdp, "RAG");
  await waitFor(cdp, `document.querySelector('#ragPruningTable')?.innerText.includes('doc-')`, "RAG pruning table");
  await clickDrawerTab(cdp, "Semantic");
  await waitFor(cdp, `document.querySelector('#semanticScores')?.innerText.includes('embedding')`, "semantic panel");

  await setInputValue(cdp, "#sampleSelect", "agent-logs", "change");
  await evalExpr(cdp, `document.querySelector('#loadSampleButton').click()`);
  await waitFor(cdp, `document.querySelector('#promptInput')?.value.includes('BUILD-882')`, "tool log sample load");
  await setInputValue(cdp, "#modeSelect", "aggressive", "change");
  await setInputValue(cdp, "#toolCompactInput", true);
  await compileAndWait(cdp, "long tool log");
  const toolLog = await evalExpr(cdp, `document.querySelector('#optimizationReport')?.innerText || ''`);
  assert(toolLog.includes("Risk") || toolLog.includes("Transformation plan"), "tool log report missing");

  const jsonPrompt = `@pin Keep CASE-JSON-7 exactly.\n\n${JSON.stringify({
    task: "clean schema prompt",
    schema: { type: "object", properties: { name: { type: "string" }, order: { type: "string" } } },
    repeated: Array(6).fill("Return strict JSON for CASE-JSON-7."),
  }, null, 2)}`;
  await setInputValue(cdp, "#promptInput", jsonPrompt);
  await setInputValue(cdp, "#outputFormat", "json", "change");
  await setInputValue(cdp, "#explainToggle", false);
  await compileAndWait(cdp, "JSON-heavy prompt");
  const jsonOutput = await evalExpr(cdp, `document.querySelector('#optimizedOutput')?.textContent || ''`);
  assert(jsonOutput.includes("CASE-JSON-7"), "JSON-heavy protected value missing");

  await setInputValue(cdp, "#promptInput", "@pin one two three four five six seven eight");
  await setInputValue(cdp, "#targetBudgetInput", "8");
  await evalExpr(cdp, `document.querySelector('#compileButton').click()`);
  await waitFor(cdp, `document.querySelector('.error-box')?.innerText.includes('Pinned content')`, "pinned budget failure");

  await setInputValue(cdp, "#promptInput", "repeat\n\nrepeat");
  await setInputValue(cdp, "#targetBudgetInput", "");
  await setInputValue(cdp, "#dryRunInput", true);
  await compileAndWait(cdp, "dry-run");
  await waitFor(cdp, `document.querySelector('#usabilityVerdict')?.textContent.includes('Preview only')`, "dry-run verdict");
  const dryRun = JSON.parse(await evalExpr(cdp, `JSON.stringify((() => ({
    report: document.querySelector('#optimizationReport')?.textContent || '',
    verdict: document.querySelector('#usabilityVerdict')?.textContent || '',
    proposed: document.querySelector('#proposedPromptPanel')?.textContent || ''
  }))())`));
  assert(dryRun.report.includes("Dry Run"), "dry-run report missing");
  assert(dryRun.verdict.includes("Preview only"), "dry-run verdict missing");
  assert(
    dryRun.proposed.includes("Proposed optimized prompt"),
    `dry-run proposed prompt missing: ${JSON.stringify(dryRun)}`,
  );
  await setViewport(cdp, 390);
  await assertVisualContract(cdp, "dry-run proposed prompt 390px", { expectDryRun: true });
  await setViewport(cdp, 1440, 1100);

  await setInputValue(cdp, "#dryRunInput", false);
  await setInputValue(cdp, "#cacheEnabled", true);
  await compileAndWait(cdp, "cache miss");
  await compileAndWait(cdp, "cache hit");
  const cacheReport = await evalExpr(cdp, `document.querySelector('#optimizationReport')?.innerText || ''`);
  assert(cacheReport.includes("hit"), "cache-enabled repeated compile did not show a hit");

  await setInputValue(cdp, "#cacheEnabled", false);
  await setInputValue(cdp, "#zeroRetentionInput", false);
  await compileAndWait(cdp, "zero retention off");
  await setInputValue(cdp, "#zeroRetentionInput", true);
  await compileAndWait(cdp, "zero retention");
  const zeroRetention = await evalExpr(cdp, `document.querySelector('#optimizationReport')?.innerText || ''`);
  assert(zeroRetention.includes("Zero retention") && zeroRetention.includes("on"), "zero-retention status missing");

  await clickDrawerTab(cdp, "History");
  await evalExpr(cdp, `document.querySelector('#historyList .history-card button')?.click()`);
  await evalExpr(cdp, `[...document.querySelectorAll('#historyList .history-actions button')].find((button) => button.textContent === 'Compare')?.click()`);
  await waitFor(cdp, `document.querySelector('.compare-table')?.innerText.includes('aggressive')`, "mode comparison");

  await assertVisualSweep(cdp);

  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 390,
    height: 900,
    deviceScaleFactor: 2,
    mobile: false,
  });
  await new Promise((resolve) => setTimeout(resolve, 300));
  const mobile = JSON.parse(await evalExpr(cdp, `JSON.stringify((() => ({
    scrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    innerWidth: window.innerWidth
  }))())`));
  assert(mobile.scrollWidth <= mobile.innerWidth, `mobile overflow: ${mobile.scrollWidth} > ${mobile.innerWidth}`);
  assert(mobile.bodyScrollWidth <= mobile.innerWidth, `mobile body overflow: ${mobile.bodyScrollWidth} > ${mobile.innerWidth}`);

  const httpErrors = cdp.events
    .filter((event) => event.method === "Network.responseReceived" && event.params.response.status >= 400)
    .filter((event) => !(event.params.response.status === 413 && event.params.response.url.endsWith("/v1/compile")))
    .map((event) => `${event.params.response.status} ${event.params.response.url}`);
  assert(httpErrors.length === 0, `HTTP errors: ${httpErrors.join(", ")}`);

  cdp.close();
} finally {
  chrome.kill("SIGTERM");
  await fs.rm(profileDir, { recursive: true, force: true }).catch(() => {});
}

process.exit(0);
