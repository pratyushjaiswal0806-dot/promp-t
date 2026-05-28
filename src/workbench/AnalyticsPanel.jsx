import { useWorkbench } from "./context/CompilerContext.jsx";
import { StackList } from "../components/StackList.jsx";

export function AnalyticsPanel() {
  const { metrics, breakdown } = useWorkbench();
  return (
    <>
      {metrics.length > 0 && (
        <div className="metrics-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "0.5rem", padding: 0 }}>
          {metrics.map(([label, value]) => (
            <div key={label} className="metric-item" style={{ padding: "0.5rem" }}>
              <span className="metric-label">{label}</span>
              <strong className="metric-value" style={{ fontSize: "1.2rem" }}>{String(value)}</strong>
            </div>
          ))}
        </div>
      )}
      {breakdown.length > 0 && <StackList title="Breakdown" items={breakdown} emptyMessage="" />}
      {metrics.length === 0 && breakdown.length === 0 && <div className="empty-state">Run analyze or compile to see metrics.</div>}
    </>
  );
}
