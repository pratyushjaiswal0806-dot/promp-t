import { useWorkbench } from "./context/CompilerContext.jsx";
import { StackList } from "../components/StackList.jsx";

export function AnalyticsPanel() {
  const { metrics, breakdown, report } = useWorkbench();
  const trust = report?.trustProfile;
  return (
    <>
      {trust && (
        <div id="trustMetrics" className="trust-metrics">
          <div><span>Prompt type</span><strong>{trust.promptType}</strong></div>
          <div><span>Best mode</span><strong>{trust.bestOptimization}</strong></div>
          <div><span>Trust</span><strong>{trust.confidence?.label || "-"}</strong></div>
          <div><span>Counting</span><strong>{trust.accounting?.label || "-"}</strong></div>
          <div><span>Pasted back</span><strong>{displayToken(trust.accounting?.optimizedReuseTokens)}</strong></div>
        </div>
      )}
      {metrics.length > 0 && (
        <div id="metrics" className="metrics-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "0.5rem", padding: 0 }}>
          {metrics.map(([label, value]) => (
            <div key={label} className="metric-item" style={{ padding: "0.5rem" }}>
              <span className="metric-label">{label}</span>
              <strong className="metric-value" style={{ fontSize: "1.2rem" }}>{String(value)}</strong>
            </div>
          ))}
        </div>
      )}
      {breakdown.length > 0 && <div id="breakdown"><StackList title="Breakdown" items={breakdown} emptyMessage="" /></div>}
      {metrics.length === 0 && breakdown.length === 0 && <div className="empty-state">Run analyze or compile to see metrics.</div>}
    </>
  );
}

function displayToken(value) {
  return value === null || value === undefined ? "-" : `${value}t`;
}
