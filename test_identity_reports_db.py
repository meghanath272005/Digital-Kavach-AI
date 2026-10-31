import sqlite3
import unittest

from tests.helpers import ROOT  # noqa: F401
from app.database import Database
from app.services import identity, reports

KEY = "unit-test-server-key"


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def test_tables_created(self):
        names = {r["name"] for r in self.db.all("SELECT name FROM sqlite_master WHERE type='table'")}
        for t in ("demo_identities", "linked_accounts", "impersonation_reports", "report_status_history"):
            self.assertIn(t, names)

    def test_start_requires_consent_and_rejects_id_numbers(self):
        with self.assertRaises(identity.ValidationError) as e: identity.start_identity(self.db, {"alias": "x", "consent": False})
        self.assertIn("consent", e.exception.errors)
        with self.assertRaises(identity.ValidationError) as e: identity.start_identity(self.db, {"alias": "123456789012", "consent": True})
        self.assertIn("alias", e.exception.errors)
        with self.assertRaises(identity.ValidationError): identity.start_identity(self.db, {"alias": "a@b.com", "consent": True})

    def test_pseudonyms_are_per_platform_and_handle_and_deterministic(self):
        iid = identity.start_identity(self.db, {"alias": "T", "consent": True})["id"]
        a = identity.add_account(self.db, KEY, iid, {"category": "personal", "platform": "Instagram", "handle": "demo.one"})
        b = identity.add_account(self.db, KEY, iid, {"category": "business", "platform": "Facebook", "handle": "demo.one"})
        c = identity.add_account(self.db, KEY, iid, {"category": "personal", "platform": "Instagram", "handle": "demo.two"})
        self.assertEqual(len({a["pseudonym"], b["pseudonym"], c["pseudonym"]}), 3)
        secret = bytes(self.db.one("SELECT secret FROM demo_identities WHERE id=?", (iid,))["secret"])
        self.assertEqual(a["pseudonym"], identity.pseudonym(KEY, secret, "Instagram", "demo.one"))
        self.assertTrue(a["pseudonym"].startswith("pid_") and len(a["pseudonym"]) == 24)
        other = identity.start_identity(self.db, {"alias": "U", "consent": True})["id"]
        d = identity.add_account(self.db, KEY, other, {"category": "personal", "platform": "Instagram", "handle": "demo.one"})
        self.assertNotEqual(a["pseudonym"], d["pseudonym"])
        self.assertNotIn("secret", d)

    def test_multiple_accounts_allowed_duplicates_rejected_remove_status(self):
        iid = identity.start_identity(self.db, {"consent": True})["id"]
        for i, cat in enumerate(identity.CATEGORIES):
            identity.add_account(self.db, KEY, iid, {"category": cat, "platform": "Instagram", "handle": f"demo.h{i}"})
        self.assertEqual(len(identity.list_accounts(self.db, iid)), 5)
        with self.assertRaises(identity.Conflict): identity.add_account(self.db, KEY, iid, {"category": "personal", "platform": "Instagram", "handle": "demo.h0"})
        acc = identity.list_accounts(self.db, iid)[0]
        self.assertEqual(identity.set_account_status(self.db, iid, acc["id"], "Paused (demo)")["status"], "Paused (demo)")
        identity.remove_account(self.db, iid, acc["id"])
        self.assertEqual(len(identity.list_accounts(self.db, iid)), 4)
        with self.assertRaises(identity.NotFound): identity.get_account(self.db, iid, acc["id"])

    def test_sql_injection_attempts_are_inert(self):
        iid = identity.start_identity(self.db, {"consent": True})["id"]
        with self.assertRaises(identity.ValidationError): identity.add_account(self.db, KEY, iid, {"category": "personal", "platform": "Instagram", "handle": "x'; DROP TABLE linked_accounts;--"})
        with self.assertRaises(identity.NotFound): identity.get_identity(self.db, "DEMO-00000000' OR '1'='1")
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM linked_accounts")["n"], 0)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.good = {"username": "fake.person", "platform": "Instagram", "report_type": "Scam or fraud through a profile",
                     "description": "This account pretends to be my shop and asks customers for money.", "evidence_description": "screenshots on my phone"}

    def test_submit_creates_reference_and_history(self):
        r = reports.submit(self.db, self.good)
        self.assertRegex(r["reference_id"], r"^DKA-\d{8}-[0-9A-F]{10}$")
        self.assertEqual(r["status"], "Submitted"); self.assertFalse(r["sent_to_platform_or_authority"])
        self.assertTrue(r["timeline"][0]["reached"]); self.assertFalse(r["timeline"][3]["reached"])
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM report_status_history")["n"], 1)

    def test_unique_references(self):
        refs = {reports.submit(self.db, self.good)["reference_id"] for _ in range(25)}
        self.assertEqual(len(refs), 25)

    def test_validation(self):
        with self.assertRaises(identity.ValidationError) as e: reports.submit(self.db, {})
        for k in ("username", "platform", "report_type", "description"): self.assertIn(k, e.exception.errors)
        bad = dict(self.good, description="too short")
        with self.assertRaises(identity.ValidationError) as e: reports.submit(self.db, bad)
        bad = dict(self.good, contact="not a contact"); 
        with self.assertRaises(identity.ValidationError) as e: reports.submit(self.db, bad)
        self.assertIn("contact", e.exception.errors)
        bad = dict(self.good, description="My Aadhaar is 1234 5678 9012 and they used it for this fake profile")
        with self.assertRaises(identity.ValidationError) as e: reports.submit(self.db, bad)
        self.assertIn("description", e.exception.errors)
        bad = dict(self.good, profile_url="javascript:alert(1)")
        with self.assertRaises(identity.ValidationError): reports.submit(self.db, bad)

    def test_lookup_hides_report_text_and_handles_unknown(self):
        ref = reports.submit(self.db, dict(self.good, contact="a@b.com", reporter_name="Asha"))["reference_id"]
        out = str(reports.lookup(self.db, ref))
        for secret in ("pretends to be my shop", "a@b.com", "Asha", "fake.person"):
            self.assertNotIn(secret, out)
        with self.assertRaises(identity.NotFound): reports.lookup(self.db, "DKA-20260101-0000000000")
        with self.assertRaises(identity.ValidationError): reports.lookup(self.db, "'; DROP TABLE impersonation_reports;--")

    def test_timeline_progression_and_end(self):
        ref = reports.submit(self.db, self.good)["reference_id"]
        seen = [reports.advance(self.db, ref)["status"] for _ in range(3)]
        self.assertEqual(seen, ["Under Review", "Additional Information Required", "Resolved"])
        with self.assertRaises(identity.ValidationError): reports.advance(self.db, ref)
        self.assertTrue(all(t["reached"] for t in reports.lookup(self.db, ref)["timeline"]))


if __name__ == "__main__":
    unittest.main()
