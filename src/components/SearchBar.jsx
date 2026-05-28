import { useRef } from "react";

export function SearchBar({ value, onChange, placeholder = "Search..." }) {
  const ref = useRef(null);
  return (
    <div className="search-bar-wrap">
      <span className="search-bar-icon">⌕</span>
      <input
        ref={ref}
        className="search-bar-input"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
      />
      <span className="search-bar-hint" aria-hidden>⌘K</span>
    </div>
  );
}
