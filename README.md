# Digital Kavach AI

**One Trusted Identity. Multiple Legitimate Accounts. Safer Digital India.**

Team **SHELD NETWORK** (Sakhamuri Meghanath, Team Leader; Tumati Krishanth) - Registration ID HSC|AP|00132 -
Amrita Vishwa Vidyapeetham, Amaravati Campus - Viksit Bharat Young Leaders Dialogue 2027, Hack for Social Cause
(theme: Digital Safety & Cyber Fraud Awareness).

> **Demonstration prototype.** Not a certified security product. No government identity verification takes place,
> there is no deepfake detection model, and no accuracy figures are claimed for the web app.

## What is in this repository

| Part | Where | Status |
|---|---|---|
| Web app (frontend + REST API + SQLite) | `frontend/`, `backend/` | Runs and tested (see Testing) |
| Google Colab notebook (ML + hybrid checker) | `notebook/digital_kavach_colab.ipynb` | Ran offline on the built-in demo set; real-data run needs internet (see Limitations) |
| Tests | `tests/` (60 tests) | Executed, all pass |
| Docs | `docs/` | API docs, deviations, 3-minute demo guide, deployment, slide-update notes |
| Screenshots | `screenshots/` | Real captures of the running app (desktop + mobile) |

## Features and honest labels

Every page carries one of: **Working feature**, **Rule-based demo**, **Simulated workflow**, **Future development**.

| Page | Label | What really happens |
|---|---|---|
| Dashboard | Working | Live scam-check box; statistics are real counts from the local database (no invented numbers) |
| Digital identity | Simulated | Scripted verification. Shows "Simulation only - no government identity verification has taken place." Never asks for Aadhaar, biometrics, documents or OTPs |
| Linked accounts | Working + Simulated | Add / view / pause / remove demo accounts; per-platform pseudonyms via real HMAC-SHA256; many accounts per identity are allowed |
| Fake profile checker | Rule-based | Transparent rules on typed text only; each finding shows points and a reason; Low / Medium / High / Inconclusive; never opens links |
| Image analysis | Working | JPG/PNG, 5 MB cap, type checked by file content, in-memory only. Metadata tags, Error Level Analysis heat map, OpenCV face-region detection (fails safely), SHA-256. **Not a deepfake detector; no scores or "percent fake"** |
| Scam message detector | Rule-based (ML optional) | Rules for OTP/PIN requests (ignores "never share your OTP" warnings), urgency, payments, links (defanged, never opened), prizes, confidential info, impersonation, digital arrest, remote-access apps, easy-money jobs. **Rules decide High; an ML model, if loaded, can raise Low to Medium only** |
| Report impersonation | Working (status steps simulated) | Server-side validation, reference ID (`DKA-YYYYMMDD-XXXXXXXXXX`), SQLite, status timeline. **Never sent to any platform or authority.** A "Simulate next review step" button demonstrates the timeline; it is labelled demo-only |
| Safety recommendations | Working | Advice plus helpline **1930** and https://cybercrime.gov.in/ |
| How the demo works | Working | Architecture diagram, what is real vs simulated |
| Future development | Future | Plans only |

## Honest deviations from the preferred stack

The build sandbox had no internet, so React/Vite/Tailwind/FastAPI/Lucide could not be installed. A tested alternative was used:
plain JavaScript (ES modules) + CSS, inline SVG icons, and a Python standard-library HTTP server with the same REST design,
SQLite, Pillow, NumPy and OpenCV. Details and a migration path are in [docs/DEVIATIONS.md](docs/DEVIATIONS.md).

## Folder structure

```
digital-kavach-ai/
  backend/app/        server.py, config.py, database.py, security.py, services/ (rules, image, identity, reports, hybrid, content)
  backend/models/     optional scam_model.joblib exported from the notebook (not committed)
  frontend/           index.html, css/styles.css, js/ (api, ui, icons, app, pages/)
  notebook/           digital_kavach_colab.ipynb
  tests/              unit + API + security tests (unittest)
  docs/               API_DOCUMENTATION.md, DEVIATIONS.md, DEMO_GUIDE.md, DEPLOYMENT.md, SLIDE_UPDATES.md
  scripts/            capture_screenshots.py
  screenshots/        real screenshots
  requirements.txt  package.json  .env.example  .gitignore  README.md
```

## Run it

Requires Python 3.10+.

```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then set DKA_SECRET_KEY to a long random value
cd backend && python3 -m app                           # serves API and frontend on http://127.0.0.1:8000
```

Open http://127.0.0.1:8000. The database file is created automatically (`backend/data/`). `npm start` is a shortcut for the
same command; there is no Node build step and no npm dependency.

### Optional: enable the ML score
Run the notebook on the real UCI SMS data in Colab, run Step 6b, download `scam_model.joblib`, and put it in
`backend/models/`. The page then shows the ML prediction beside the rule findings. Only load model files you created
(pickle files can run code).

## Testing

```bash
python3 -m unittest discover -s tests -t .      # 60 tests: rules, hybrid logic, image checks, DB, API, security
python3 scripts/capture_screenshots.py          # re-capture screenshots (needs playwright + chromium, server running)
```

## Security notes
Server-side validation on every endpoint; parameterised SQL only; CSP without `unsafe-inline`, `X-Frame-Options`,
`nosniff`, `no-referrer`; per-IP rate limiting (429 + `Retry-After`); path-traversal-safe static serving; request size limits;
logs record method, route and status only (never messages, profiles, reports or images); secrets only via environment.
The demo has **no user authentication** (identity ids are random capability tokens). Do not expose it publicly with real data.

## Limitations
- No real identity verification; no live platform access; no deepfake model; rules cover mainly English and some Hinglish.
- Rules produce false alarms and misses; results are preliminary.
- The 0.95 F1 / 0.65 F1 figures on the slides come from the notebook run on real data. They could **not** be re-verified in the offline build sandbox (no internet to download the UCI dataset). Re-run the notebook in Colab before quoting them.
- Not tested: internet dataset download, ipywidgets UI (both need Colab/internet), real-device mobile browsers (tested with headless Chromium at 390 px).
- Reports and accounts live in a local SQLite file; pseudonyms change after a restart unless `DKA_SECRET_KEY` is set (only for accounts linked after the restart).

## Deployment and GitHub
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). GitHub Pages cannot host the Python server.
