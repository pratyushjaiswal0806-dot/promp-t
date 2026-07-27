import { useEffect } from "react";
import { useWorkbench } from "./context/CompilerContext.jsx";
import { InputPanel } from "./InputPanel.jsx";
import { OutputPanel } from "./OutputPanel.jsx";
import { PolicyControls } from "./PolicyControls.jsx";
import { AnalyticsPanel } from "./AnalyticsPanel.jsx";
import { HistoryPanel } from "./HistoryPanel.jsx";
import { Drawer } from "../components/Drawer.jsx";
import { StatusBar } from "../components/StatusBar.jsx";

const DRAWER_TABS = [
  { id: "metrics", label: "Metrics", primary: true },
  { id: "segments", label: "Segments" },
  { id: "diff", label: "Diff", primary: true },
  { id: "rag", label: "RAG" },
  { id: "changes", label: "Changes" },
  { id: "lint", label: "Lint" },
  { id: "entities", label: "Entities" },
  { id: "semantic", label: "Semantic" },
  { id: "history", label: "History", primary: true },
];

export function WorkbenchShell() {
  const {
    entities,
    changes,
    lintFindings,
    segments,
    diffItems,
    ragRows,
    semantic,
    appStatus,
    selectedModel,
    mode,
    controls,
    canExport,
    handleCompile,
  } = useWorkbench();

  useEffect(() => {
    const onKey = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        handleCompile();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleCompile]);

  const statusItems = [
    { label: "Model", value: selectedModel },
    { label: "Mode", value: mode },
    { label: "Budget", value: controls.targetTokenBudget || "open" },
    { label: "Cache", value: controls.cacheEnabled ? "on" : "off" },
    { dot: appStatus.className || "ready", label: appStatus.text },
  ];

  return (
    <div className="workbench-ide" data-page-id="workbench">
      <div className="workflow-strip" aria-label="Optimization workflow">
        {["Input", "Optimize", "Verify", "Export"].map((step, index) => (
          <div className="workflow-step" key={step}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{step}</strong>
          </div>
        ))}
      </div>

      <div className="workbench-content">
        <aside className="workbench-sidebar" aria-label="Optimization controls">
          <div className="sidebar-section">
            <PolicyControls />
          </div>
        </aside>

        <section className="workbench-main" aria-label="Prompt optimization workbench">
          <div className="workbench-editors">
            <div id="controlPanel" className="workbench-input">
              <div className="editor-panel-header">
                <span className="eyebrow">01 Input</span>
                <span className="kbd-hint"><kbd>⌘</kbd>+<kbd>Enter</kbd></span>
              </div>
              <div className="code-editor-area">
                <InputPanel />
              </div>
            </div>
            <div id="outputPanel" className="workbench-output">
              <div className="editor-panel-header">
                <span className="eyebrow">02 Optimized Output</span>
                {canExport && <span className="savings-badge">Ready to export</span>}
              </div>
              <div className="output-area">
                <OutputPanel />
              </div>
            </div>
          </div>

          <div id="analyticsPanel">
            <Drawer tabs={DRAWER_TABS} defaultHeight={190}>
              <div tabId="metrics"><AnalyticsPanel /></div>
              <div tabId="segments"><SegmentHeatmap segments={segments} /></div>
              <div tabId="diff"><DiffComparison diffItems={diffItems} /></div>
              <div tabId="rag"><RagPruningTable rows={ragRows} /></div>
              <div tabId="changes"><ChangeList changes={changes} /></div>
              <div tabId="lint"><LintList findings={lintFindings} /></div>
              <div tabId="entities"><EntityList entities={entities} /></div>
              <div tabId="semantic"><SemanticPanel semantic={semantic} /></div>
              <div tabId="history"><HistoryPanel /></div>
            </Drawer>
          </div>
        </section>
      </div>

      <div className="workbench-footer">
        <StatusBar items={statusItems} />
      </div>
    </div>
  );
}

function SegmentHeatmap({ segments }) {
  const maxTokens = Math.max(1, ...segments.map((segment) => Number(segment.tokens || segment.token_count || 0)));
  return (
    <div className="table-wrap">
      <table id="segmentsTable" className="compact-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Tokens</th>
            <th>Risk / Weight</th>
            <th>Why kept</th>
          </tr>
        </thead>
        <tbody>
          {segments.length ? segments.map((segment, index) => {
            const tokens = Number(segment.tokens || segment.token_count || 0);
            const risk = Number(segment.risk || segment.compression_risk_score || (segment.pinned ? 1 : 0.2));
            const width = Math.max(4, Math.round((tokens / maxTokens) * 100));
            return (
              <tr key={segment.id || index}>
                <td>{segment.id || segment.segment_id || `seg_${index + 1}`}</td>
                <td>{segment.type || segment.component_type || "text"}</td>
                <td>{tokens}</td>
                <td>
                  <div className="heatmap-track">
                    <span style={{ width: `${width}%`, opacity: Math.max(0.35, Math.min(1, risk)) }} />
                  </div>
                </td>
                <td>{segment.pinned || segment.is_pinned ? "Pinned/protected" : segment.status === "removed" ? "Removed by optimization" : "Kept for context"}</td>
              </tr>
            );
          }) : (
            <tr><td colSpan="5"><div className="empty-state">Run analyze or compile to see segment token weight and risk.</div></td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function DiffComparison({ diffItems }) {
  return (
    <div id="diffList" className="diff-comparison-list">
      {diffItems.length ? diffItems.map((item, index) => (
        <article key={`${item.segment_id || "seg"}-${index}`} className={`diff-row ${item.status || "changed"}`}>
          <header>
            <strong>{item.segment_id || `seg_${index + 1}`}</strong>
            <span>{item.status || "changed"} · {item.type || "text"}</span>
          </header>
          <div className="diff-columns">
            <pre>{item.original_text || ""}</pre>
            <pre>{item.optimized_text || item.new_text || ""}</pre>
          </div>
          <p>{item.reason || (item.status === "kept" ? "Kept because it still contributes context or protected values." : "Changed by optimization policy.")}</p>
        </article>
      )) : (
        <div className="empty-state">Compile to see original vs optimized diff rows.</div>
      )}
    </div>
  );
}

function RagPruningTable({ rows }) {
  return (
    <div className="table-wrap">
      <table id="ragPruningTable" className="compact-table">
        <thead>
          <tr>
            <th>Chunk</th>
            <th>Source</th>
            <th>Decision</th>
            <th>Relevance</th>
            <th>Similarity</th>
            <th>Why</th>
          </tr>
        </thead>
        <tbody>
          {rows.length ? rows.map((row) => (
            <tr key={row.id}>
              <td>{row.id}</td>
              <td>{row.source}</td>
              <td>{row.decision}</td>
              <td>{String(row.relevance ?? "-")}</td>
              <td>{String(row.similarity ?? "-")}</td>
              <td>{row.why}</td>
            </tr>
          )) : (
            <tr><td colSpan="6"><div className="empty-state">No RAG chunks scored yet.</div></td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function ChangeList({ changes }) {
  return (
    <div id="changes" className="diff-list">
      {changes.length ? changes.map((change, index) => (
        <div key={`${change.type}-${index}`} className={`diff-item ${change.type === "warning" ? "changed" : "kept"}`}>
          <div className="diff-heading">
            <span>{change.type}</span>
            {change.tokens && <span>{change.tokens}t</span>}
          </div>
          <span>{change.label || ""}</span>
        </div>
      )) : <div className="empty-state">No changes yet.</div>}
    </div>
  );
}

function LintList({ findings }) {
  return (
    <div id="lintFindings" className="stack-list">
      {findings.length ? findings.map((finding, index) => (
        <div key={`${finding.code || "finding"}-${index}`} className="stack-row">
          <span>{finding.severity || "info"} · {finding.code || "lint"}</span>
          <strong>{finding.message || finding.description || ""}</strong>
        </div>
      )) : <div className="empty-state">No lint findings.</div>}
    </div>
  );
}

function EntityList({ entities }) {
  return (
    <div id="entities">
      {entities.length ? entities.map((entity, index) => (
        <span key={`${entity.value || entity.name || entity}-${index}`} className="entity">
          {entity.value || entity.name || entity.text || String(entity)}
        </span>
      )) : <div className="empty-state">No protected entities detected.</div>}
    </div>
  );
}

function SemanticPanel({ semantic }) {
  const chunks = semantic?.chunks || [];
  return (
    <div id="semanticScores" className="semantic-panel">
      {semantic ? (
        <>
          <div className="stack-list">
            {[
              ["Scorer", semantic.scorer],
              ["Provider", semantic.provider],
              ["RAG chunks", semantic.summary?.rag_chunks ?? 0],
              ["Removed", semantic.summary?.removed_chunks ?? 0],
            ].map(([label, value]) => (
              <div key={label} className="stack-row"><span>{label}</span><strong>{String(value)}</strong></div>
            ))}
          </div>
          <div className="semantic-chunks">
            {chunks.slice(0, 12).map((chunk) => (
              <div key={chunk.id} className="semantic-chunk">
                <strong>{chunk.id}</strong>
                <span>{chunk.source || chunk.segment_type} · relevance {chunk.query_relevance_score}</span>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="empty-state">Run compile with semantic scoring to see chunk scores.</div>
      )}
    </div>
  );
}
