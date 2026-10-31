import { el, alertBox, field, textarea, tag, loadingCard, tags } from "../ui.js";
import { icon } from "../icons.js";
import { api, cached, store } from "../api.js";
import { limitationsCard } from "./how.js";

const TOOLS = [
  ["identity", "id", "simulated", "Identity verification demo", "Walk through a clearly labelled sample verification. No real ID is used."],
  ["accounts", "link", "working", "Linked accounts demo", "See how personal, business and community accounts can share one verified identity privately."],
  ["profile", "profile", "rule", "Fake profile checker", "Check a username, link and bio for warning signs, with the reason for each."],
  ["image", "image", "working", "Deepfake and image analysis", "Upload an image for metadata and edit-trace checks. Not a deepfake detector."],
  ["scam", "scam", "rule", "Scam message detector", "Paste a suspicious SMS or chat message and see what looks wrong."],
  ["report", "flag", "working", "Impersonation reporting", "Prepare a report and get a reference ID. It is saved locally, not sent anywhere."],
  ["safety", "book", "working", "Cyber safety recommendations", "Plain advice on OTPs, links, payments and what to do after a fraud."],
  ["how", "info", null, "How the demo works", "The problem, the idea, and exactly what is real in this prototype."],
];

export async function dashboard() {
  const samples = await cached("samples", "/api/samples");
  const stats = await api.get("/api/dashboard/stats");
  const ta = textarea("quick", { max: 5000, rows: 4, ph: "Paste a suspicious message here" });
  const out = el("div", { "aria-live": "polite" });
  const run = async () => {
    out.replaceChildren(loadingCard("Checking\u2026"));
    try {
      const r = await api.post("/api/scam/check", { message: ta.value });
      out.replaceChildren(el("div", { class: "risk" }, el("span", { class: `risk-badge ${r.category}` }, `${r.category} risk`), el("span", { class: "muted" }, `${r.score} rule points`)),
        ...r.findings.filter((f) => f.points > 0).slice(0, 3).map((f) => el("article", { class: `finding ${f.severity}` }, el("div", { class: "finding-head" }, el("h3", {}, f.title), el("span", { class: "pts" }, `+${f.points} points`)), el("p", {}, f.explanation))),
        el("p", { class: "muted" }, el("a", { href: "#/scam" }, "Open the full detector"), " for every indicator and safety steps. Risk assessment is preliminary and may be incorrect. Rules mainly cover English and some Hinglish."));
    } catch (e) { out.replaceChildren(alertBox("bad", e.fields?.message || e.message)); }
  };
  const live = el("div", { class: "card" }, el("h3", {}, "Try it now: is this message a scam?"), el("p", { class: "muted" }, tag("rule"), " Runs the real rule checks. The text is not stored."),
    field("quick", "Message to check", ta),
    el("div", { class: "actions" }, el("button", { class: "btn", type: "button", onclick: run }, "Analyse message"), el("button", { class: "btn ghost", type: "button", onclick: () => { ta.value = samples.scam[0].text; run(); } }, "Use sample scam")), out);
  const hero = el("section", { class: "hero" }, el("div", {}, el("h1", {}, "Check before you trust."), el("p", { class: "tagline" }, "One Trusted Identity. Multiple Legitimate Accounts. Safer Digital India."),
    el("p", {}, "Digital Kavach AI is a student prototype that shows how verified identity, scam checks and impersonation reporting could fit into one safer social media experience. Every result tells you whether it came from real processing or a simulation.")), live);
  const stat = (n, l) => el("div", { class: "card stat" }, el("div", { class: "n" }, String(n)), el("div", { class: "l" }, l));
  const c = stats.checks_run;
  const refs = store.reports;
  return [hero,
    el("h2", {}, "Activity in this prototype"), el("p", { class: "muted" }, stats.source),
    el("div", { class: "grid cols-4" }, stat(stats.demo_identities, "Demo identities created"), stat(stats.linked_accounts, "Demo accounts linked"), stat(stats.reports_saved, "Reports saved locally"), stat(c.scam_messages + c.profiles + c.images, `Checks run (${c.scam_messages} scam, ${c.profiles} profile, ${c.images} image)`)),
    el("h2", {}, "Safety tools"),
    el("div", { class: "grid cols-3" }, TOOLS.map(([p, ic, kind, t, d]) => el("a", { class: "card tool", href: `#/${p}` }, el("div", { class: "top" }, el("span", { class: "ico" }, icon(ic)), kind ? tag(kind) : null), el("h3", {}, t), el("p", {}, d)))),
    el("h2", {}, "Recent report references"),
    el("section", { class: "card" }, refs.length ? [el("p", { class: "muted" }, "Reports made in this browser. Open one to see its demonstration status."), el("ul", { class: "chips" }, refs.map((r) => el("li", {}, el("a", { class: "chip", href: `#/report?ref=${encodeURIComponent(r)}` }, r))))] : el("p", { class: "muted" }, "No reports made in this browser yet. ", el("a", { href: "#/report" }, "Prepare one"), ".")),
    el("h2", {}, "Safety tips"),
    el("section", { class: "card" }, el("ul", { class: "clean" }, ["Never share an OTP or PIN. No bank, government office or delivery company will ask for it.", "Do not tap links in unexpected messages. Type the website address yourself.", "Before you act, ask: who is asking, am I being rushed, can I confirm another way?", "If money is lost, call 1930 straight away and report at cybercrime.gov.in."].map((t) => el("li", {}, t)))),
    el("h2", {}, "What the labels mean"),
    el("div", { class: "grid cols-4" }, [["working", "Real code runs on what you give it."], ["rule", "Real, published rules. No machine learning in this web app."], ["simulated", "Scripted walk-through using sample data."], ["future", "Planned. Not built yet."]].map(([k, t]) => el("div", { class: "card" }, tag(k), el("p", { class: "muted" }, t)))),
    ...limitationsCard()];
}
