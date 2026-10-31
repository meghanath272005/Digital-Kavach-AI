import { el, pageHeader, alertBox, field, input, textarea, select, showErrors, loadingCard, fmtDate, toast } from "../ui.js";
import { icon } from "../icons.js";
import { api, cached, store } from "../api.js";

const NOT_SENT = ["Your report is not sent anywhere. ", "This prototype does not submit reports to any social media platform or to law enforcement. To report for real, use the platform's own Report option and file a complaint at ", el("strong", {}, "cybercrime.gov.in"), " or call ", el("strong", {}, "1930"), "."];

export function statusCard(s, onChange) {
  const box = el("section", { class: "card accent", "aria-label": "Report status" });
  box.append(el("h3", {}, "Saved locally (demo)"), el("p", { class: "muted" }, `${s.reference_id} \u00b7 ${s.report_type} \u00b7 ${s.platform} \u00b7 ${fmtDate(s.created_at)}`));
  box.append(el("p", {}, el("strong", {}, "Current status: "), s.status));
  box.append(el("ol", { class: "timeline" }, s.timeline.map((t) => el("li", { class: t.reached ? "reached" : null }, el("span", { class: "dot" }, t.reached ? icon("check") : null),
    el("div", {}, el("strong", {}, t.status), el("small", {}, t.reached ? `${t.note}${t.at ? ` (${fmtDate(t.at)})` : ""}` : "Not reached"))))));
  if (s.can_simulate_next_step) box.append(el("button", { class: "btn ghost small", type: "button", onclick: async () => { try { onChange(await api.post(`/api/reports/${s.reference_id}/simulate-next`)); } catch (e) { toast(e.message); } } }, "Simulate next review step (demo only)"));
  box.append(el("p", { class: "must" }, s.notice));
  return box;
}

export async function reportPage() {
  const meta = await cached("meta", "/api/meta"), samples = await cached("samples", "/api/samples");
  const f = {
    reporter_name: input("reporter_name", { max: 80 }), contact: input("contact", { max: 120 }),
    username: input("username", { max: 121 }), platform: select("platform", meta.report_platforms, "Choose platform"),
    profile_url: input("profile_url", { max: 500, ph: "https://..." }), report_type: select("report_type", meta.report_types, "Choose one"),
    description: textarea("description", { max: 2000, rows: 4 }), evidence_description: textarea("evidence_description", { max: 2000, rows: 3 }),
  };
  const out = el("div", { "aria-live": "polite" }), lookupOut = el("div"), recent = el("div");
  const form = el("form", { class: "card", novalidate: true },
    el("div", { class: "row two" }, field("reporter_name", "Your name (optional)", f.reporter_name), field("contact", "Contact email or phone (optional)", f.contact, "Stored only in this local demo database.")),
    el("div", { class: "row two" }, field("username", "Impersonating username", f.username), field("platform", "Platform", f.platform)),
    field("profile_url", "Profile URL (optional)", f.profile_url, "Never opened by this tool."),
    field("report_type", "Type of suspected impersonation", f.report_type),
    field("description", "What happened?", f.description, "At least 20 characters. Do not include Aadhaar, card numbers, passwords or OTPs."),
    field("evidence_description", "Supporting evidence (optional)", f.evidence_description, "Describe or paste links to your screenshots. Files are not uploaded in this prototype."),
    el("div", { class: "actions" }, el("button", { class: "btn", type: "submit" }, "Submit report")));
  function drawRecent() {
    const refs = store.reports;
    recent.replaceChildren(refs.length ? el("div", {}, el("h3", {}, "Reports made in this browser"), el("ul", { class: "chips" }, refs.map((r) => el("li", {}, el("button", { class: "chip", type: "button", onclick: () => lookup(r) }, r))))) : el("p", { class: "muted" }, "No reports made in this browser yet."));
  }
  const showStatus = (s, target) => target.replaceChildren(statusCard(s, (n) => showStatus(n, target)));
  form.addEventListener("submit", async (e) => {
    e.preventDefault(); showErrors(form, {});
    out.replaceChildren(loadingCard("Validating and saving your report locally\u2026"));
    try {
      const body = Object.fromEntries(Object.entries(f).map(([k, c]) => [k, c.value]));
      const s = await api.post("/api/reports", body); store.addReport(s.reference_id); drawRecent();
      out.replaceChildren(alertBox("ok", s.message), el("button", { class: "ref-chip", type: "button", title: "Copy reference ID", onclick: () => { navigator.clipboard?.writeText(s.reference_id); toast("Reference ID copied."); } }, s.reference_id), el("div", { class: "spacer" }));
      const sc = el("div"); showStatus(s, sc); out.append(sc); out.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) { out.replaceChildren(); if (!showErrors(form, err.fields)) out.append(alertBox("bad", err.message)); }
  });
  const refIn = input("reference_id", { max: 40, ph: "DKA-20261029-XXXXXXXXXX" });
  async function lookup(ref) {
    refIn.value = ref; lookupOut.replaceChildren(loadingCard("Looking up the reference\u2026"));
    try { showStatus(await api.get(`/api/reports/${encodeURIComponent(ref)}`), lookupOut); }
    catch (e) { lookupOut.replaceChildren(alertBox("bad", e.fields?.reference_id || e.message)); }
  }
  const lookupForm = el("form", { class: "card", novalidate: true }, el("h2", {}, "Check a demonstration report status"),
    el("div", { class: "field" }, el("label", { for: "reference_id" }, "Reference ID"), refIn), el("div", { class: "actions" }, el("button", { class: "btn ghost", type: "submit" }, "Check status")), recent, lookupOut);
  lookupForm.addEventListener("submit", (e) => { e.preventDefault(); lookup(refIn.value.trim()); });
  drawRecent();
  const sample = el("button", { class: "btn ghost small", type: "button", onclick: () => { for (const k of Object.keys(f)) if (samples.report[k] !== undefined) f[k].value = samples.report[k]; toast("Sample report filled in."); } }, samples.report.label + " (demonstration data)");
  const hashRef = (location.hash.split("?ref=")[1] || "").trim();
  if (hashRef) lookup(decodeURIComponent(hashRef));
  return [...pageHeader(["working"], "Impersonation reporting", "Prepare a clear report and get a reference ID. Reports are validated and saved to this prototype's local database."),
    alertBox("bad", ...NOT_SENT), el("p", {}, el("strong", {}, "Sample: "), sample), form, out, lookupForm];
}
