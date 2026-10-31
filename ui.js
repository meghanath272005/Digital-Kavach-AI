// DOM helpers. Everything is built with textContent / createElement so user-supplied text can never become markup.
import { icon } from "./icons.js";

export function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === "class") n.className = v;
    else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2), v);
    else if (k === "text") n.textContent = v;
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return n;
}

export const LABELS = {
  working: "Working feature", rule: "Rule-based demo", simulated: "Simulated workflow", future: "Future development",
};
export const tag = (kind) => el("span", { class: `tag ${kind}` }, LABELS[kind]);
export const tags = (...kinds) => el("div", { class: "tags" }, kinds.map(tag));

export function pageHeader(kinds, title, lede) {
  return [kinds.length ? tags(...kinds) : null, el("h1", {}, title), lede ? el("p", { class: "lede" }, lede) : null];
}
export function alertBox(kind, ...kids) {
  return el("div", { class: `alert ${kind}`, role: kind === "bad" ? "alert" : null }, icon(kind === "ok" || kind === "info" ? "info" : "alert"), el("div", {}, kids));
}
export const spinner = () => el("span", { class: "spinner", "aria-hidden": "true" });
export const loadingCard = (text) => el("div", { class: "card loading-card", role: "status" }, spinner(), el("span", {}, text));

let toastTimer;
export function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), 2600);
}

export function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d) ? iso : d.toLocaleString();
}

/** Button that shows a spinner and disables itself while `fn` runs. */
export function asyncButton(label, fn, cls = "btn") {
  const b = el("button", { class: cls, type: "button" }, label);
  b.addEventListener("click", async () => {
    if (b.disabled) return;
    b.disabled = true;
    b.replaceChildren(spinner(), "Working\u2026");
    try { await fn(); } finally { b.disabled = false; b.replaceChildren(label); }
  });
  return b;
}

/** Labelled form field with an error slot. */
export function field(id, label, control, hint) {
  const wrap = el("div", { class: "field", id: `f-${id}` });
  wrap.append(el("label", { for: id }, label));
  if (hint) wrap.append(el("span", { class: "hint", id: `${id}-hint` }, hint));
  wrap.append(control);
  return wrap;
}
export function showErrors(form, fields) {
  form.querySelectorAll(".field").forEach((f) => { f.classList.remove("invalid"); f.querySelector(".err")?.remove(); });
  let first = null;
  for (const [k, msg] of Object.entries(fields || {})) {
    const f = form.querySelector(`#f-${k}`);
    if (!f) continue;
    f.classList.add("invalid");
    f.append(el("p", { class: "err", id: `${k}-err`, role: "alert" }, msg));
    const c = f.querySelector("input,select,textarea");
    c?.setAttribute("aria-invalid", "true"); c?.setAttribute("aria-describedby", `${k}-err`);
    first = first || c;
  }
  first?.focus();
  return Object.keys(fields || {}).length > 0;
}
export const input = (id, o = {}) => el("input", { id, name: id, type: o.type || "text", autocomplete: "off", maxlength: o.max, placeholder: o.ph, min: o.min, inputmode: o.mode });
export const textarea = (id, o = {}) => el("textarea", { id, name: id, maxlength: o.max, rows: o.rows || 4, placeholder: o.ph });
export function select(id, options, placeholder) {
  const s = el("select", { id, name: id });
  if (placeholder) s.append(el("option", { value: "" }, placeholder));
  for (const o of options) { const [v, l] = Array.isArray(o) ? o : [o, o]; s.append(el("option", { value: v }, l)); }
  return s;
}
