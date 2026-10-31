"""Security helpers: headers, CSP, rate limiting, safe static-file resolution."""
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; "
       "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; "
       "form-action 'self'; frame-ancestors 'none'")

SECURITY_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cache-Control": "no-store",
}


class RateLimiter:
    """Sliding-window limiter keyed by client address (in memory; resets on restart)."""

    def __init__(self, per_minute):
        self.per_minute = per_minute
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key, now=None):
        if self.per_minute <= 0:
            return True, 0
        now = time.monotonic() if now is None else now
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= self.per_minute:
                return False, int(60 - (now - q[0])) + 1
            q.append(now)
            return True, 0


def safe_static_path(root: Path, url_path: str):
    """Maps a URL path to a file strictly inside `root`; returns None on any traversal attempt."""
    from urllib.parse import unquote
    rel = unquote(url_path.split("?", 1)[0]).lstrip("/")
    if "\x00" in rel or "\\" in rel:
        return None
    root = root.resolve()
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate if candidate.is_file() else None
