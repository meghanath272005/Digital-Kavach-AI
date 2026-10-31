import { el, pageHeader, alertBox, field, input, textarea, showErrors, loadingCard } from "../ui.js";
import { api, cached } from "../api.js";
import { profileResult } from "./shared.js";

export async function profilePage() {
  const samples = await cached("samples", "/api/samples");
  const f = {
    username: input("username", { max: 61 }), url: input("url", { max: 500, ph: "https://..." }),
    description: textarea("description", { max: 2000, rows: 3 }), notes: textarea("notes", { max: 2000, rows: 3 }),
    account_age_days: input("account_age_days", { type: "number", min: 0, mode: "numeric" }),
    followers: input("followers", { type: "number", min: 0, mode: "numeric" }), following: input("following", { type: "number", min: 0, mode: "numeric" }),
  };
  const result = el("div", { "aria-live": "polite" });
  const form = el("form", { class: "card", novalidate: true },
    el("div", { class: "row two" }, field("username", "Username", f.username), field("url", "Public profile URL", f.url, "Optional. Never opened by this tool.")),
    field("description", "Profile description (bio)", f.description, "Paste what the profile says about itself."),
    field("notes", "Supporting information (optional)", f.notes, "What happened? For example: asked me for money, copied my photos."),
    el("div", { class: "row" }, field("account_age_days", "Account age in days", f.account_age_days), field("followers", "Followers", f.followers), field("following", "Following", f.following)),
    el("div", { class: "actions" }, el("button", { class: "btn", type: "submit" }, "Check profile")));
  form.addEventListener("submit", async (e) => {
    e.preventDefault(); showErrors(form, {});
    const body = Object.fromEntries(Object.entries(f).map(([k, c]) => [k === "url" ? "url" : k, c.value]));
    result.replaceChildren(loadingCard("Applying the profile rules\u2026"));
    try { result.replaceChildren(profileResult(await api.post("/api/profile/check", body))); result.firstChild.scrollIntoView({ behavior: "smooth", block: "start" }); }
    catch (err) { result.replaceChildren(); if (!showErrors(form, err.fields)) result.append(alertBox("bad", err.message)); }
  });
  const load = (s) => { for (const k of Object.keys(f)) f[k].value = s[k] ?? ""; };
  return [...pageHeader(["rule"], "Fake profile risk checker", "Enter what you can see on a public profile. The checker applies fixed, published rules to your text only and explains every point it adds."),
    alertBox("warn", el("strong", {}, "Risk assessment is preliminary and may be incorrect. "), "A risk score never proves that a person is a criminal. This tool does not open links, scrape accounts or access any platform database."),
    el("div", { class: "samples" }, el("strong", {}, "Sample scenarios (demonstration data):"), samples.profile.map((s) => el("button", { class: "btn ghost small", type: "button", onclick: () => load(s) }, s.label))),
    form, result];
}
