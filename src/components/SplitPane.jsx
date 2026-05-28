import { useRef, useState, useCallback, useEffect } from "react";

export function SplitPane({ left, right, defaultSize = "50%", direction = "horizontal" }) {
  const containerRef = useRef(null);
  const [splitPos, setSplitPos] = useState(null);
  const [dragging, setDragging] = useState(false);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  useEffect(() => {
    if (!dragging) return;
    const handleMouseMove = (e) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      if (direction === "horizontal") {
        const pct = ((e.clientX - rect.left) / rect.width) * 100;
        setSplitPos(Math.max(20, Math.min(80, pct)));
      } else {
        const pct = ((e.clientY - rect.top) / rect.height) * 100;
        setSplitPos(Math.max(20, Math.min(80, pct)));
      }
    };
    const handleMouseUp = () => setDragging(false);
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => { document.removeEventListener("mousemove", handleMouseMove); document.removeEventListener("mouseup", handleMouseUp); };
  }, [dragging, direction]);

  const pos = splitPos ?? (typeof defaultSize === "number" ? defaultSize : parseFloat(defaultSize) || 50);

  return (
    <div ref={containerRef} className={`split-pane ${direction}`} style={{ flex: 1 }}>
      <div className="split-pane-panel" style={direction === "horizontal" ? { width: `${pos}%` } : { height: `${pos}%` }}>
        {left}
      </div>
      <div className={`split-pane-divider ${dragging ? "active" : ""}`} onMouseDown={handleMouseDown} />
      <div className="split-pane-panel" style={{ flex: 1 }}>
        {right}
      </div>
    </div>
  );
}
