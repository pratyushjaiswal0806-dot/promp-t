import { navItems } from "../content/navigation.js";
import { ThemeToggle } from "./ThemeToggle.jsx";

export function Topbar({ activePage, onNavigate, status }) {
  return (
    <header className="topbar" aria-label="PromptCompiler navigation">
      <div className="topbar-left">
        <button className="brand-lockup" type="button" onClick={() => onNavigate("home")} aria-label="PromptCompiler home">
          <strong className="brand-title">PromptCompiler</strong>
        </button>
        <span className={`status-chip ${status?.className || ""}`}>
          {status?.text || "Initializing"}
        </span>
        <ThemeToggle />
      </div>
      <nav className="topnav" aria-label="Page sections">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={activePage === item.id ? "active" : ""}
            type="button"
            data-page-target={item.id}
            data-page-path={item.href}
            aria-current={activePage === item.id ? "page" : undefined}
            onClick={() => onNavigate(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
