import { el, pageHeader, alertBox, field, input, showErrors, asyncButton, tag, fmtDate } from "../ui.js";
import { api, store } from "../api.js";

const SIM = "Simulation only \u2014 no government identity verification has taken place.";

export async function identityPage(ctx) {
  const head = pageHeader(["simulated"], "Digital identity verification", "A guided demonstration of how a person could establish one verified identity and later link several legitimate accounts to it.");
  const warn = alertBox("sim", SIM);
  const holder = el("div");
  const showStart = () => {
    const alias = input("alias", { max: 30 });
    const consent = el("input", { type: "checkbox", id: "consent", name: "consent" });
    const form = el("form", { class: "card", novalidate: true },
      el("h2", {}, "Start a demo verification"),
      el("p", {}, "This walks through the stages a real provider would run, using placeholder steps. You do not enter any ID number, photo or OTP."),
      field("alias", "Display alias (optional)", alias, "Any nickname. Do not type your real legal name or any ID number."),
      el("div", { class: "field", id: "f-consent" }, el("label", { for: "consent", class: "check" }, consent, " I understand this is a simulation. No government identity verification will take place and I will not enter any Aadhaar number, document or OTP.")),
      el("div", { class: "actions" }, el("button", { class: "btn", type: "submit" }, "Start demo verification")));
    form.addEventListener("submit", async (e) => {
      e.preventDefault(); showErrors(form, {});
      try { const r = await api.post("/api/identity/start", { alias: alias.value, consent: consent.checked }); store.identity = r.id; ctx.refreshIdentityChip(); showDone(r); }
      catch (err) { if (!showErrors(form, err.fields)) form.prepend(alertBox("bad", err.message)); }
    });
    holder.replaceChildren(form, el("div", { class: "card" }, el("h2", {}, "What a real deployment would need"),
      el("p", {}, "Real verification requires an authorised identity provider, explicit user consent and legal compliance (for example under the DPDP Act, 2023). Those parts are ", tag("future"))));
  };
  const showDone = (r) => {
    holder.replaceChildren(el("section", { class: "card accent" },
      el("div", {}, el("span", { class: "id-box" }, r.id), tag("simulated")),
      el("h2", {}, r.status), alertBox("sim", el("strong", {}, "Simulation only \u2014 no government identity verification has taken place. "), "This status is for demonstration only. Nothing was sent to Aadhaar, DigiLocker or any identity provider."),
      el("p", { class: "muted" }, `Created ${fmtDate(r.created_at)}${r.alias ? ` \u00b7 alias: ${r.alias}` : ""} \u00b7 linked accounts: ${r.account_count}`),
      el("h3", {}, "Verification steps (all simulated)"),
      el("ol", { class: "step-list" }, r.steps.map((s, i) => el("li", {}, el("span", { class: "step-no" }, i + 1), el("div", {}, el("strong", {}, s.step), el("div", { class: "muted" }, s.detail))))),
      el("div", { class: "two-col" },
        el("div", {}, el("h3", { class: "good" }, "A participating platform would see"), el("ul", { class: "clean" }, r.platform_sees.map((t) => el("li", {}, t)))),
        el("div", {}, el("h3", { class: "bad-h" }, "It would not see"), el("ul", { class: "clean" }, r.platform_does_not_see.map((t) => el("li", {}, t))))),
      el("p", {}, el("strong", {}, "Never collected by this prototype: "), r.never_collected.join(", "), "."),
      el("div", { class: "actions" }, el("a", { class: "btn", href: "#/accounts" }, "Link demo accounts"),
        el("button", { class: "btn ghost", type: "button", onclick: () => { store.identity = null; ctx.refreshIdentityChip(); showStart(); } }, "Start over"))));
  };
  if (store.identity) { try { showDone(await api.get(`/api/identity/${store.identity}`)); } catch { store.identity = null; showStart(); } } else showStart();
  return [...head, warn, holder];
}
