export function DiffList({ items }) {
  return (
    <div>
      <h3 style={{ marginBottom: "0.75rem", fontSize: "1rem" }}>Diff</h3>
      <div className="diff-list">
        {items && items.length ? (
          items.map((item, i) => {
            const reason = item.reason || _diffReason(item);
            return (
              <div className={`diff-item ${item.status || "kept"}`} key={`${item.segment_id || i}`}>
                <div className="diff-heading">
                  <strong>{item.segment_id || "segment"}</strong>
                  <span>{item.status || "kept"}</span>
                </div>
                <p>{reason}</p>
              </div>
            );
          })
        ) : (
          <div className="empty-state">Compile a prompt to inspect the diff.</div>
        )}
      </div>
    </div>
  );
}

function _diffReason(item) {
  if (item.status === "removed") return "Removed from optimized prompt.";
  if (item.status === "changed") return "Compacted while preserving protected values and pins.";
  if (item.pinned) return "Pinned segment preserved exactly.";
  return "Segment retained.";
}
