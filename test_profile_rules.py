import unittest
from tests.helpers import ROOT  # noqa: F401
from app.services import profile_rules, content


def run(sample):
    clean, errors = profile_rules.validate(sample)
    assert not errors, errors
    return profile_rules.analyse(clean)


class ProfileTests(unittest.TestCase):
    def test_suspicious_sample_is_high_with_reasons(self):
        r = run(content.SAMPLES["profile"][0])
        self.assertEqual(r["category"], "High")
        for f in r["findings"]:
            self.assertTrue(f["detail"]); self.assertGreater(f["points"], 0)
        self.assertEqual(r["disclaimer"], "Risk assessment is preliminary and may be incorrect.")

    def test_ordinary_sample_is_low(self):
        self.assertEqual(run(content.SAMPLES["profile"][1])["category"], "Low")

    def test_too_little_information_is_inconclusive(self):
        r = run(content.SAMPLES["profile"][2])
        self.assertEqual(r["category"], "Inconclusive"); self.assertTrue(r["limited_information"])

    def test_lookalike_domain_and_ratio_rules(self):
        r = run({"username": "shop_helper", "url": "http://instagrarn.com/shop_helper", "description": "Guaranteed returns, DM on WhatsApp",
                 "notes": "", "account_age_days": 2, "followers": 5, "following": 3000})
        ids = {f["id"] for f in r["findings"]}
        self.assertIn("L6", ids)
        self.assertGreaterEqual(len(ids), 4)

    def test_validation_errors(self):
        _, e = profile_rules.validate({"username": "", "url": "javascript:alert(1)", "followers": "abc", "account_age_days": -5})
        self.assertIn("username", e); self.assertIn("url", e); self.assertIn("followers", e); self.assertIn("account_age_days", e)

    def test_url_is_never_fetched(self):
        import socket
        real = socket.socket
        def boom(*a, **k): raise AssertionError("network access attempted")
        socket.socket = boom
        try:
            run(content.SAMPLES["profile"][0])
        finally:
            socket.socket = real


if __name__ == "__main__":
    unittest.main()
