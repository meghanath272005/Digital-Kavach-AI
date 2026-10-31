"""SQLite access. Every query is parameterised; the schema is created automatically on startup."""
import os
import sqlite3
import threading
from contextlib import contextmanager

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS demo_identities (
    id TEXT PRIMARY KEY,
    alias TEXT NOT NULL DEFAULT '',
    secret BLOB NOT NULL,
    status TEXT NOT NULL DEFAULT 'Demo Verification Completed',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS linked_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_id TEXT NOT NULL REFERENCES demo_identities(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    platform TEXT NOT NULL,
    handle TEXT NOT NULL,
    pseudonym TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active (demo)',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE (identity_id, platform, handle)
);
CREATE TABLE IF NOT EXISTS impersonation_reports (
    reference_id TEXT PRIMARY KEY,
    reporter_name TEXT NOT NULL DEFAULT '',
    contact TEXT NOT NULL DEFAULT '',
    username TEXT NOT NULL,
    platform TEXT NOT NULL,
    profile_url TEXT NOT NULL DEFAULT '',
    report_type TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence_description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Submitted',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS report_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_id TEXT NOT NULL REFERENCES impersonation_reports(reference_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    changed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
-- Counters only (feature name + number). No message, profile, image or report content is ever stored here.
CREATE TABLE IF NOT EXISTS usage_counters (
    feature TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0
);
"""


class Database:
    def __init__(self, path):
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)

    @contextmanager
    def tx(self):
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                yield self._conn
                self._conn.execute("COMMIT")
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def one(self, sql, params=()):
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def all(self, sql, params=()):
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def bump(self, feature):
        with self.tx() as c:
            c.execute("INSERT INTO usage_counters(feature,count) VALUES(?,1) "
                      "ON CONFLICT(feature) DO UPDATE SET count = count + 1", (feature,))

    def close(self):
        with self._lock:
            self._conn.close()
