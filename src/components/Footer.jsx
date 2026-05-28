import { navItems } from "../content/navigation.js";

export function Footer({ onNavigate }) {
  return (
    <footer className="footer" style={{ padding: "4rem 2rem 2rem", textAlign: "left", maxWidth: "1440px", margin: "0 auto", width: "100%", borderTop: "1px solid var(--line-strong)" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "2rem", marginBottom: "4rem" }}>
        <div>
          <strong style={{ color: "var(--text)", fontSize: "0.9rem", display: "block", marginBottom: "1rem" }}>Product</strong>
          <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <button type="button" onClick={() => onNavigate('home')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Home</button>
            <button type="button" onClick={() => onNavigate('workbench')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Workbench</button>
            <button type="button" onClick={() => onNavigate('platform')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Platform</button>
          </nav>
        </div>
        <div>
          <strong style={{ color: "var(--text)", fontSize: "0.9rem", display: "block", marginBottom: "1rem" }}>Resources</strong>
          <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <button type="button" onClick={() => onNavigate('docs')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Read Docs</button>
            <button type="button" style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Resourations</button>
            <button type="button" onClick={() => onNavigate('how-it-works')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>How it Works</button>
            <button type="button" style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Platform Stages</button>
            <button type="button" style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Compile modes</button>
          </nav>
        </div>
        <div>
          <strong style={{ color: "var(--text)", fontSize: "0.9rem", display: "block", marginBottom: "1rem" }}>Company</strong>
          <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <button type="button" onClick={() => onNavigate('use-cases')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Use Cases</button>
            <button type="button" onClick={() => onNavigate('api-reference')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>API</button>
            <button type="button" onClick={() => onNavigate('observability')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Observability</button>
            <button type="button" onClick={() => onNavigate('security')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Security</button>
            <button type="button" style={{ textAlign: "left", background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>Contact</button>
          </nav>
        </div>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
          <span style={{color: "var(--muted)", fontSize: "1rem", cursor: "pointer"}}>GitHub</span>
          <span style={{color: "var(--muted)", fontSize: "1rem", cursor: "pointer"}}>X</span>
          <span style={{color: "var(--muted)", fontSize: "1rem", cursor: "pointer"}}>YT</span>
          <span style={{color: "var(--muted)", fontSize: "1rem", cursor: "pointer"}}>IN</span>
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", borderTop: "1px solid var(--line)", paddingTop: "2rem", fontSize: "0.75rem", color: "var(--muted)" }}>
        <span>PromptCompiler Motion Homepage V2</span>
        <span>All rights reserved</span>
      </div>
    </footer>
  );
}
