import { el, pageHeader, tag } from "../ui.js";
import { icon } from "../icons.js";
import { api } from "../api.js";

export function limitationsCard() {
  const L = [
    ["No real identity verification.", "Nothing contacts Aadhaar, DigiLocker or any identity provider. The verification flow is a scripted simulation on placeholder data."],
    ["No live social-media access.", "The profile checker reads only text you type; it cannot see platform data and never opens links."],
    ["No deepfake detection model.", "Image analysis uses classic metadata and compression checks and can miss skilled edits or flag harmless photos."],
    ["Rule-based text checks.", "Scam and profile checks use fixed rules, mainly for English and some Hinglish. They produce false alarms and misses. Any ML model comes only from the Colab notebook and is advisory."],
    ["Reports stay local.", "They are saved in this prototype's database, not sent to platforms or authorities."],
    ["No accuracy figures are claimed here.", "The web app has not been tested with real users or datasets, and is not a certified security product."],
  ];
  return [el("h2", {}, "Prototype limitations"), el("section", { class: "card" }, el("ul", { class: "clean" }, L.map(([b, t]) => el("li", {}, el("strong", {}, b + " "), t))))];
}

const box = (t, sub, kind) => el("div", { class: `flow-box ${kind || ""}` }, t, sub ? el("small", {}, sub) : null);
const arrow = () => el("div", { class: "flow-arrow" }, icon("arrow"));

export async function howPage() {
  const h = await api.get("/api/health"), stats = await api.get("/api/dashboard/stats");
  const rows = [
    ["Digital identity verification", "simulated", "Scripted simulation. No government ID, Aadhaar, DigiLocker or OTP is contacted or collected."],
    ["Linked accounts", "working", "Real pairwise-pseudonym computation (HMAC-SHA256) on demo identities. The identity itself is simulated."],
    ["Fake profile risk checker", "rule", "Transparent rules on the text you enter. No ML, no scraping."],
    ["Image analysis", "working", "Real metadata, Error Level Analysis and face-region checks. NOT a deepfake detector."],
    ["Scam message detector", "rule", h.ml_model_loaded ? "Transparent rules decide. A trained model adds an advisory score only." : "Transparent keyword and pattern rules. No ML model is loaded; the notebook trains one."],
    ["Impersonation reporting", "working", "Validated and saved to local SQLite with a reference ID. Never sent to any platform or authority."],
  ];
  const step = (n, t, ...kids) => el("section", { class: "card" }, el("h3", {}, `${n}. ${t}`), ...kids);
  return [...pageHeader(["working"], "How the demo works", "A short guide for judges and visitors: what problem we address, what we propose, and what is real in this build."),
    step(1, "The problem", el("p", {}, "Fake profiles, impersonation, manipulated images and scam messages harm individuals, families and small businesses. People struggle to tell what is genuine, and reporting is confusing.")),
    step(2, "The proposed solution", el("p", {}, "Digital Kavach AI proposes one privacy-conscious safety platform: a person verifies a digital identity once through an authorised provider, can still keep several legitimate accounts (personal, shop, village, temple, organisation), and gets plain-language checks for suspicious profiles, images and messages. Platforms would receive only a pseudonymous token, never the legal identity.")),
    step(3, "What the current prototype demonstrates", el("p", {}, "A working interface and six workflows. Identity verification is a simulation; the profile and scam checks use transparent rules; image analysis runs real file-level checks; account linking and reporting store data in a local database.")),
    step(4, "Which features use actual processing", el("div", { class: "table-wrap" }, el("table", {}, el("thead", {}, el("tr", {}, ["Feature", "Label", "What really happens"].map((x) => el("th", {}, x)))),
      el("tbody", {}, rows.map(([f, k, t]) => el("tr", {}, el("th", { scope: "row" }, f), el("td", {}, tag(k)), el("td", {}, t)))))),
      el("p", { class: "muted" }, `Machine-learning models loaded in this web app: ${stats.ml_models_loaded}. Not implemented: Aadhaar / DigiLocker verification; live social-media verification; trained deepfake detection model; LLM scam classification.`)),
    step(5, "What is planned for the future", el("p", {}, tag("future"), " Trained AI models, larger Indian scam datasets, authorised identity verification, privacy-preserving linking and platform integrations. See ", el("a", { href: "#/future" }, "Future development"), ".")),
    el("h2", {}, "System architecture"),
    el("section", { class: "card", "aria-label": "Architecture diagram" }, el("div", { class: "flow" },
      box("User input"), arrow(), box("Frontend validation", "Browser: required fields, file type and size"), arrow(), box("Backend API", "Python REST API: validates everything again"), arrow(), box("Feature selection"), arrow(),
      el("div", { class: "flow-branch" }, box("Identity and linked accounts", "HMAC-SHA256 pseudonyms (identity itself simulated)", "simulated"), box("Rule-based analysis", "Scam and profile rules", "rule"), box("ML model (optional)", h.ml_model_loaded ? "Loaded: advisory only" : "Not loaded in this build; trained in Colab", "future"),
        box("Image processing", "Pillow, NumPy, OpenCV", "working"), box("Report storage", "SQLite, local only", "working"), box("Trained deepfake models", "Future development", "future")),
      arrow(), box("Risk assessment", "Rules decide High; ML can raise to Medium at most"), arrow(), box("Explanation and safety recommendations"), arrow(), box("Report reference ID", "DKA-date-code, saved locally")),
      el("p", { class: "muted" }, "Colour key: ", tag("working"), " ", tag("rule"), " ", tag("simulated"), " ", tag("future"))),
    el("h2", {}, "Technologies used"),
    el("section", { class: "card" }, el("ul", { class: "clean" }, [
      ["Frontend", "Plain JavaScript (ES modules) and CSS, built with safe DOM calls. React, Vite and Tailwind were planned but could not be installed offline."],
      ["Backend", "Python 3 standard-library HTTP server with a REST JSON API (FastAPI could not be installed offline) and SQLite with parameterised queries."],
      ["Image processing", "Pillow (metadata, Error Level Analysis), NumPy, OpenCV (Haar face-region detector)."],
      ["Machine learning", "scikit-learn TF-IDF + Logistic Regression / Naive Bayes, trained in the Google Colab notebook on the public UCI SMS Spam Collection."],
    ].map(([a, b]) => el("li", {}, el("strong", {}, a + ": "), b)))),
    el("h2", {}, "Privacy and security choices"),
    el("section", { class: "card" }, el("ul", { class: "clean" }, [
      "No Aadhaar numbers, biometrics, OTPs or identity documents are collected or stored.",
      "Inputs are validated again on the server. Uploads are limited to JPG/PNG up to 5 MB, checked by file content, and are never written to disk.",
      "Database access uses parameterised queries. Messages, profiles and uploads are never written to server logs. Secrets belong in environment variables.",
      "Report text is stored locally; the status lookup never returns it.",
      "Security headers, a strict Content Security Policy, rate limiting and path-traversal protection are enabled.",
    ].map((t) => el("li", {}, t)))),
    ...limitationsCard(),
    el("h2", {}, "Team"), el("section", { class: "card" }, el("p", {}, el("strong", {}, "SHELD NETWORK"), " - Sakhamuri Meghanath (Team Leader), Tumati Krishanth."), el("p", {}, "Registration ID HSC|AP|00132. Amrita Vishwa Vidyapeetham, Amaravati Campus."), el("p", {}, "Viksit Bharat Young Leaders Dialogue 2027 - Hack for Social Cause. Theme: Digital Safety and Cyber Fraud Awareness."))];
}
