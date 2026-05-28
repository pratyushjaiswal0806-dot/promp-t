import { useState } from "react";

export function Accordion({ items }) {
  const [openIdx, setOpenIdx] = useState(null);
  if (!items?.length) return null;
  return (
    <div className="accordion">
      {items.map((item, i) => {
        const isOpen = openIdx === i;
        return (
          <div key={item.title || i}>
            <button
              className={`accordion-trigger ${isOpen ? "open" : ""}`}
              onClick={() => setOpenIdx(isOpen ? null : i)}
              aria-expanded={isOpen}
              type="button"
            >
              <span>{item.title}</span>
              <span className={`accordion-icon ${isOpen ? "open" : ""}`}>▾</span>
            </button>
            {isOpen && (
              <div className="accordion-content">
                {typeof item.body === "string" ? <p>{item.body}</p> : item.body}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
