import { useState } from "react";

export function EndpointCard({ method = "GET", path, description, requestSchema, responseSchema, example, statusCodes }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="endpoint-card">
      <div className="endpoint-card-header" onClick={() => setOpen(!open)} role="button" tabIndex={0} aria-expanded={open}>
        <span className={`endpoint-method ${method.toLowerCase()}`}>{method}</span>
        <span className="endpoint-path">{path}</span>
        <span className="endpoint-desc">{description}</span>
        <span className={`endpoint-expand-icon ${open ? "open" : ""}`}>▾</span>
      </div>
      {open && (
        <div className="endpoint-card-body">
          {requestSchema && (
            <>
              <h4>Request Body</h4>
              <pre>{requestSchema}</pre>
            </>
          )}
          {responseSchema && (
            <>
              <h4>Response Schema</h4>
              <pre>{responseSchema}</pre>
            </>
          )}
          {example && (
            <>
              <h4>Example</h4>
              <pre>{example}</pre>
            </>
          )}
          {statusCodes?.length > 0 && (
            <>
              <h4>Status Codes</h4>
              <table className="status-table">
                <thead><tr><th>Code</th><th>Description</th></tr></thead>
                <tbody>
                  {statusCodes.map((sc) => (
                    <tr key={sc.code}><td>{sc.code}</td><td>{sc.description}</td></tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}
    </div>
  );
}
