import { icon } from "./icons.js";
import { el, toast } from "./ui.js";
import { api, store } from "./api.js";
import { dashboard } from "./pages/dashboard.js";
import { identityPage } from "./pages/identity.js";
import { accountsPage } from "./pages/accounts.js";
import { profilePage } from "./pages/profile.js";
import { imagePage } from "./pages/image.js";
import { scamPage } from "./pages/scam.js";
import { reportPage } from "./pages/report.js";
import { safetyPage } from "./pages/safety.js";
import { howPage } from "./pages/how.js";
import { futurePage } from "./pages/future.js";

const ROUTES = [
  { path: "dashboard", label: "Dashboard", icon: "home", group: "Safety tools", page: dashboard },
  { path: "identity", label: "Digital identity", icon: "id", page: identityPage },
  { path: "accounts", label: "Linked accounts", icon: "link", page: accountsPage },
  { path: "profile", label: "Fake profile checker", icon: "profile", page: profilePage },
  { path: "image", label: "Image analysis", icon: "image", page: imagePage },
  { path: "scam", label: "Scam message detector", icon: "scam", page: scamPage },
  { path: "report", label: "Report impersonation", icon: "flag", page: reportPage },
  { path: "safety", label: "Safety recommendations", icon: "book", group: "Learn", page: safetyPage },
  { path: "how", label: "How the demo works", icon: "info", page: howPage },
  { path: "future", label: "Future development", icon: "rocket", page: futurePage },
];
const sidebar = document.getElementById("sidebar");
const scrim = document.getElementById("scrim");
const menuBtn = document.getElementById("menuBtn");
menuBtn.append(icon("menu"));

function buildNav() {
  const box = document.getElementById("navLinks");
  box.replaceChildren();
  for (const r of ROUTES) {
    if (r.group) box.append(el("div", { class: "nav-group" }, r.group));
    box.append(el("a", { class: "nav-link", href: `#/${r.path}`, "data-route": r.path }, icon(r.icon), el("span", {}, r.label)));
  }
}
function setMenu(open) {
  sidebar.classList.toggle("open", open);
  scrim.hidden = !open;
  menuBtn.setAttribute("aria-expanded", String(open));
  if (open) sidebar.querySelector("a")?.focus(); else if (window.matchMedia("(max-width:980px)").matches) menuBtn.focus({ preventScroll: true });
}
menuBtn.addEventListener("click", () => setMenu(!sidebar.classList.contains("open")));
scrim.addEventListener("click", () => setMenu(false));
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && sidebar.classList.contains("open")) setMenu(false); });

export async function refreshIdentityChip() {
  const chip = document.getElementById("identityChip");
  const id = store.identity;
  if (id) {
    try { await api.get(`/api/identity/${id}`); chip.replaceChildren("Demo identity (simulation)", el("b", {}, id)); return; }
    catch (e) { if (e.status === 404) store.identity = null; }
  }
  chip.replaceChildren("No demo identity yet. Start one on the Digital identity page.");
}

async function render() {
  const path = (location.hash.replace(/^#\//, "") || "dashboard").split("?")[0];
  const route = ROUTES.find((r) => r.path === path) || ROUTES[0];
  document.querySelectorAll(".nav-link").forEach((a) => (a.dataset.route === route.path ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
  document.title = `${route.label} - Digital Kavach AI`;
  const view = document.getElementById("view");
  view.replaceChildren();
  try { view.append(...[].concat(await route.page({ refreshIdentityChip, toast }))); }
  catch (e) { view.append(el("div", { class: "alert bad", role: "alert" }, e.message || "This page could not load.")); }
  setMenu(false);
  window.scrollTo(0, 0);
  document.getElementById("main").focus({ preventScroll: true });
}
buildNav();
window.addEventListener("hashchange", render);
render();
refreshIdentityChip();
