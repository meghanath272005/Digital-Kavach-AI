"""Digital Kavach AI - standard-library HTTP server (REST JSON API + static frontend).

Why not FastAPI? It was not installable in the offline build environment, so the same REST design is
implemented with Python's standard library. See docs/DEVIATIONS.md. Nothing here pretends otherwise.
"""
import json
import logging
import mimetypes
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import config
from .database import Database
from .security import RateLimiter, SECURITY_HEADERS, safe_static_path
from .services import content, hybrid, identity, image_forensics, profile_rules, reports

log = logging.getLogger("kavach")
MAX_JSON_BYTES = 64 * 1024
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/svg+xml", ".svg")

ID_ROUTE = re.compile(r"^/api/identity/(DEMO-[0-9A-F]{8})(/.*)?$")
ACC_ROUTE = re.compile(r"^/accounts(?:/(\d{1,9}))?$")
REF_ROUTE = re.compile(r"^/api/reports/([A-Za-z0-9-]{1,40})(/simulate-next)?$")


class ApiError(Exception):
    def __init__(self, status, message, fields=None):
        super().__init__(message)
        self.status, self.message, self.fields = status, message, fields or {}


def make_server(host=None, port=None, db_path=None, rate_limit=None, frontend_dir=None):
    host = host or config.HOST
    port = config.PORT if port is None else port
    db = Database(db_path or config.DB_PATH)
    hybrid.load_model(config.MODEL_PATH)
    general = RateLimiter(config.RATE_LIMIT_PER_MIN if rate_limit is None else rate_limit)
    heavy = RateLimiter(max(5, (config.RATE_LIMIT_PER_MIN if rate_limit is None else rate_limit) // 4) if (rate_limit or config.RATE_LIMIT_PER_MIN) > 0 else 0)
    root = Path(frontend_dir or config.FRONTEND_DIR)

    class Handler(BaseHTTPRequestHandler):
        server_version = "KavachDemo"
        sys_version = ""

        # --- logging: method, route and status ONLY. Never bodies, queries or user text. ---
        def log_message(self, fmt, *args):
            return

        def _log(self, status):
            path = urlparse(self.path).path
            path = re.sub(r"DEMO-[0-9A-F]{8}", "DEMO-*", path)
            path = re.sub(r"DKA-[0-9A-Za-z-]+", "DKA-*", path)
            log.info("%s %s -> %s", self.command, path[:80], status)

        # --- response helpers ---
        def _headers(self, status, ctype, length, extra=None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(length))
            for k, v in SECURITY_HEADERS.items():
                self.send_header(k, v)
            origin = self.headers.get("Origin")
            if origin and origin in config.CORS_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()

        def _json(self, status, payload, extra=None):
            body = json.dumps(payload, ensure_ascii=False).encode()
            self._headers(status, "application/json; charset=utf-8", len(body), extra)
            if self.command != "HEAD":
                self.wfile.write(body)
            self._log(status)

        def _error(self, status, message, fields=None, extra=None):
            self._json(status, {"error": {"status": status, "message": message, "fields": fields or {}}}, extra)

        def _read_body(self, limit):
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                raise ApiError(411, "A Content-Length header is required.")
            if length < 0 or length > limit:
                # Drain (up to 16 MB, discarding) so the client can read our 413 instead of a broken pipe.
                remaining = min(max(length, 0), 16 * 1024 * 1024)
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                self.close_connection = True
                raise ApiError(413, f"Request body too large (limit {limit // 1024} KB).")
            return self.rfile.read(length)

        def _read_json(self):
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if ctype != "application/json":
                raise ApiError(415, "Send the request as application/json.")
            raw = self._read_body(MAX_JSON_BYTES)
            try:
                data = json.loads(raw.decode("utf-8") or "{}")
            except (ValueError, UnicodeDecodeError):
                raise ApiError(400, "The request body is not valid JSON.")
            if not isinstance(data, dict):
                raise ApiError(400, "The JSON body must be an object.")
            return data

        # --- verbs ---
        def do_OPTIONS(self):
            origin = self.headers.get("Origin")
            extra = {}
            if origin and origin in config.CORS_ORIGINS:
                extra = {"Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
                         "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "600"}
            self._headers(204, "text/plain", 0, extra)
            self._log(204)

        def do_GET(self):
            self._dispatch("GET")

        def do_HEAD(self):
            self._dispatch("GET")

        def do_POST(self):
            self._dispatch("POST")

        def do_PATCH(self):
            self._dispatch("PATCH")

        def do_DELETE(self):
            self._dispatch("DELETE")

        def _dispatch(self, method):
            path = urlparse(self.path).path
            try:
                if path.startswith("/api/"):
                    self._api(method, path)
                elif method == "GET":
                    self._static(path)
                else:
                    raise ApiError(405, "Method not allowed.")
            except ApiError as e:
                self._error(e.status, e.message, e.fields)
            except identity.ValidationError as e:
                self._error(422, "Some fields need attention.", e.errors)
            except identity.NotFound as e:
                self._error(404, str(e) or "Not found.")
            except identity.Conflict as e:
                self._error(409, str(e))
            except Exception:  # never leak internals or user content
                log.exception("unhandled error on %s", re.sub(r"[^/\w-]", "", path)[:60])
                self._error(500, "Something went wrong on the server. Please try again.")

        # --- static files with path-traversal protection ---
        def _static(self, path):
            target = safe_static_path(root, path)
            if target is None:
                raise ApiError(404, "Not found.")
            data = target.read_bytes()
            ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
                ctype += "; charset=utf-8"
            self._headers(200, ctype, len(data))
            if self.command != "HEAD":
                self.wfile.write(data)
            self._log(200)

        # --- API ---
        def _api(self, method, path):
            client = self.client_address[0]
            is_heavy = path.startswith("/api/image/")
            ok, retry = (heavy if is_heavy else general).allow(client)
            if not ok:
                self._error(429, "Too many requests. Please wait a moment and try again.", extra={"Retry-After": str(retry)})
                return
            if path == "/api/health" and method == "GET":
                return self._json(200, {"status": "ok", "service": "digital-kavach-ai-demo", "ml_model_loaded": hybrid.model_loaded()})
            if path == "/api/dashboard/stats" and method == "GET":
                return self._json(200, self._stats())
            if path == "/api/meta" and method == "GET":
                return self._json(200, {"categories": identity.CATEGORIES, "platforms": identity.PLATFORMS,
                                        "report_platforms": reports.PLATFORMS, "report_types": reports.REPORT_TYPES,
                                        "report_statuses": reports.STATUSES, "account_statuses": identity.ACCOUNT_STATUSES})
            if path == "/api/samples" and method == "GET":
                return self._json(200, content.SAMPLES)
            if path == "/api/recommendations" and method == "GET":
                return self._json(200, content.RECOMMENDATIONS)
            if path == "/api/scam/check" and method == "POST":
                return self._scam(self._read_json())
            if path == "/api/profile/check" and method == "POST":
                return self._profile(self._read_json())
            if path == "/api/image/sample" and method == "GET":
                body = image_forensics.make_sample_image()
                self._headers(200, "image/jpeg", len(body))
                self.wfile.write(body)
                return self._log(200)
            if path == "/api/image/analyse-sample" and method == "POST":
                self._read_body(1024)
                return self._image(image_forensics.make_sample_image())
            if path == "/api/image/analyse" and method == "POST":
                ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                if ctype not in ("image/jpeg", "image/png", "application/octet-stream"):
                    raise ApiError(415, "Send the image bytes as image/jpeg or image/png.")
                return self._image(self._read_body(config.MAX_IMAGE_BYTES + 1024))
            if path == "/api/identity/start" and method == "POST":
                out = identity.start_identity(db, self._read_json())
                return self._json(201, out)
            m = ID_ROUTE.match(path)
            if m:
                return self._identity(method, m.group(1), m.group(2) or "")
            if path == "/api/reports" and method == "POST":
                return self._json(201, reports.submit(db, self._read_json()))
            m = REF_ROUTE.match(path)
            if m:
                if m.group(2) and method == "POST":
                    self._read_body(1024)
                    return self._json(200, reports.advance(db, m.group(1)))
                if not m.group(2) and method == "GET":
                    return self._json(200, reports.lookup(db, m.group(1)))
            raise ApiError(404, "Unknown API route.")

        def _stats(self):
            counts = {r["feature"]: r["count"] for r in db.all("SELECT feature, count FROM usage_counters")}
            one = lambda sql: db.one(sql)["n"]
            return {"source": "Counts from this prototype's local database only. No figures are estimated or invented.",
                    "demo_identities": one("SELECT COUNT(*) AS n FROM demo_identities"),
                    "linked_accounts": one("SELECT COUNT(*) AS n FROM linked_accounts"),
                    "reports_saved": one("SELECT COUNT(*) AS n FROM impersonation_reports"),
                    "checks_run": {"scam_messages": counts.get("scam_check", 0), "profiles": counts.get("profile_check", 0),
                                   "images": counts.get("image_check", 0)},
                    "ml_models_loaded": 1 if hybrid.model_loaded() else 0}

        def _scam(self, data):
            text = str(data.get("message", ""))
            if not text.strip():
                raise identity.ValidationError({"message": "Paste the message you want to check."})
            if len(text) > 5000:
                raise identity.ValidationError({"message": "Keep the message under 5,000 characters."})
            result = hybrid.analyse(text.strip())
            db.bump("scam_check")
            self._json(200, result)

        def _profile(self, data):
            clean, errors = profile_rules.validate(data)
            if errors:
                raise identity.ValidationError(errors)
            result = profile_rules.analyse(clean)
            db.bump("profile_check")
            self._json(200, result)

        def _image(self, raw):
            try:
                result = image_forensics.analyse(raw, config.MAX_IMAGE_BYTES)
            except image_forensics.ImageError as e:
                raise ApiError(422, str(e), {"image": str(e)})
            db.bump("image_check")
            self._json(200, result)

        def _identity(self, method, iid, rest):
            if rest == "" and method == "GET":
                return self._json(200, identity.get_identity(db, iid))
            m = ACC_ROUTE.match(rest)
            if not m:
                raise ApiError(404, "Unknown API route.")
            aid = m.group(1)
            if aid is None:
                if method == "GET":
                    return self._json(200, {"accounts": identity.list_accounts(db, iid)})
                if method == "POST":
                    return self._json(201, identity.add_account(db, config.SECRET_KEY, iid, self._read_json()))
            else:
                aid = int(aid)
                if method == "GET":
                    return self._json(200, identity.get_account(db, iid, aid))
                if method == "PATCH":
                    return self._json(200, identity.set_account_status(db, iid, aid, self._read_json().get("status")))
                if method == "DELETE":
                    identity.remove_account(db, iid, aid)
                    return self._json(200, {"removed": True})
            raise ApiError(405, "Method not allowed.")

    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    httpd.kavach_db = db
    return httpd


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    httpd = make_server()
    host, port = httpd.server_address[:2]
    if config.SECRET_KEY_IS_EPHEMERAL:
        log.warning("DKA_SECRET_KEY is not set: pseudonyms will change after a restart (fine for a demo).")
    log.info("Digital Kavach AI demo on http://%s:%s  (ML model loaded: %s)", host, port, hybrid.model_loaded())
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("Stopping.")
    finally:
        httpd.server_close()
        httpd.kavach_db.close()


if __name__ == "__main__":
    sys.exit(main())
