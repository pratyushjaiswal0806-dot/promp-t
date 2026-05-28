import { useWorkbench } from "./context/CompilerContext.jsx";
import { DiffList } from "../components/DiffList.jsx";

export function Inspector() {
  const { segments, diffItems, semantic } = useWorkbench();
  return (
    <>
      {segments.length > 0 && (
        <div className="table-wrap" style={{ marginBottom: "0.75rem" }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Role</th>
                <th>Tokens</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {segments.slice(0, 20).map((seg) => (
                <tr key={seg.id}>
                  <td>{seg.id}</td>
                  <td>{seg.type}</td>
                  <td>{seg.role}</td>
                  <td>{String(seg.tokens)}</td>
                  <td>{seg.pinned ? "Pinned" : "Open"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {diffItems.length > 0 && <DiffList items={diffItems} />}
      {segments.length === 0 && diffItems.length === 0 && <div className="empty-state">Compile a prompt to see detailed inspection data.</div>}
    </>
  );
}
