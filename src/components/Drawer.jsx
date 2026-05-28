import { useState, useCallback, useRef, useEffect } from "react";
import React from "react";

export function Drawer({ tabs = [], defaultTab, defaultHeight = 200, children }) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id || "");
  const [height, setHeight] = useState(defaultHeight);
  const [dragging, setDragging] = useState(false);
  const drawerRef = useRef(null);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  useEffect(() => {
    if (!dragging) return;
    const handleMouseMove = (e) => {
      if (!drawerRef.current) return;
      const rect = drawerRef.current.getBoundingClientRect();
      const newHeight = Math.max(80, Math.min(600, rect.bottom - e.clientY));
      setHeight(newHeight);
    };
    const handleMouseUp = () => setDragging(false);
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => { document.removeEventListener("mousemove", handleMouseMove); document.removeEventListener("mouseup", handleMouseUp); };
  }, [dragging]);

  const tabContent = (() => {
    if (!children) return null;
    const arr = React.Children.toArray(children);
    const match = arr.find((c) => c?.props?.tabId === activeTab);
    return match || null;
  })();

  return (
    <div ref={drawerRef} className="drawer" style={{ height }}>
      <div className="drawer-handle" onMouseDown={handleMouseDown} title="Drag to resize">⋮</div>
      {tabs.length > 0 && (
        <div className="drawer-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`drawer-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}
      <div className="drawer-body">
        {tabContent}
      </div>
    </div>
  );
}
