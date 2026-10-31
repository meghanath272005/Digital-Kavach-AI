import io
import json
import logging
import unittest

from PIL import Image
from tests.helpers import LiveServer, ROOT  # noqa: F401
from app.services import image_forensics as ifx


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = LiveServer()

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    # ---- basics
    def test_health_and_meta_samples_recommendations(self):
        st, d, _ = self.s.json("GET", "/api/health"); self.assertEqual((st, d["status"]), (200, "ok"))
        self.assertFalse(d["ml_model_loaded"])
        st, d, _ = self.s.json("GET", "/api/meta"); self.assertEqual(st, 200); self.assertIn("Instagram", d["platforms"])
        st, d, _ = self.s.json("GET", "/api/samples"); self.assertEqual(st, 200); self.assertTrue(d["scam"])
        st, d, _ = self.s.json("GET", "/api/recommendations"); self.assertEqual(d["helpline"]["number"], "1930")
        self.assertEqual(d["helpline"]["portal"], "https://cybercrime.gov.in/")

    def test_unknown_route_and_wrong_method(self):
        self.assertEqual(self.s.json("GET", "/api/nope")[0], 404)
        self.assertEqual(self.s.json("DELETE", "/api/health")[0], 404)

    # ---- scam
    def test_scam_check_high_and_defanged(self):
        st, d, _ = self.s.json("POST", "/api/scam/check", {"message": "SBI ALERT: share the OTP now or account blocked http://sbi-kyc-update.xyz"})
        self.assertEqual(st, 200); self.assertEqual(d["category"], "High")
        self.assertTrue(d["links"][0]["display"].startswith("hxxp://")); self.assertFalse(d["ml"]["available"])

    def test_scam_genuine_alert_not_high(self):
        st, d, _ = self.s.json("POST", "/api/scam/check", {"message": "HDFC Bank: Rs 500 debited a/c XX1234. Never share your OTP with anyone."})
        self.assertEqual(st, 200); self.assertNotEqual(d["category"], "High")

    def test_scam_validation(self):
        st, d, _ = self.s.json("POST", "/api/scam/check", {"message": "   "}); self.assertEqual(st, 422); self.assertIn("message", d["error"]["fields"])
        st, d, _ = self.s.json("POST", "/api/scam/check", {"message": "a" * 5001}); self.assertEqual(st, 422)
        st, _, _ = self.s.json("POST", "/api/scam/check", raw=b"{not json", headers={"Content-Type": "application/json"}); self.assertEqual(st, 400)
        st, _, _ = self.s.json("POST", "/api/scam/check", raw=b"message=hi", headers={"Content-Type": "text/plain"}); self.assertEqual(st, 415)
        st, _, _ = self.s.json("POST", "/api/scam/check", raw=b"[1,2]", headers={"Content-Type": "application/json"}); self.assertEqual(st, 400)

    def test_oversized_json_rejected(self):
        st, _, _ = self.s.json("POST", "/api/scam/check", raw=b'{"message":"' + b"a" * 70000 + b'"}', headers={"Content-Type": "application/json"})
        self.assertEqual(st, 413)

    # ---- profile
    def test_profile_check(self):
        st, samples, _ = self.s.json("GET", "/api/samples")
        st, d, _ = self.s.json("POST", "/api/profile/check", samples["profile"][0]); self.assertEqual((st, d["category"]), (200, "High"))
        st, d, _ = self.s.json("POST", "/api/profile/check", {"username": ""}); self.assertEqual(st, 422); self.assertIn("username", d["error"]["fields"])
        st, d, _ = self.s.json("POST", "/api/profile/check", {"username": "ok_user", "url": "ftp://x.y"}); self.assertEqual(st, 422)

    # ---- image
    def test_image_upload_png_and_jpeg(self):
        b = io.BytesIO(); Image.new("RGB", (100, 80), (9, 99, 199)).save(b, "PNG")
        st, d, _ = self.s.json("POST", "/api/image/analyse", raw=b.getvalue(), headers={"Content-Type": "image/png"})
        self.assertEqual(st, 200); self.assertEqual(d["measurements"]["format"], "PNG"); self.assertFalse(d["stored"])
        st, d, _ = self.s.json("POST", "/api/image/analyse", raw=ifx.make_sample_image(), headers={"Content-Type": "image/jpeg"})
        self.assertEqual(st, 200); self.assertTrue(d["ela_heatmap"].startswith("data:image/png"))

    def test_image_sample_endpoints(self):
        st, h, raw = self.s.request("GET", "/api/image/sample"); self.assertEqual(st, 200); self.assertEqual(raw[:3], b"\xff\xd8\xff")
        st, d, _ = self.s.json("POST", "/api/image/analyse-sample"); self.assertEqual(st, 200); self.assertEqual(d["verdict"], "Indicators found")

    def test_image_rejections(self):
        st, d, _ = self.s.json("POST", "/api/image/analyse", raw=b"GIF89a" + b"0" * 300, headers={"Content-Type": "image/png"}); self.assertEqual(st, 422)  # wrong content, claimed PNG
        st, _, _ = self.s.json("POST", "/api/image/analyse", raw=b"<svg onload=alert(1)>", headers={"Content-Type": "image/svg+xml"}); self.assertEqual(st, 415)
        st, _, _ = self.s.json("POST", "/api/image/analyse", raw=b"", headers={"Content-Type": "image/png"}); self.assertEqual(st, 422)
        st, _, _ = self.s.json("POST", "/api/image/analyse", raw=b"\x89PNG\r\n\x1a\n" + b"\0" * (5 * 1024 * 1024 + 4096), headers={"Content-Type": "image/png"}); self.assertEqual(st, 413)

    # ---- identity + accounts
    def test_identity_and_accounts_flow(self):
        st, d, _ = self.s.json("POST", "/api/identity/start", {"alias": "Tester", "consent": False}); self.assertEqual(st, 422)
        st, d, _ = self.s.json("POST", "/api/identity/start", {"alias": "Tester", "consent": True}); self.assertEqual(st, 201)
        iid = d["id"]; self.assertTrue(d["simulated"]); self.assertIn("Simulation only", d["notice"]); self.assertIn("Aadhaar number or image", d["never_collected"])
        self.assertEqual(self.s.json("GET", f"/api/identity/{iid}")[0], 200)
        body = {"category": "business", "platform": "Facebook", "handle": "demo.shop"}
        st, a, _ = self.s.json("POST", f"/api/identity/{iid}/accounts", body); self.assertEqual(st, 201); self.assertTrue(a["pseudonym"].startswith("pid_"))
        self.assertEqual(self.s.json("POST", f"/api/identity/{iid}/accounts", body)[0], 409)
        self.assertEqual(self.s.json("POST", f"/api/identity/{iid}/accounts", {"category": "x", "platform": "y", "handle": "!"})[0], 422)
        st, lst, _ = self.s.json("GET", f"/api/identity/{iid}/accounts"); self.assertEqual(len(lst["accounts"]), 1)
        self.assertEqual(self.s.json("GET", f"/api/identity/{iid}/accounts/{a['id']}")[0], 200)
        st, p, _ = self.s.json("PATCH", f"/api/identity/{iid}/accounts/{a['id']}", {"status": "Paused (demo)"}); self.assertEqual(p["status"], "Paused (demo)")
        self.assertEqual(self.s.json("PATCH", f"/api/identity/{iid}/accounts/{a['id']}", {"status": "hacked"})[0], 422)
        self.assertEqual(self.s.json("DELETE", f"/api/identity/{iid}/accounts/{a['id']}")[0], 200)
        self.assertEqual(self.s.json("GET", f"/api/identity/{iid}/accounts/{a['id']}")[0], 404)
        self.assertEqual(self.s.json("GET", "/api/identity/DEMO-FFFFFFFF")[0], 404)

    def test_account_belongs_to_its_identity_only(self):
        i1 = self.s.json("POST", "/api/identity/start", {"consent": True})[1]["id"]
        i2 = self.s.json("POST", "/api/identity/start", {"consent": True})[1]["id"]
        a = self.s.json("POST", f"/api/identity/{i1}/accounts", {"category": "personal", "platform": "X", "handle": "demo.a"})[1]
        self.assertEqual(self.s.json("GET", f"/api/identity/{i2}/accounts/{a['id']}")[0], 404)
        self.assertEqual(self.s.json("DELETE", f"/api/identity/{i2}/accounts/{a['id']}")[0], 404)

    # ---- reports
    def test_report_submit_lookup_and_timeline(self):
        body = {"username": "fake.asha", "platform": "Instagram", "report_type": "Fake profile using my identity", "description": "A new account uses my name and photo to ask for money."}
        st, r, _ = self.s.json("POST", "/api/reports", body); self.assertEqual(st, 201)
        ref = r["reference_id"]; self.assertFalse(r["sent_to_platform_or_authority"]); self.assertIn("NOT been sent", r["notice"])
        st, g, _ = self.s.json("GET", f"/api/reports/{ref}"); self.assertEqual((st, g["status"]), (200, "Submitted"))
        self.assertNotIn("A new account uses my name", json.dumps(g))
        st, n, _ = self.s.json("POST", f"/api/reports/{ref}/simulate-next"); self.assertEqual(n["status"], "Under Review")
        self.assertEqual(self.s.json("GET", "/api/reports/DKA-20260101-AAAAAAAAAA")[0], 404)
        self.assertEqual(self.s.json("GET", "/api/reports/not-a-ref")[0], 422)

    def test_report_validation_errors(self):
        st, d, _ = self.s.json("POST", "/api/reports", {}); self.assertEqual(st, 422)
        for k in ("username", "platform", "report_type", "description"): self.assertIn(k, d["error"]["fields"])

    # ---- stats reflect real data only
    def test_dashboard_stats_are_real_counts(self):
        before = self.s.json("GET", "/api/dashboard/stats")[1]
        self.s.json("POST", "/api/scam/check", {"message": "Please share your OTP right now"})
        self.s.json("POST", "/api/identity/start", {"consent": True})
        after = self.s.json("GET", "/api/dashboard/stats")[1]
        self.assertEqual(after["checks_run"]["scam_messages"], before["checks_run"]["scam_messages"] + 1)
        self.assertEqual(after["demo_identities"], before["demo_identities"] + 1)
        self.assertEqual(after["ml_models_loaded"], 0)


class SecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = LiveServer()

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def test_security_headers_and_csp(self):
        for path in ("/", "/api/health", "/css/styles.css"):
            st, h, _ = self.s.request("GET", path)
            self.assertEqual(st, 200, path)
            self.assertIn("default-src 'self'", h["Content-Security-Policy"]); self.assertNotIn("unsafe-inline", h["Content-Security-Policy"])
            self.assertEqual(h["X-Content-Type-Options"], "nosniff"); self.assertEqual(h["X-Frame-Options"], "DENY")
            self.assertIn("no-referrer", h["Referrer-Policy"])

    def test_path_traversal_blocked(self):
        for p in ("/../backend/app/config.py", "/..%2f..%2fbackend%2fapp%2fconfig.py", "/%2e%2e/%2e%2e/etc/passwd", "/..\\..\\etc\\passwd", "/js/../../backend/app/server.py", "/%00.html"):
            st, _, body = self.s.request("GET", p)
            self.assertIn(st, (400, 404), p); self.assertNotIn(b"SECRET_KEY", body)

    def test_static_serving_and_404(self):
        st, h, body = self.s.request("GET", "/"); self.assertIn(b"Digital Kavach AI", body); self.assertIn("text/html", h["Content-Type"])
        self.assertIn("javascript", self.s.request("GET", "/js/app.js")[1]["Content-Type"])
        self.assertEqual(self.s.request("GET", "/missing.html")[0], 404)

    def test_cors_only_for_allowed_origins(self):
        st, h, _ = self.s.request("GET", "/api/health", headers={"Origin": "https://evil.example"})
        self.assertNotIn("Access-Control-Allow-Origin", h)

    def test_rate_limit_returns_429(self):
        s = LiveServer(rate_limit=8)
        try:
            codes = [s.request("GET", "/api/health")[0] for _ in range(12)]
            self.assertEqual(codes[:8], [200] * 8); self.assertIn(429, codes[8:])
            st, h, _ = s.request("GET", "/api/health"); self.assertEqual(st, 429); self.assertIn("Retry-After", h)
        finally:
            s.close()

    def test_user_content_never_logged(self):
        records = []
        class H(logging.Handler):
            def emit(self, r): records.append(r.getMessage())
        h = H(); lg = logging.getLogger("kavach"); lg.addHandler(h); lg.setLevel(logging.DEBUG)
        try:
            secret = "UNIQUE-SECRET-TEXT-9917"
            self.s.json("POST", "/api/scam/check", {"message": f"Share the OTP {secret}"})
            self.s.json("POST", "/api/reports", {"username": "x_user", "platform": "X", "report_type": "Other", "description": f"{secret} description long enough"})
            self.s.json("GET", "/api/reports/DKA-20260101-AAAAAAAAAA?q=" + secret)
        finally:
            lg.removeHandler(h)
        self.assertTrue(records)
        self.assertFalse(any(secret in r for r in records), records)

    def test_server_error_does_not_leak_details(self):
        # a malformed Content-Length must not crash the handler or leak a traceback
        st, _, body = self.s.request("POST", "/api/scam/check", raw=b"{}", headers={"Content-Type": "application/json", "Content-Length": "-5"})
        self.assertNotIn(b"Traceback", body)


class SecretsTests(unittest.TestCase):
    def test_no_hardcoded_secret_key(self):
        import re
        src = (ROOT / "backend" / "app" / "config.py").read_text()
        self.assertIn('os.environ.get("DKA_SECRET_KEY")', src)
        self.assertFalse(re.search(r'SECRET_KEY\s*=\s*["\'][0-9a-fA-F]{16,}', src))


if __name__ == "__main__":
    unittest.main()
