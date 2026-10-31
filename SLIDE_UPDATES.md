# Updating the HSC slides to match what was actually built

1. **Slide 1/2 (labels)** - correct as they are. Keep "Working: Web prototype + Colab ML notebook", "Rule-based: profile and scam checks", "Simulated: identity", "Planned: Aadhaar/DigiLocker, deepfake model".
2. **Slide 2 "explainable rules + trained scam-text model"** - in the web app the ML model is **optional**: it is trained in the Colab notebook and only affects the web result if you export `scam_model.joblib` into `backend/models/`. Either export it before the demo or reword to "rules in the web app; ML model trained in the notebook".
3. **Slide 3 (Technical Approach)** - the frontend is "JavaScript (ES modules) + CSS" and the backend "Python 3 + standard-library server + SQLite": this matches. Do **not** write React/FastAPI. Replace the three small screenshots with the new ones from `screenshots/`. Fill in the **GitHub link** and **demo video link** placeholders.
4. **Slide 5 numbers**:
   - "29 automated tests pass" -> this repository now has **60 executed tests** (all pass) plus 13 checks inside the notebook. Update to the number you re-run on your own machine.
   - "0.95 F1 on 1,035 held-out SMS" and "F1 0.65 on our 32-message check": these come from your earlier Colab run. They could not be re-verified in the offline build, so **re-run the notebook in Colab with the real dataset and copy the numbers it prints** before presenting.
5. **Slide 3/5 wording** - keep "No accuracy figures are claimed for fake profiles, images or deepfakes".
6. **New facts worth adding** - reports can show a status timeline (the review steps are simulated, labelled demo-only); the hybrid rule is enforced by tests (ML alone can never make a message High); images are processed in memory only.
7. **Slide 7 references** - unchanged. OpenCV/Pillow/SQLite docs are still accurate; add Python `http.server` docs if you cite the backend.
