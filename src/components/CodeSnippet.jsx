import { useState } from "react";

export function CodeSnippet({ code }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  };
  return (
    <span className="code-snippet">
      <code>{code}</code>
      <button className={`code-snippet-copy ${copied ? "copied" : ""}`} onClick={handleCopy} aria-label={copied ? "Copied" : "Copy to clipboard"} type="button">
        {copied ? "✓" : "⌘"}
      </button>
    </span>
  );
}
