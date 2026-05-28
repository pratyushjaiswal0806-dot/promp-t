export function StackList({ title, items, emptyMessage = "No data." }) {
  return (
    <div>
      {title && <h3 style={{ marginBottom: "0.75rem", fontSize: "1rem" }}>{title}</h3>}
      <div className="stack-list">
        {items && items.length ? (
          items.map(([label, value]) => (
            <div className="stack-row" key={label}>
              <span>{label}</span>
              <strong>{String(value)}</strong>
            </div>
          ))
        ) : (
          <div className="empty-state">{emptyMessage}</div>
        )}
      </div>
    </div>
  );
}
