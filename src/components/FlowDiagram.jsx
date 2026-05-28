export function FlowDiagram({ nodes, arrows = true, highlightIndex }) {
  if (!nodes?.length) return null;
  const rows = [];
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    rows.push(
      <div key={n.id || i} className={`flow-node ${highlightIndex === i ? "highlight" : ""}`}>
        <span className="flow-node-label">{n.label || n.title}</span>
        {n.type && <span className="flow-node-type">{n.type}</span>}
      </div>
    );
    if (arrows && i < nodes.length - 1) {
      rows.push(<span key={`arrow-${i}`} className="flow-arrow">→</span>);
    }
  }
  return <div className="flow-diagram"><div className="flow-row">{rows}</div></div>;
}
