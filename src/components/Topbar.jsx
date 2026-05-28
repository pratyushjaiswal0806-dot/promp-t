import { navItems } from "../content/navigation.js";
import { ThemeToggle } from "./ThemeToggle.jsx";

export function Topbar({ activePage, onNavigate, status }) {
  return (
    <header className="topbar" aria-label="PromptCompiler navigation" style={{ justifyContent: "space-between", borderBottom: "none" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <button className="brand-lockup" type="button" onClick={() => onNavigate("home")} aria-label="PromptCompiler home" style={{ gap: "0.5rem" }}>
          <strong className="brand-title" style={{ fontSize: "1.2rem", fontWeight: "600" }}>PromptCompiler</strong>
        </button>
        <span className={`status-chip ${status?.className || ""}`} style={{ background: "rgba(199,248,90,0.1)", border: "1px solid rgba(199,248,90,0.3)", borderRadius: "999px" }}>
          {status?.text || "Initializing"}
        </span>
        <ThemeToggle />
      </div>
      <nav className="topnav" aria-label="Page sections" style={{ flex: "none", gap: "1rem" }}>
        {navItems.map((item) => (
          <button
            key={item.id}
            className={activePage === item.id ? "active" : ""}
            type="button"
            aria-current={activePage === item.id ? "page" : undefined}
            onClick={() => onNavigate(item.id)}
            style={{ fontSize: "0.85rem", padding: 0 }}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
