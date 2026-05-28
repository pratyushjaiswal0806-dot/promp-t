export function StatusBar({ items = [] }) {
  return (
    <div className="status-bar" role="status">
      {items.map((item, i) => (
        <span key={i} className="status-bar-item">
          {item.dot && <span className={`status-bar-dot ${item.dot}`} />}
          <span>{item.label}</span>
          {item.value && <strong style={{ color: "var(--text)", fontWeight: 500 }}>{item.value}</strong>}
        </span>
      ))}
    </div>
  );
}
