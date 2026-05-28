import { useState } from "react";

export function TabPanel({ tabs = [], defaultTab, children }) {
  const [active, setActive] = useState(defaultTab || tabs[0]?.id || "");

  const activeChild = Array.isArray(children)
    ? children.find((c) => c?.props?.tabId === active)
    : children;

  return (
    <div className="tab-panel">
      <div className="tab-list" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-trigger ${active === tab.id ? "active" : ""}`}
            onClick={() => setActive(tab.id)}
            role="tab"
            aria-selected={active === tab.id}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tab-content" role="tabpanel">
        {activeChild}
      </div>
    </div>
  );
}
