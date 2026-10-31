// Small inline icon set (Lucide-style 24x24 strokes). lucide-react could not be installed offline.
const P = {
  home: '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
  id: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M6 16c.5-1.5 1.7-2 3-2s2.5.5 3 2M15 10h3M15 14h3"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  profile: '<circle cx="9" cy="8" r="3.5"/><path d="M3 20c.6-3.5 3-5.5 6-5.5"/><circle cx="17" cy="16" r="3"/><path d="M19.2 18.2 21 20"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="m4 18 5-5 4 4 3-3 4 4"/>',
  scam: '<path d="M4 5h16v11H9l-5 4z"/><path d="M12 8.5v3.2M12 13.8v.1"/>',
  flag: '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
  book: '<path d="M3 5.5C5 4.5 8 4.5 12 6.5c4-2 7-2 9-1V19c-2-1-5-1-9 1-4-2-7-2-9-1z"/><path d="M12 6.5V20"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.1"/>',
  rocket: '<path d="M5 15c-1.5 1-2 3.5-2 5 1.5 0 4-.5 5-2"/><path d="M9 15 6 12c1-4 4-7 11-8 1 0 3 0 3 0 0 7-3 11-8 12z"/><circle cx="15" cy="9" r="1.4"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  alert: '<path d="M12 3 2 20h20z"/><path d="M12 10v4.5M12 17.5v.1"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v4h16v-4"/>',
  check: '<path d="m5 12 4.5 4.5L19 7"/>',
  arrow: '<path d="M12 4v14M6 13l6 6 6-6"/>',
};
export function icon(name, cls = "") {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("viewBox", "0 0 24 24");
  s.setAttribute("fill", "none");
  s.setAttribute("stroke", "currentColor");
  s.setAttribute("stroke-width", "1.8");
  s.setAttribute("stroke-linecap", "round");
  s.setAttribute("stroke-linejoin", "round");
  s.setAttribute("aria-hidden", "true");
  if (cls) s.setAttribute("class", cls);
  s.innerHTML = P[name] || P.info;
  return s;
}
