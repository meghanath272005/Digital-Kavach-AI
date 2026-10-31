// All data comes from the backend REST API; nothing is hard-coded or faked in the browser.
export class ApiError extends Error {
  constructor(status, message, fields) { super(message); this.status = status; this.fields = fields || {}; }
}
async function call(method, path, body, headers = {}) {
  let res;
  try {
    res = await fetch(path, { method, headers: body instanceof Blob ? headers : { "Content-Type": "application/json", ...headers },
      body: body === undefined ? undefined : body instanceof Blob ? body : JSON.stringify(body) });
  } catch {
    throw new ApiError(0, "Could not reach the server. Check that the backend is running and try again.");
  }
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON */ }
  if (!res.ok) {
    const e = data?.error;
    throw new ApiError(res.status, e?.message || `Request failed (${res.status}).`, e?.fields);
  }
  return data;
}
export const api = {
  get: (p) => call("GET", p),
  post: (p, b = {}) => call("POST", p, b),
  patch: (p, b) => call("PATCH", p, b),
  del: (p) => call("DELETE", p),
  image: (blob) => call("POST", "/api/image/analyse", blob, { "Content-Type": blob.type || "application/octet-stream" }),
};
const memo = {};
export const cached = (key, p) => (memo[key] ||= api.get(p).catch((e) => { delete memo[key]; throw e; }));

// Browser-side convenience state only (the demo identity id and the report references made in this browser).
export const store = {
  get identity() { return localStorage.getItem("dka_identity"); },
  set identity(v) { v ? localStorage.setItem("dka_identity", v) : localStorage.removeItem("dka_identity"); },
  get reports() { try { return JSON.parse(localStorage.getItem("dka_reports") || "[]"); } catch { return []; } },
  addReport(ref) { const l = [ref, ...this.reports.filter((r) => r !== ref)].slice(0, 8); localStorage.setItem("dka_reports", JSON.stringify(l)); },
};
