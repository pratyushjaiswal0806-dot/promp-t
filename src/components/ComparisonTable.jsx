export function ComparisonTable({ headers, rows }) {
  if (!headers?.length || !rows?.length) return null;
  return (
    <div className="comparison-table-wrap">
      <table className="comparison-table">
        <thead>
          <tr>{headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}>
                  {cell === true ? <span className="check">✓</span> :
                   cell === false ? <span className="cross">✗</span> :
                   typeof cell === "string" && cell.startsWith("check:") ? <span className="check">{cell.slice(6)}</span> :
                   typeof cell === "string" && cell.startsWith("cross:") ? <span className="cross">{cell.slice(6)}</span> :
                   cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
