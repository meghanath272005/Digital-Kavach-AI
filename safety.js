import { el, pageHeader, alertBox } from "../ui.js";
import { cached } from "../api.js";

export async function safetyPage() {
  const d = await cached("reco", "/api/recommendations");
  const h = d.helpline;
  return [...pageHeader(["working"], "Cyber safety recommendations", "Plain advice to use before, during and after something looks suspicious."),
    alertBox("info", el("strong", {}, "Real help: "), `National Cyber Crime Helpline `, el("strong", {}, h.number), " and ", el("a", { href: h.portal, rel: "noopener noreferrer", target: "_blank" }, "cybercrime.gov.in"), `. ${h.text.replace(/^.*?Ministry of Home Affairs\)\.\s*/, "")}`),
    ...d.sections.map((s, i) => el("details", { class: "acc", open: i === 0 }, el("summary", {}, s.title), el("div", { class: "body" }, el("ul", { class: "clean" }, s.items.map((t) => el("li", {}, t)))))),
    el("section", { class: "card" }, el("h2", {}, "A quick check before you act"), el("ul", { class: "clean" }, d.quick_check.map((t) => el("li", {}, t))))];
}
