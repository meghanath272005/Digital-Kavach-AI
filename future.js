import { el, pageHeader, tag } from "../ui.js";
import { limitationsCard } from "./how.js";

const ITEMS = [
  ["Trained deepfake detection models", "Integrate and benchmark pretrained image-manipulation and deepfake-detection models (for example models trained on FaceForensics++ or DFDC), reporting real error rates."],
  ["Larger Indian scam datasets", "Collect and label a larger, consented set of Indian-language scam and genuine messages so the ML component can be tested honestly before use."],
  ["More reliable fake-profile assessment", "Combine rules with a validated model, using authorised platform signals and a human review and appeal process."],
  ["Authorised identity verification", "Integrate approved identity providers with explicit user consent and compliance with the Digital Personal Data Protection Act, 2023."],
  ["Privacy-preserving account linking", "Replace the demo pseudonyms with a reviewed protocol (for example pairwise identifiers with selective disclosure) so platforms learn only what they need."],
  ["Official social media platform APIs", "Work with participating platforms through official APIs so verified badges and reports can really be exchanged."],
  ["Real-world testing", "Usability, accessibility and security review with real users and regional-language support."],
  ["Production-grade security infrastructure", "Authentication, managed database, monitoring, audited secrets handling and a professional security assessment."],
];
export async function futurePage() {
  return [...pageHeader(["future"], "Future development", "What the SHELD NETWORK team plans next. Everything on this page is a plan, not a finished feature."),
    ...ITEMS.map(([t, p]) => el("div", { class: "future-item" }, el("div", {}, el("h3", {}, t), el("p", {}, p)), tag("future"))),
    ...limitationsCard()];
}
