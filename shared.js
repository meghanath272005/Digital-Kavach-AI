import { el, alertBox } from "../ui.js";

export function riskHeader(category, score, thresholds, extra) {
  return el("div", { class: "risk" },
    el("span", { class: `risk-badge ${category}` }, `${category} risk`),
    score != null ? el("span", { class: "muted" }, `${score} rule points (Low ${thresholds.low}, Medium ${thresholds.medium}, High ${thresholds.high.replace(" and above", "+")})`) : null, extra);
}
export const bullets = (items) => el("ul", { class: "clean" }, items.map((t) => el("li", {}, t)));
export const methodBox = (summary, extra = []) => el("div", { class: "method" }, el("strong", {}, "How this was assessed: "), summary, ...extra);

function ruleFinding(f, textKey) {
  return el("article", { class: `finding ${f.severity}` },
    el("div", { class: "finding-head" }, el("h3", {}, f.title), el("span", { class: "pts" }, f.points > 0 ? `+${f.points} points` : "info, 0 points")),
    el("p", {}, f[textKey]),
    f.evidence?.length ? el("div", { class: "matched" }, "Matched: ", f.evidence.map((e) => [el("code", {}, e), " "])) : null);
}

export function scamResult(r) {
  const out = el("section", { class: "card accent", "aria-label": "Scam check result" });
  out.append(riskHeader(r.category, r.score, r.thresholds));
  if (r.ml_raised_category) out.append(alertBox("warn", "The ML score raised this message from Low to Medium. ML alone can never make a message High."));
  out.append(el("h2", {}, "Detected warning signs"));
  const flagged = r.findings.filter((f) => f.points > 0), notes = r.findings.filter((f) => f.points === 0);
  if (!flagged.length) out.append(el("p", {}, "No rule matched this message. That does not prove it is safe."));
  flagged.forEach((f) => out.append(ruleFinding(f, "explanation")));
  notes.forEach((f) => out.append(ruleFinding(f, "explanation")));
  if (r.links.length) {
    out.append(el("h2", {}, "Links found (shown disarmed, never opened)"),
      el("div", { class: "table-wrap" }, el("table", {}, el("thead", {}, el("tr", {}, el("th", {}, "Link"), el("th", {}, "Observations from the text of the link"))),
        el("tbody", {}, r.links.map((l) => el("tr", {}, el("td", {}, el("code", {}, l.display)), el("td", {}, l.reasons.length ? l.reasons.join("; ") : "No technical red flags in the text of the link.")))))));
  }
  out.append(el("h2", {}, "ML prediction"));
  if (r.ml.available) out.append(el("p", {}, `Model output: ${r.ml.label} (model score ${r.ml.probability}). `, r.ml.note));
  else out.append(el("p", { class: "muted" }, r.ml.note));
  out.append(el("h2", {}, "Recommended safety actions"), bullets(r.recommendations));
  out.append(methodBox(r.method.summary, [` ML or LLM used: ${r.method.ml_or_llm_used ? "ML model only (advisory)" : "no"}.`, bullets(r.limitations)]));
  out.append(el("p", { class: "must" }, r.disclaimer));
  return out;
}

export function profileResult(r) {
  const out = el("section", { class: "card accent", "aria-label": "Profile check result" });
  out.append(riskHeader(r.category, r.score, r.thresholds));
  if (r.limited_information) out.append(alertBox("warn", "Too little information was entered to judge this profile, so the result is Inconclusive. Add more details for a better check."));
  out.append(el("h2", {}, "Potential warning signs"));
  if (!r.findings.length) out.append(el("p", {}, "No warning-sign rule matched the information you entered."));
  r.findings.forEach((f) => out.append(ruleFinding({ ...f, evidence: null }, "detail")));
  if (r.checks_passed?.length) out.append(el("h2", {}, "Checks passed"), el("ul", { class: "clean passed" }, r.checks_passed.map((t) => el("li", {}, t))));
  out.append(el("h2", {}, "Safety recommendations"), bullets(r.recommendations));
  out.append(methodBox(r.method.summary, [` ML or LLM used: ${r.method.ml_or_llm_used ? "yes" : "no"}.`]));
  out.append(el("p", { class: "must" }, r.disclaimer));
  return out;
}

const dd = (k, v) => [el("dt", {}, k), el("dd", {}, v)];
export function imageResult(r, originalUrl) {
  const out = el("section", { class: "card accent", "aria-label": "Image analysis result" });
  out.append(el("div", { class: "risk" }, el("span", { class: `risk-badge ${r.verdict === "Indicators found" ? "High" : "Inconclusive"}` }, r.verdict)), el("p", {}, r.summary));
  const pair = el("div", { class: "img-pair" },
    el("figure", {}, el("img", { src: originalUrl, alt: "The image you analysed" }), el("figcaption", {}, "Your image")));
  if (r.ela_heatmap) pair.append(el("figure", {}, el("img", { src: r.ela_heatmap, alt: "Error Level Analysis heat map" }),
    el("figcaption", {}, "Error Level Analysis map. Brighter areas recompress differently. This is a visual aid, not proof; textured areas and sharp edges also glow.")));
  out.append(pair, el("h2", {}, "What the checks found"));
  r.findings.forEach((f) => out.append(el("article", { class: `finding ${f.level}` }, el("div", { class: "finding-head" }, el("h3", {}, f.title), el("span", { class: "pts" }, f.level)), el("p", {}, f.detail))));
  const m = r.measurements;
  out.append(el("h2", {}, "Measurements"), el("dl", { class: "dl" },
    dd("Format", `${m.format}, ${m.width} x ${m.height} px (${m.megapixels} MP), ${m.file_size_kb} KB`),
    dd("Camera metadata", m.exif_present ? `EXIF present${m.camera ? `, camera: ${m.camera}` : ", no camera model"}` : "No EXIF metadata"),
    dd("Software tag", m.software_tag || "None"),
    dd("Face regions located", m.face_detector_available === false ? "Detector unavailable" : String(m.faces_detected)),
    m.ela ? dd("ELA (mean / peak-to-typical ratio)", `${m.ela.global_mean} / ${m.ela.ratio}`) : null,
    dd("SHA-256 fingerprint", el("code", {}, m.sha256))));
  out.append(el("h2", {}, "Safety guidance"), bullets(r.guidance));
  out.append(el("div", { class: "method" }, el("strong", {}, "Method: "), `${r.method.type} using ${r.method.libraries.join(", ")}. Deepfake model used: no. Not performed: ${r.method.not_performed.join("; ")}. The image was not stored.`));
  out.append(el("p", { class: "must" }, r.disclaimer));
  return out;
}
