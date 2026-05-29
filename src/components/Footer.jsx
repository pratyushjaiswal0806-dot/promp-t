import { navItems } from "../content/navigation.js";

export function Footer({ onNavigate }) {
  return (
    <footer className="footer" style={{ padding: "6rem 2rem 3rem", textAlign: "left", maxWidth: "1200px", margin: "0 auto", width: "100%", borderTop: "4px solid var(--text)" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "3rem", marginBottom: "4rem" }}>
        <div>
          <strong style={{ color: "var(--text)", fontSize: "1.1rem", display: "block", marginBottom: "1.5rem", fontFamily: "var(--font-serif)", fontWeight: "900", textTransform: "uppercase" }}>Product</strong>
          <nav style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <button type="button" onClick={() => onNavigate('home')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>Home</button>
            <button type="button" onClick={() => onNavigate('workbench')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>Workbench</button>
            <button type="button" onClick={() => onNavigate('platform')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>Platform</button>
          </nav>
        </div>
        <div>
          <strong style={{ color: "var(--text)", fontSize: "1.1rem", display: "block", marginBottom: "1.5rem", fontFamily: "var(--font-serif)", fontWeight: "900", textTransform: "uppercase" }}>Resources</strong>
          <nav style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <button type="button" onClick={() => onNavigate('docs')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>Read Docs</button>
            <button type="button" onClick={() => onNavigate('how-it-works')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>How it Works</button>
          </nav>
        </div>
        <div>
          <strong style={{ color: "var(--text)", fontSize: "1.1rem", display: "block", marginBottom: "1.5rem", fontFamily: "var(--font-serif)", fontWeight: "900", textTransform: "uppercase" }}>Company</strong>
          <nav style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <button type="button" onClick={() => onNavigate('use-cases')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>Use Cases</button>
            <button type="button" onClick={() => onNavigate('api-reference')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>API</button>
            <button type="button" onClick={() => onNavigate('observability')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>Observability</button>
            <button type="button" onClick={() => onNavigate('security')} style={{ textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", fontSize: "0.9rem", padding: 0, fontFamily: "var(--font-mono)" }}>Security</button>
          </nav>
        </div>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end", alignItems: "flex-start" }}>
          <span style={{color: "var(--text)", fontSize: "1rem", cursor: "pointer", fontFamily: "var(--font-mono)", fontWeight: "bold", border: "2px solid var(--text)", padding: "0.25rem 0.5rem"}}>GH</span>
          <span style={{color: "var(--text)", fontSize: "1rem", cursor: "pointer", fontFamily: "var(--font-mono)", fontWeight: "bold", border: "2px solid var(--text)", padding: "0.25rem 0.5rem"}}>X</span>
          <span style={{color: "var(--text)", fontSize: "1rem", cursor: "pointer", fontFamily: "var(--font-mono)", fontWeight: "bold", border: "2px solid var(--text)", padding: "0.25rem 0.5rem"}}>YT</span>
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", borderTop: "2px solid var(--text)", paddingTop: "2rem", fontSize: "0.8rem", color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
        <span>PromptCompiler Brutalist Zine Homepage V3</span>
        <span>All rights reserved</span>
      </div>
    </footer>
  );
}
