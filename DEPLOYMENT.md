# GitHub and deployment

## Push to GitHub
```bash
git init
git add .
git commit -m "Initial Digital Kavach AI full-stack implementation"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```
`.env`, `backend/data/` and model files are git-ignored. Then add the repository link to slide 3 ("GitHub / GitLab").

## Hosting (the Python server must run somewhere; GitHub Pages cannot host it)
Set environment variables: `DKA_HOST=0.0.0.0`, `DKA_PORT=$PORT` (if the host provides one), `DKA_SECRET_KEY=<long random>`, `DKA_DB_PATH=<path on a persistent disk>`.
Start command: `cd backend && python3 -m app`. Install command: `pip install -r requirements.txt`.

- **Render**: New Web Service from the GitHub repo, runtime Python, the commands above. Free instances sleep and have ephemeral disks (data resets) - fine for a demo; add a persistent disk to keep reports.
- **Railway**: New project from the repo; set the variables; Railway provides `PORT` (set `DKA_PORT` to it, or run `DKA_PORT=$PORT`).
- **PythonAnywhere**: upload/clone the repo, create a virtualenv, `pip install -r requirements.txt`. This server is not WSGI; run it in an "Always-on task" (paid) or use it only for short demos. Converting the routes to a WSGI/FastAPI app is the clean option there.

Before any public deployment: this demo has no user authentication, and it must not be used for real personal data.
