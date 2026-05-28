export function CodeBlock({ title, lines }) {
  return (
    <div className="code-block full-span">
      {title && (
        <div className="code-header">
          <p className="eyebrow" style={{ fontSize: "0.65rem", color: "var(--accent-lime)", marginBottom: "0.25rem" }}>Terminal / SDK reference</p>
          <strong>{title}</strong>
        </div>
      )}
      <div className="code-body">
        {(!lines || lines.length === 0) ? (
          <code>No commands available.</code>
        ) : (
          lines.map((line, i) => (
            <div className="code-line" key={i}>
              <span className="code-line-num">{i + 1}</span>
              <code>{line}</code>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
