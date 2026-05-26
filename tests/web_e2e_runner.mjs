import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const baseUrl = process.argv[2];
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 11500 + Math.floor(Math.random() * 1000);
const profileDir = path.join(os.tmpdir(), `promptcompiler-e2e-${Date.now()}`);

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function requestJson(pathname, method = "GET") {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: "127.0.0.1", port, path: pathname, method }, (res) => {
      let data = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch (error) {
          reject(error);
        }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

async function waitForChrome() {
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    try {
      return await requestJson("/json/version");
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
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
      if (msg.error) {
        reject(new Error(`${msg.error.message}: ${msg.error.data || ""}`));
      } else {
        resolve(msg.result || {});
      }
      return;
    }
    if (msg.method) {
      events.push(msg);
    }
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
        close() {
          ws.close();
        },
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
    timeout: 15000,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || "Runtime evaluation failed");
  }
  return result.result.value;
}

async function waitFor(cdp, expression, label, timeout = 15000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await evalExpr(cdp, expression).catch(() => false)) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error(`Timed out waiting for ${label}`);
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
    `${pageId} page`,
  );
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
    "--window-size=1440,1200",
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
  await waitFor(cdp, 'document.readyState === "complete"', "page load");
  await waitFor(
    cdp,
    'Boolean(document.querySelector("#heroPanel") && document.querySelector("[data-page-target=workbench]") && document.querySelector("[data-page-target=docs]"))',
    "multipage shell boot",
  );

  const pageBoot = JSON.parse(
    await evalExpr(
      cdp,
      `JSON.stringify((() => ({
        navTargets: [...document.querySelectorAll('[data-page-target]')].map((item) => item.getAttribute('data-page-target')),
        homeText: document.body.textContent,
        shellWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth
      }))())`,
    ),
  );
  for (const pageId of ["home", "workbench", "how-it-works", "platform", "security", "use-cases", "docs", "api-reference", "observability"]) {
    assert(pageBoot.navTargets.includes(pageId), `missing navigation target: ${pageId}`);
  }
  for (const phrase of ["PromptCompiler", "Parse", "Protect", "Compile", "Measure", "Local-first"]) {
    assert(pageBoot.homeText.includes(phrase), `home explanation is missing: ${phrase}`);
  }
  assert(pageBoot.shellWidth <= pageBoot.innerWidth, "initial desktop shell overflowed horizontally");

  await evalExpr(cdp, `history.pushState(null, "", "/docs"); window.dispatchEvent(new PopStateEvent("popstate")); true`);
  await waitFor(
    cdp,
    `location.pathname === '/docs' && Boolean(document.querySelector('[data-page-id="docs"]'))`,
    "path-addressable docs page",
  );

  for (const pageId of ["how-it-works", "platform", "security", "use-cases", "docs", "api-reference", "observability"]) {
    await navigateToPage(cdp, pageId);
    const pageText = await evalExpr(cdp, "document.body.innerText");
    assert(pageText.length > 800, `${pageId} page is not informative enough`);
  }

  await navigateToPage(cdp, "workbench");
  await waitFor(
    cdp,
    'document.querySelector("#promptInput") && document.querySelector("#compileButton") && document.querySelector("#analyzeButton") && document.querySelector("#sampleSelect")?.options.length > 1',
    "workbench boot",
  );

  const boot = JSON.parse(
    await evalExpr(
      cdp,
      `JSON.stringify((() => ({
        requiredSelectors: [
          '#promptInput',
          '#promptIdeaInput',
          '#promptKindSelect',
          '#generatePromptButton',
          '#lintButton',
          '#analyzeButton',
          '#compileButton',
          '#modelSelect',
          '#sampleSelect',
          '#importInput',
          '#exportTextButton',
          '#exportJsonButton',
          '#historyList',
          '#segmentsTable',
          '#diffList',
          '#nimButton',
          '#modeSelect',
          '#targetBudgetInput',
          '#systemPromptRef',
          '#outputFormat',
          '#maxWordsInput',
          '#retrievalTopKInput',
          '#cacheStaticPrefix',
          '#cacheEnabled',
          '#explainToggle',
          '#dryRunInput',
          '#semanticScores',
          '#lintFindings'
        ].filter((selector) => !document.querySelector(selector)),
        premiumSelectors: [
          '#heroPanel',
          '#signalCanvas',
          '#pipelinePanel',
          '#proofPanel',
          '#workflowRail',
          '.motion-orbit',
          '.motion-stream',
          '.motion-marquee',
          '.page-transition-beam'
        ].filter((selector) => !document.querySelector(selector)),
        premiumText: document.body.innerText,
        canvasReady: window.__promptCompilerVizReady === true,
        canvasPixels: (() => {
          const canvas = document.querySelector('#signalCanvas');
          if (!canvas) return 0;
          const context = canvas.getContext('2d');
          const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
          let lit = 0;
          for (let index = 3; index < pixels.length; index += 4) {
            if (pixels[index] > 0 && (pixels[index - 1] > 10 || pixels[index - 2] > 10 || pixels[index - 3] > 10)) {
              lit += 1;
            }
          }
          return lit;
        })(),
        primaryText: document.querySelector('#compileButton')?.textContent || '',
        heroIndex: [...document.querySelectorAll('main section')].findIndex((section) => section.id === 'heroPanel'),
        controlIndex: [...document.querySelectorAll('main section')].findIndex((section) => section.id === 'controlPanel'),
        outputIndex: [...document.querySelectorAll('main section')].findIndex((section) => section.id === 'outputPanel'),
        analyticsIndex: [...document.querySelectorAll('main section')].findIndex((section) => section.id === 'analyticsPanel')
      }))())`,
    ),
  );

  assert(boot.requiredSelectors.length === 0, `missing dashboard selectors: ${boot.requiredSelectors.join(", ")}`);
  assert(boot.premiumSelectors.length === 0, `missing premium selectors: ${boot.premiumSelectors.join(", ")}`);
  assert(boot.primaryText.trim() === "Compile & Optimize", "primary action is not available");
  assert(boot.heroIndex !== -1 && boot.controlIndex !== -1 && boot.heroIndex < boot.controlIndex, "hero must lead the workbench");
  const accessibilityState = JSON.parse(
    await evalExpr(
      cdp,
      `JSON.stringify((() => {
        const modelSelect = document.querySelector('#modelSelect');
        const modelSearch = document.querySelector('#modelSearch');
        const originalModel = modelSelect.value;
        modelSearch.value = 'unlikely-model-filter-value';
        modelSearch.dispatchEvent(new Event('input', { bubbles: true }));
        return {
          activeNav: document.querySelector('[data-page-target="workbench"]')?.getAttribute('aria-current'),
          importButton: document.querySelector('.file-button')?.tagName,
          importInputHiddenByDisplay: getComputedStyle(document.querySelector('#importInput')).display,
          originalModel,
          filteredModel: modelSelect.value,
          modelOptions: [...modelSelect.options].map((option) => option.value)
        };
      })())`,
    ),
  );
  assert(accessibilityState.activeNav === "page", "active navigation must expose aria-current");
  assert(accessibilityState.importButton === "BUTTON", "file import affordance must be keyboard reachable");
  assert(accessibilityState.importInputHiddenByDisplay !== "none", "file input must not be display none");
  assert(accessibilityState.filteredModel === accessibilityState.originalModel, "model search must preserve selected model");
  assert(accessibilityState.modelOptions.includes(accessibilityState.originalModel), "selected model option disappeared while filtering");
  await evalExpr(
    cdp,
    `(() => {
      const modelSearch = document.querySelector('#modelSearch');
      modelSearch.value = '';
      modelSearch.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    })()`,
  );
  await evalExpr(cdp, `document.querySelector('.hero-actions a[href="#pipelinePanel"]')?.click()`);
  await waitFor(
    cdp,
    `location.hash === '#pipelinePanel' && Boolean(document.querySelector('[data-page-id="workbench"]') && document.querySelector('#pipelinePanel'))`,
    "workbench section anchor",
  );
  for (const phrase of ["What happens inside", "Parse", "Protect", "Compile", "Measure", "Local-first"]) {
    assert(boot.premiumText.includes(phrase), `premium explanation is missing: ${phrase}`);
  }
  assert(boot.canvasReady === true && boot.canvasPixels > 500, "signal canvas did not render visible pixels");
  assert(
    boot.outputIndex !== -1 && boot.analyticsIndex !== -1 && boot.outputIndex < boot.analyticsIndex,
    "optimized output must appear before analytics",
  );

  await evalExpr(
    cdp,
    `(() => {
      localStorage.removeItem('promptcompiler.history.v1');
      const sample = document.querySelector('#sampleSelect');
      if (sample.options.length > 1) {
        sample.selectedIndex = 1;
        sample.dispatchEvent(new Event('change', { bubbles: true }));
      }
      document.querySelector('#loadSampleButton').click();
      return true;
    })()`,
  );

  await waitFor(
    cdp,
    'document.querySelector("#promptInput")?.value.trim().length > 0',
    "sample prompt load",
  );

  await evalExpr(
    cdp,
    `(() => {
      const mode = document.querySelector('#modeSelect');
      mode.value = 'balanced';
      mode.dispatchEvent(new Event('change', { bubbles: true }));
      document.querySelector('#targetBudgetInput').value = '70';
      document.querySelector('#cacheEnabled').checked = true;
      document.querySelector('#retrievalTopKInput').value = '3';
      return true;
    })()`,
  );

  await evalExpr(cdp, `document.querySelector('#analyzeButton').click()`);
  await waitFor(
    cdp,
    'document.querySelectorAll("#segmentsTable tbody tr").length > 0 && !document.querySelector("#segmentsTable")?.innerText.includes("Analyze a prompt")',
    "analysis segment table",
  );

  await evalExpr(cdp, `document.querySelector('#compileButton').click()`);
  await waitFor(
    cdp,
    'document.querySelector("#compileButton")?.textContent === "Compile & Optimize" && document.querySelector("#optimizedOutput")?.textContent.includes("CASE-123")',
    "compile dashboard prompt",
  );
  const compiled = JSON.parse(
    await evalExpr(
      cdp,
      `JSON.stringify((() => ({
        metrics: document.querySelector('#metrics')?.innerText || '',
        breakdown: document.querySelector('#breakdown')?.innerText || '',
        entities: document.querySelector('#entities')?.innerText || '',
        changes: document.querySelector('#changes')?.innerText || '',
        lint: document.querySelector('#lintFindings')?.innerText || '',
        optimized: document.querySelector('#optimizedOutput')?.textContent || '',
        segments: document.querySelector('#segmentsTable')?.innerText || '',
        diff: document.querySelector('#diffList')?.innerText || '',
        historyCount: document.querySelectorAll('#historyList button').length,
        jsonDisabled: document.querySelector('#exportJsonButton')?.disabled,
        outputTop: document.querySelector('#outputPanel')?.getBoundingClientRect().top || 0,
        analyticsTop: document.querySelector('#analyticsPanel')?.getBoundingClientRect().top || 0
      }))())`,
    ),
  );
  assert(compiled.metrics.includes("Original") && compiled.metrics.includes("Saved"), "analytics metrics are missing");
  assert(compiled.metrics.includes("Route") && compiled.metrics.includes("Cache"), "route/cache metrics are missing");
  assert(compiled.breakdown.includes("type:"), "breakdown analytics are missing");
  assert(compiled.entities.includes("CASE-123"), "protected value analytics are missing");
  assert(compiled.changes.length > 0, "change analytics are missing");
  assert(compiled.changes.includes("tool_summary"), "compression plan actions are missing");
  assert(compiled.lint.length > 0, "lint findings area did not update");
  assert(compiled.optimized.includes("CASE-123"), "optimized prompt did not render");
  assert(compiled.segments.includes("seg_"), "segment table did not render analyzed segments");
  assert(compiled.diff.length > 0, "diff list did not render compile details");
  assert(compiled.historyCount >= 1, "compile history did not record the run");
  assert(compiled.jsonDisabled === false, "JSON export did not enable after compile");
  assert(compiled.outputTop < compiled.analyticsTop, "optimized output is not before analytics visually");

  await evalExpr(
    cdp,
    `(() => {
      const sample = document.querySelector('#sampleSelect');
      sample.value = 'rag-overlap';
      sample.dispatchEvent(new Event('change', { bubbles: true }));
      document.querySelector('#loadSampleButton').click();
      const mode = document.querySelector('#modeSelect');
      mode.value = 'balanced';
      mode.dispatchEvent(new Event('change', { bubbles: true }));
      document.querySelector('#targetBudgetInput').value = '';
      return true;
    })()`,
  );
  await waitFor(cdp, `document.querySelector('#promptInput')?.value.includes('Source: doc-a')`, "RAG sample load");
  await evalExpr(cdp, `document.querySelector('#compileButton').click()`);
  await waitFor(
    cdp,
    `document.querySelector("#compileButton")?.textContent === "Compile & Optimize" && document.querySelector("#semanticScores")?.innerText.includes("rag")`,
    "semantic signal render",
  );
  const semantic = JSON.parse(
    await evalExpr(
      cdp,
      `JSON.stringify((() => ({
        text: document.querySelector('#semanticScores')?.innerText || '',
        changes: document.querySelector('#changes')?.innerText || ''
      }))())`,
    ),
  );
  assert(semantic.text.includes("doc-"), "semantic scores did not preserve source metadata");
  assert(semantic.changes.includes("rag_prune"), "RAG pruning action did not render");

  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 390,
    height: 900,
    deviceScaleFactor: 2,
    mobile: false,
  });
  await new Promise((resolve) => setTimeout(resolve, 300));
  const mobile = JSON.parse(
    await evalExpr(
      cdp,
      `JSON.stringify((() => ({
        clientWidth: document.documentElement.clientWidth,
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        bodyScrollWidth: document.body.scrollWidth
      }))())`,
    ),
  );
  assert(mobile.scrollWidth <= mobile.innerWidth, `mobile overflow: ${mobile.scrollWidth} > ${mobile.innerWidth}`);
  assert(
    mobile.bodyScrollWidth <= mobile.innerWidth,
    `mobile body overflow: ${mobile.bodyScrollWidth} > ${mobile.innerWidth}`,
  );

  const httpErrors = cdp.events
    .filter((event) => event.method === "Network.responseReceived" && event.params.response.status >= 400)
    .map((event) => `${event.params.response.status} ${event.params.response.url}`);
  assert(httpErrors.length === 0, `HTTP errors: ${httpErrors.join(", ")}`);

  cdp.close();
} finally {
  chrome.kill("SIGTERM");
  await fs.rm(profileDir, { recursive: true, force: true }).catch(() => {});
}

process.exit(0);
