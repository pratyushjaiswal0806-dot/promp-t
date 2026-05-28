export function ProgressBar({ current, max, label, showLabel = true }) {
  const pct = max > 0 ? Math.min(100, (current / max) * 100) : 0;
  const cls = pct >= 95 ? "danger" : pct >= 80 ? "warning" : "";
  return (
    <div className="progress-bar-wrap">
      {showLabel && (
        <div className="progress-bar-labels">
          <span>{label || "Tokens"}</span>
          <span>{current}/{max}</span>
        </div>
      )}
      <div className="progress-bar-track">
        <div className={`progress-bar-fill ${cls}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
