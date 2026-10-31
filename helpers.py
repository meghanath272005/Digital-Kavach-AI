import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.server import make_server  # noqa: E402


class LiveServer:
    """Runs the real HTTP server on a free port with an in-memory database."""

    def __init__(self, rate_limit=1000):
        self.httpd = make_server(host="127.0.0.1", port=0, db_path=":memory:", rate_limit=rate_limit)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown(); self.httpd.server_close(); self.httpd.kavach_db.close()

    def request(self, method, path, body=None, headers=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        h = dict(headers or {})
        if raw is None and body is not None:
            h.setdefault("Content-Type", "application/json")
        if method in ("POST", "PATCH") and data is None:
            data = b""
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def json(self, method, path, body=None, **kw):
        status, headers, raw = self.request(method, path, body, **kw)
        try:
            return status, json.loads(raw.decode() or "null"), headers
        except ValueError:
            return status, None, headers
