# 3-minute judge demonstration guide

Start: `cd backend && python3 -m app`, open http://127.0.0.1:8000. Have the Dashboard open.

| Time | Do | Say |
|---|---|---|
| 0:00-0:20 | Dashboard | "Digital Kavach AI is a safety prototype. Every feature carries an honest label: working, rule-based, simulated or future. Nothing here is real identity verification." Point at the red/amber notices and the real-count statistics |
| 0:20-1:00 | Click **Use sample scam** on the dashboard, then open **Scam message detector** and paste the *Genuine-style alert* sample | "Rules decide High, and every rule shows its points and reason. The links are defanged and never opened. The genuine bank alert that says 'never share your OTP' is not High." |
| 1:00-1:30 | **Fake profile checker** -> *Suspicious sample profile* -> Check profile | "Each warning sign shows why. It only reads the text we type; it never opens links or scrapes platforms. 'Preliminary and may be incorrect.'" |
| 1:30-2:00 | **Image analysis** -> synthetic sample -> Start analysis | "Real metadata, Error Level Analysis and face-region checks. This is NOT a deepfake detector, and there is no percent-fake score." |
| 2:00-2:30 | **Digital identity** -> tick consent -> Start; then **Linked accounts** -> Load 5 sample accounts | "One simulated identity, five legitimate accounts, five different HMAC-SHA256 tokens. Platforms never see a legal name." Stress the 'Simulation only' banner |
| 2:30-3:00 | **Report impersonation** -> sample report -> Submit -> Simulate next step; end on **Future development** | "Saved to a local database only - it says clearly it is not sent anywhere. Trained deepfake models, authorised verification under DPDP 2023 and platform integrations are plans, not features." |

Likely questions: *Is the F1 score real?* - From the Colab notebook on public English SMS data; not claimed for Indian scams (that is why rules decide High). *Is identity verification real?* - No. Simulation only.
