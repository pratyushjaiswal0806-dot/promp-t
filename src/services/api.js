const BASE = "";

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : {}; } catch { data = { error: text || `HTTP ${res.status}` }; }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

export function getJson(url) { return request(url); }
export function postJson(url, payload) { return request(url, { method: "POST", body: JSON.stringify(payload) }); }
