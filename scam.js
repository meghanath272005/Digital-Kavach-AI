import { el, pageHeader, alertBox, field, textarea, showErrors, asyncButton, loadingCard, tag } from "../ui.js";
import { api, cached } from "../api.js";
import { scamResult } from "./shared.js";

export async function scamPage() {
  const samples = await cached("samples", "/api/samples");
  const stats = await api.get("/api/health");
  const ta = textarea("message", { max: 5000, rows: 6, ph: "Paste a suspicious SMS, WhatsApp or email message here" });
  const count = el("div", { class: "counter" }, "0 / 5000");
  const result = el("div", { "aria-live": "polite" });
  ta.addEventListener("input", () => (count.textContent = `${ta.value.length} / 5000`));
  const form = el("form", { class: "card", novalidate: true });
  const run = async () => {
    showErrors(form, {});
    result.replaceChildren(loadingCard("Analysing the message text\u2026"));
    try { result.replaceChildren(scamResult(await api.post("/api/scam/check", { message: ta.value }))); result.firstChild.scrollIntoView({ behavior: "smooth", block: "start" }); }
    catch (e) { result.replaceChildren(); if (!showErrors(form, e.fields)) result.append(alertBox("bad", e.message)); }
  };
  form.addEventListener("submit", (e) => { e.preventDefault(); run(); });
  const btn = el("button", { class: "btn", type: "submit" }, "Analyse message");
  form.append(field("message", "Message text", ta), count, el("div", { class: "actions" }, btn));
  const sampleRow = el("div", { class: "samples" }, el("strong", {}, "Sample messages (demonstration data):"),
    samples.scam.map((s) => el("button", { class: "btn ghost small", type: "button", onclick: () => { ta.value = s.text; ta.dispatchEvent(new Event("input")); ta.focus(); } }, s.label)));
  return [...pageHeader(["rule"], "Scam message detector", "Paste a suspicious SMS, WhatsApp or email text. The detector looks for known scam patterns and explains each one."),
    alertBox("warn", el("strong", {}, stats.ml_model_loaded ? "Rules decide; ML is advisory. " : "This is rule-based detection, not AI. "),
      stats.ml_model_loaded ? "A trained model adds an advisory score but can never make a message High. " : "No machine-learning model or LLM reads your message in this web app. ",
      "Links are only described as text and ", el("strong", {}, "never opened"), ". Risk assessment is preliminary and may be incorrect."),
    sampleRow, form, result];
}
