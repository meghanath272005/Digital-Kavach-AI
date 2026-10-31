# Deviations from the requested stack (and why)

The build environment had **no internet access**, so `pip install fastapi uvicorn pydantic` and `npm install react vite tailwindcss lucide-react` could not work.
Rather than pretend, the following tested alternatives were used.

| Requested | Used instead | Notes |
|---|---|---|
| React + Vite + Tailwind | Plain JavaScript ES modules + hand-written CSS | No build step. DOM is built with `createElement`/`textContent`, so user text is never parsed as HTML |
| Lucide React icons | Inline SVG icon set (`frontend/js/icons.js`) in a similar line style | |
| FastAPI + Pydantic | Python `http.server` (threaded) with the same REST routes | Validation is hand-written per endpoint; there is no automatic OpenAPI page or response-model validation - the contract is in `docs/API_DOCUMENTATION.md` |
| pytest / httpx | `unittest` + `urllib` against a live server on a random port | |
| Installed ML model | None in the web app by default; optional `scam_model.joblib` exported from the notebook | The page says plainly when no model is loaded |

Preserved: SQLite, Pillow, NumPy, OpenCV, scikit-learn (notebook), parameterised SQL, security headers + CSP, rate limiting, path-traversal protection, environment variables, CORS allow-list.

## Moving to FastAPI + React later
The service modules in `backend/app/services/` are framework-independent: wrap each in a FastAPI route and Pydantic schema. The REST contract can stay unchanged, so a Vite/React frontend can call it as-is.
