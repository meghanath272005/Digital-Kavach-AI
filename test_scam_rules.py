import unittest
from tests.helpers import ROOT  # noqa: F401  (sets sys.path)
from app.services import scam_rules, hybrid, content

GENUINE = [
    "HDFC Bank: Rs 2,500.00 debited from a/c XX4821 on 28-Oct via UPI. If not you, call the number on the back of your card. Never share your OTP with anyone.",
    "Your OTP for login is 482913. Do not share this OTP with anyone. Valid for 10 minutes. - Amazon",
    "Dear customer, Rs 15,000 credited to your account XX1234 on 12-Oct-2026. Available balance Rs 52,310. -SBI",
    "Your parcel from Flipkart will be delivered today between 2 PM and 6 PM. Track at flipkart.com/orders",
    "Hi, meeting moved to 4 pm tomorrow. Please bring the printed report.",
]


def cat(text):
    return scam_rules.analyse(text)["category"]


class ScamRuleTests(unittest.TestCase):
    def test_otp_request_is_high(self):
        r = scam_rules.analyse("Dear customer share your OTP now to avoid account blocked immediately")
        self.assertEqual(r["category"], "High")
        self.assertIn("R1", [f["id"] for f in r["findings"]])

    def test_never_share_otp_warning_is_not_a_request(self):
        r = scam_rules.analyse("Never share your OTP with anyone. Do not share your PIN or password with anyone, even bank staff.")
        ids = [f["id"] for f in r["findings"] if f["points"] > 0]
        self.assertNotIn("R1", ids)

    def test_genuine_alerts_never_high(self):
        for m in GENUINE:
            self.assertNotEqual(cat(m), "High", m)
            self.assertNotEqual(hybrid.analyse(m)["category"], "High", m)

    def test_urgency_prize_payment_job_threat_remote(self):
        self.assertIn("R2", [f["id"] for f in scam_rules.analyse("Act now! Your account will be blocked today")["findings"]])
        self.assertIn("R5", [f["id"] for f in scam_rules.analyse("Congratulations you have won a lottery prize")["findings"]])
        self.assertIn("R3", [f["id"] for f in scam_rules.analyse("Pay a processing fee of Rs 4999 to release the amount")["findings"]])
        self.assertIn("R10", [f["id"] for f in scam_rules.analyse("Work from home part-time job, earn Rs 5000 per day")["findings"]])
        self.assertIn("R8", [f["id"] for f in scam_rules.analyse("A case registered against you. Digital arrest, stay on video call")["findings"]])
        self.assertIn("R9", [f["id"] for f in scam_rules.analyse("Please install AnyDesk so we can fix your account")["findings"]])

    def test_confidential_info_and_org_impersonation(self):
        r = scam_rules.analyse("SBI: update your KYC. Send your Aadhaar and PAN card number immediately")
        ids = [f["id"] for f in r["findings"]]
        self.assertIn("R6", ids); self.assertIn("R7", ids)

    def test_links_are_defanged_and_never_fetched(self):
        r = scam_rules.analyse("Verify now at http://sbi-kyc-update.xyz/login")
        self.assertTrue(r["links"])
        shown = r["links"][0]["display"]
        self.assertTrue(shown.startswith("hxxp://"))
        self.assertNotIn("http://", shown)
        self.assertIn("[.]", shown)
        self.assertTrue(r["links"][0]["reasons"])

    def test_inconclusive_for_very_short_text(self):
        self.assertEqual(cat("hi"), "Inconclusive")

    def test_scores_capped_and_explanations_present(self):
        r = scam_rules.analyse(content.SAMPLES["scam"][1]["text"])
        self.assertLessEqual(r["score"], 100)
        for f in r["findings"]:
            self.assertTrue(f["explanation"])
        self.assertIn("preliminary", r["disclaimer"])

    def test_sample_scams_high(self):
        for s in content.SAMPLES["scam"]:
            expected_high = s["label"] != "Genuine-style alert"
            self.assertEqual(cat(s["text"]) == "High", expected_high, s["label"])


if __name__ == "__main__":
    unittest.main()
