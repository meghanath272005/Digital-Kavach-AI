import { el, pageHeader, alertBox, field, select, input, showErrors, tag, fmtDate, toast } from "../ui.js";
import { api, cached, store } from "../api.js";

export async function accountsPage(ctx) {
  const head = pageHeader(["working", "simulated"], "Linked accounts demonstration", "One verified identity, several legitimate accounts. Each platform receives a different pseudonymous token, so the accounts cannot be matched to each other or to a legal name.");
  const warn = alertBox("sim", el("strong", {}, "Simulation only \u2014 no government identity verification has taken place. "), "The identity is a demo. The token calculation (HMAC-SHA256) is real code; the verification behind it is not.");
  if (!store.identity) return [...head, warn, el("div", { class: "card" }, el("p", {}, "Start a demo identity first, then come back to link accounts."), el("a", { class: "btn", href: "#/identity" }, "Go to Digital identity"))];
  const iid = store.identity, meta = await cached("meta", "/api/meta"), samples = await cached("samples", "/api/samples");
  const cat = select("category", Object.entries(meta.categories)), plat = select("platform", meta.platforms), handle = input("handle", { max: 61 });
  const listBox = el("div"), detail = el("div");
  const form = el("form", { class: "card", novalidate: true }, el("h2", {}, "Add an account"),
    el("div", { class: "row" }, field("category", "Used for", cat), field("platform", "Platform", plat), field("handle", "Handle", handle, "Use a made-up demo handle")),
    el("div", { class: "actions" }, el("button", { class: "btn", type: "submit" }, "Link account"),
      el("button", { class: "btn ghost", type: "button", onclick: async () => {
        let added = 0;
        for (const a of samples.accounts) { try { await api.post(`/api/identity/${iid}/accounts`, a); added++; } catch { /* already linked */ } }
        toast(added ? "Sample scenario loaded." : "Sample accounts are already linked."); load();
      } }, "Load 5 sample accounts (demonstration data)")));
  form.addEventListener("submit", async (e) => {
    e.preventDefault(); showErrors(form, {});
    try { await api.post(`/api/identity/${iid}/accounts`, { category: cat.value, platform: plat.value, handle: handle.value }); handle.value = ""; toast("Account linked."); load(); }
    catch (err) { if (!showErrors(form, err.status === 409 ? { handle: err.message } : err.fields)) toast(err.message); }
  });
  async function load() {
    let accounts;
    try { accounts = (await api.get(`/api/identity/${iid}/accounts`)).accounts; } catch (e) { listBox.replaceChildren(alertBox("bad", e.message)); return; }
    const card = el("section", { class: "card" }, el("h2", {}, `Accounts linked to ${iid} (${accounts.length})`));
    if (!accounts.length) card.append(el("p", { class: "muted" }, "No accounts linked yet. Add one above or load the sample accounts."));
    for (const [key, label] of Object.entries(meta.categories)) {
      const group = accounts.filter((a) => a.category === key);
      if (!group.length) continue;
      card.append(el("h3", {}, label));
      group.forEach((a) => card.append(el("div", { class: "account" },
        el("div", { class: "meta" }, el("strong", {}, a.platform), ` \u00b7 @${a.handle} `, el("span", { class: "muted" }, `(${a.status})`), el("div", { class: "muted" }, "Token this platform would receive:"), el("span", { class: "token" }, a.pseudonym)),
        el("div", { class: "btns" },
          el("button", { class: "btn ghost small", type: "button", onclick: () => view(a.id) }, "View"),
          el("button", { class: "btn ghost small", type: "button", onclick: async () => { await api.patch(`/api/identity/${iid}/accounts/${a.id}`, { status: a.status.startsWith("Active") ? "Paused (demo)" : "Active (demo)" }); load(); } }, a.status.startsWith("Active") ? "Pause" : "Activate"),
          el("button", { class: "btn danger small", type: "button", "aria-label": `Remove ${a.platform} account ${a.handle}`, onclick: async () => { await api.del(`/api/identity/${iid}/accounts/${a.id}`); detail.replaceChildren(); toast("Account removed."); load(); } }, "Remove")))));
    }
    listBox.replaceChildren(card);
  }
  async function view(id) {
    const a = await api.get(`/api/identity/${iid}/accounts/${id}`);
    detail.replaceChildren(el("section", { class: "card accent" }, el("h2", {}, `${a.platform} \u00b7 @${a.handle}`),
      el("dl", { class: "dl" }, el("dt", {}, "Used for"), el("dd", {}, a.category_label), el("dt", {}, "Status"), el("dd", {}, a.status), el("dt", {}, "Linked on"), el("dd", {}, fmtDate(a.created_at)), el("dt", {}, "Pseudonymous token"), el("dd", {}, el("span", { class: "token" }, a.pseudonym))),
      el("p", { class: "muted" }, "The token is HMAC-SHA256(per-identity secret, platform + handle). The platform never learns your legal name or ID.")));
    detail.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  await load();
  return [...head, warn, form, listBox, detail, el("section", { class: "card" }, el("h2", {}, "What each side can see"),
    el("div", { class: "two-col" }, el("div", {}, el("h3", { class: "good" }, "Platform"), el("ul", { class: "clean" }, el("li", {}, "A per-platform pseudonymous token (pid_...)"), el("li", {}, "A 'demo-verified person' flag"))),
      el("div", {}, el("h3", { class: "bad-h" }, "Not shared"), el("ul", { class: "clean" }, el("li", {}, "Legal name"), el("li", {}, "Aadhaar or any ID number"), el("li", {}, "Your other accounts on other platforms")))),
    el("p", {}, "The same person gets a different token on every platform and for every handle. Multiple legitimate accounts are allowed; the goal is to make impersonating someone harder, not to limit real users."),
    el("p", {}, tag("future"), " Real linking would need participating platforms and an authorised verification provider."))];
}
