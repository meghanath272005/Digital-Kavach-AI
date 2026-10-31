"""Configuration read from environment variables (and an optional .env file). No secrets live in code."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv():
    for candidate in (ROOT / ".env", ROOT / "backend" / ".env"):
        if candidate.is_file():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


HOST = os.environ.get("DKA_HOST", "127.0.0.1")
PORT = _int("DKA_PORT", 8000)
DB_PATH = os.environ.get("DKA_DB_PATH", str(ROOT / "backend" / "data" / "kavach_demo.sqlite3"))
FRONTEND_DIR = Path(os.environ.get("DKA_FRONTEND_DIR", str(ROOT / "frontend"))).resolve()
CORS_ORIGINS = [o.strip() for o in os.environ.get("DKA_CORS_ORIGINS", "").split(",") if o.strip()]
RATE_LIMIT_PER_MIN = _int("DKA_RATE_LIMIT_PER_MIN", 60)
MAX_IMAGE_BYTES = _int("DKA_MAX_IMAGE_MB", 5) * 1024 * 1024
MODEL_PATH = os.environ.get("DKA_MODEL_PATH", str(ROOT / "backend" / "models" / "scam_model.joblib"))
# Server-side key mixed into every pseudonym HMAC. If unset, a random one is generated for this run
# (pseudonyms then change after a restart, which is acceptable for a demo; set it for stable tokens).
SECRET_KEY = os.environ.get("DKA_SECRET_KEY") or secrets.token_hex(32)
SECRET_KEY_IS_EPHEMERAL = "DKA_SECRET_KEY" not in os.environ
