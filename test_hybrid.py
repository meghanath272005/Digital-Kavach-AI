import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT  # noqa: F401
from app.services import hybrid


class HybridTests(unittest.TestCase):
    def tearDown(self):
        hybrid.load_model("/nonexistent/model.joblib")

    def test_no_model_says_so_honestly(self):
        hybrid.load_model("/nonexistent/model.joblib")
        r = hybrid.analyse("Hello, see you at the temple committee meeting on Sunday morning.")
        self.assertFalse(r["ml"]["available"])
        self.assertFalse(r["method"]["ml_or_llm_used"])

    def _tiny_model(self):
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        X = ["zzzword offer zzzword zzzword", "zzzword zzzword win zzzword", "see you at lunch tomorrow", "meeting moved to monday morning",
             "zzzword zzzword zzzword", "please bring the report to class"]
        y = [1, 1, 0, 0, 1, 0]
        m = Pipeline([("t", TfidfVectorizer()), ("c", LogisticRegression(C=50))]).fit(X, y)
        path = Path(tempfile.mkdtemp()) / "m.joblib"
        joblib.dump(m, path)
        return str(path)

    def test_ml_alone_raises_to_medium_never_high(self):
        # NOTE: a TINY synthetic model, used only to test the combination logic. Not a real scam model.
        self.assertTrue(hybrid.load_model(self._tiny_model()))
        r = hybrid.analyse("zzzword zzzword zzzword zzzword zzzword")
        self.assertTrue(r["ml"]["available"])
        self.assertEqual(r["rule_category"], "Low")
        self.assertEqual(r["category"], "Medium")
        self.assertTrue(r["ml_raised_category"])
        self.assertNotEqual(r["category"], "High")

    def test_rules_still_decide_high(self):
        self.assertTrue(hybrid.load_model(self._tiny_model()))
        r = hybrid.analyse("Share the OTP immediately or your account will be blocked http://x-y-z.xyz")
        self.assertEqual(r["category"], "High")

    def test_bad_model_file_fails_safe(self):
        bad = Path(tempfile.mkdtemp()) / "bad.joblib"
        bad.write_bytes(b"not a model")
        self.assertFalse(hybrid.load_model(str(bad)))
        self.assertFalse(hybrid.analyse("hello there my friend, how are you doing")["ml"]["available"])


if __name__ == "__main__":
    unittest.main()
