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
  { id: "metrics", label: "Metrics" },
  { id: "segments", label: "Segments" },
  { id: "diff", label: "Diff" },
  { id: "changes", label: "Changes" },
  { id: "lint", label: "Lint" },
  { id: "entities", label: "Entities" },
  { id: "semantic", label: "Semantic" },
  { id: "history", label: "History" },
];

export function WorkbenchShell() {
  const {
    metrics, breakdown, entities, changes, lintFindings, segments, diffItems, semantic,
    history, appStatus, workingAction, selectedModel, mode, inputValue,
    optimizedOutput, canExport, handleCompile, handleAnalyze,
  } = useWorkbench();

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        handleCompile();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleCompile]);

  const statusItems = [
    { label: "Model", value: selectedModel },
    { label: "Mode", value: mode },
    { dot: appStatus.className || "ready", label: appStatus.text },
  ];

  return (
    <div className="workbench-ide">
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Left sidebar */}
        <div className="workbench-sidebar">
          <div className="sidebar-section">
            <PolicyControls />
          </div>
        </div>

        {/* Center + right panels */}
        <div className="workbench-main">
          <div className="workbench-editors">
            <div className="workbench-input">
              <div className="editor-panel-header">
                <span className="eyebrow">01 Input</span>
                <span className="kbd-hint"><kbd>⌘</kbd>+<kbd>Enter</kbd> to compile</span>
              </div>
              <div className="code-editor-area">
                <InputPanel />
              </div>
            </div>
            <div className="workbench-output" style={{ position: "relative" }}>
              <div className="editor-panel-header">
                <span className="eyebrow">02 Output</span>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  {canExport && <span className="savings-badge">Tokens saved</span>}
                </div>
              </div>
              <div className="output-area" style={{ position: "relative" }}>
                <OutputPanel />
              </div>
            </div>
          </div>

          {/* Bottom drawer */}
          <Drawer tabs={DRAWER_TABS} defaultHeight={200}>
            <div tabId="metrics"><AnalyticsPanel /></div>
            <div tabId="segments">
              <div className="stack-list">
                {segments.map((s, i) => (
                  <div key={i} className="stack-row" style={{ gap: "0.75rem", alignItems: "flex-start" }}>
                    <span style={{ fontSize: "0.65rem", padding: "0.15rem 0.4rem", borderRadius: "var(--radius-sm)", background: s.pinned ? "rgba(199,248,90,0.15)" : "var(--surface-dark)", color: s.pinned ? "var(--accent-lime)" : "var(--muted)", border: "1px solid var(--line)", whiteSpace: "nowrap" }}>
                      {s.type || "text"}
                    </span>
                    <span style={{ fontSize: "0.7rem", color: "var(--muted)", whiteSpace: "nowrap" }}>{s.tokens}t</span>
                    {s.pinned && <span style={{ fontSize: "0.6rem", color: "var(--accent-lime)" }}>pinned</span>}
                    <span style={{ fontSize: "0.75rem", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {(s.text || s.content || "").slice(0, 100)}{(s.text || s.content || "").length > 100 ? "..." : ""}
                    </span>
                  </div>
                ))}
                {segments.length === 0 && <div className="empty-state">No segments yet. Run analyze or compile.</div>}
              </div>
            </div>
            <div tabId="diff">
              <div className="diff-list">
                {diffItems.length > 0 ? diffItems.map((d, i) => (
                  <div key={i} className={`diff-item ${d.status === "kept" ? "kept" : d.status === "changed" ? "changed" : "removed"}`}>
                    <div className="diff-heading">
                      <span style={{ fontWeight: 600, fontSize: "0.75rem" }}>{d.segment_id || d.id || `seg_${i}`}</span>
                      <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>{d.status} · {d.type || "text"}</span>
                    </div>
                    {d.status === "changed" && (
                      <div style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
                        <div style={{ color: "var(--danger)", textDecoration: "line-through" }}>- {(d.original_text || "").slice(0, 150)}{(d.original_text || "").length > 150 ? "..." : ""}</div>
                        <div style={{ color: "var(--accent-lime)" }}>+ {(d.new_text || d.optimized_text || "").slice(0, 150)}{(d.new_text || d.optimized_text || "").length > 150 ? "..." : ""}</div>
                      </div>
                    )}
                    {d.status === "removed" && (
                      <div style={{ fontSize: "0.75rem", color: "var(--danger)", textDecoration: "line-through" }}>- {(d.original_text || "").slice(0, 150)}{(d.original_text || "").length > 150 ? "..." : ""}</div>
                    )}
                    {d.status === "kept" && (
                      <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{(d.original_text || d.optimized_text || "").slice(0, 120)}...</div>
                    )}
                  </div>
                )) : <div className="empty-state">No diff data. Compile to see differences.</div>}
              </div>
            </div>
            <div tabId="changes">
              <div className="diff-list">
                {changes.map((c, i) => (
                  <div key={i} className={`diff-item ${c.type === "warning" ? "changed" : "kept"}`}>
                    <div className="diff-heading">
                      <span style={{ fontWeight: 600, fontSize: "0.75rem" }}>{c.type}</span>
                      {c.tokens && <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>{c.tokens}t</span>}
                    </div>
                    <span style={{ fontSize: "0.75rem" }}>{c.label || ""}</span>
                    {c.segment_id && <span style={{ fontSize: "0.65rem", color: "var(--muted)" }}>{c.segment_id}</span>}
                  </div>
                ))}
                {changes.length === 0 && <div className="empty-state">No changes yet.</div>}
              </div>
            </div>
            <div tabId="lint">
              <div className="stack-list">
                {lintFindings.map((f, i) => (
                  <div key={i} className="stack-row" style={{ gap: "0.5rem", alignItems: "flex-start" }}>
                    <span style={{ fontSize: "0.65rem", padding: "0.15rem 0.4rem", borderRadius: "var(--radius-sm)", background: f.severity === "high" ? "rgba(184,61,74,0.15)" : f.severity === "medium" ? "rgba(167,106,0,0.15)" : "var(--surface-dark)", color: f.severity === "high" ? "var(--danger)" : f.severity === "medium" ? "var(--warning)" : "var(--muted)", border: "1px solid var(--line)", whiteSpace: "nowrap" }}>
                      {f.severity || "info"}
                    </span>
                    <span style={{ fontSize: "0.65rem", color: "var(--muted)", whiteSpace: "nowrap" }}>{f.code || ""}</span>
                    <span style={{ fontSize: "0.75rem", flex: 1 }}>{f.message || f.description || ""}</span>
                  </div>
                ))}
                {lintFindings.length === 0 && <div className="empty-state">No lint findings.</div>}
              </div>
            </div>
            <div tabId="entities">
              <div>
                {entities.map((e, i) => (
                  <span key={i} className="entity">{e.value || e.name || e.text || String(e)}</span>
                ))}
                {entities.length === 0 && <div className="empty-state">No entities detected.</div>}
              </div>
            </div>
            <div tabId="semantic">
              <div className="stack-list">
                {semantic ? (
                  Object.entries(semantic).map(([k, v]) => (
                    <div key={k} className="stack-row">
                      <span>{k}</span>
                      <span>{String(v)}</span>
                    </div>
                  ))
                ) : (
                  <div className="empty-state">No semantic data. Run compile with semantic policy.</div>
                )}
              </div>
            </div>
            <div tabId="history"><HistoryPanel /></div>
          </Drawer>
        </div>
      </div>

      <div className="workbench-footer">
        <StatusBar items={statusItems} />
      </div>
    </div>
  );
}
