const KEY = "promptcompiler.history.v1";

export function readHistory() {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch { return []; }
}

export function saveToHistory(item) {
  const next = [item, ...readHistory()].slice(0, 8);
  try { localStorage.setItem(KEY, JSON.stringify(next)); } catch { /* quota */ }
  return next;
}

export function clearHistory() {
  try { localStorage.removeItem(KEY); } catch { /* */ }
}
