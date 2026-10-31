import io
import unittest

from PIL import Image
from tests.helpers import ROOT  # noqa: F401
from app.services import image_forensics as ifx

MAX = 5 * 1024 * 1024


def png_bytes(size=(120, 90), color=(10, 120, 200), **save):
    b = io.BytesIO(); Image.new("RGB", size, color).save(b, "PNG", **save); return b.getvalue()


def jpg_bytes(size=(200, 150), exif=None):
    b = io.BytesIO(); Image.new("RGB", size, (200, 80, 40)).save(b, "JPEG", quality=85, **({"exif": exif} if exif else {})); return b.getvalue()


class ImageTests(unittest.TestCase):
    def test_sample_has_expected_outputs(self):
        r = ifx.analyse(ifx.make_sample_image(), MAX)
        self.assertEqual(r["measurements"]["format"], "JPEG")
        self.assertEqual(len(r["measurements"]["sha256"]), 64)
        self.assertTrue(r["ela_heatmap"].startswith("data:image/png;base64,"))
        self.assertTrue(any(f["id"] == "M2" for f in r["findings"]))
        self.assertFalse(r["stored"]); self.assertFalse(r["method"]["ml_deepfake_model_used"] if "ml_deepfake_model_used" in r["method"] else r["method"]["ml_or_deepfake_model_used"])

    def test_no_scores_or_percentages(self):
        r = ifx.analyse(jpg_bytes(), MAX)
        text = str(r).lower()
        for bad in ("percent fake", "% fake", "confidence", "authentic:"):
            self.assertNotIn(bad, text)
        self.assertIn("cannot establish", r["disclaimer"])

    def test_png_skips_ela(self):
        r = ifx.analyse(png_bytes(), MAX)
        self.assertIsNone(r["ela_heatmap"]); self.assertTrue(any(f["id"] == "E2" for f in r["findings"]))

    def test_type_checked_by_content_not_name(self):
        with self.assertRaises(ifx.ImageError):
            ifx.analyse(b"GIF89a" + b"\x00" * 200, MAX)
        with self.assertRaises(ifx.ImageError):
            ifx.analyse(b"<html><script>alert(1)</script></html>", MAX)

    def test_size_and_empty_and_corrupt(self):
        with self.assertRaises(ifx.ImageError): ifx.analyse(b"", MAX)
        with self.assertRaises(ifx.ImageError): ifx.analyse(png_bytes(), 100)
        with self.assertRaises(ifx.ImageError): ifx.analyse(b"\x89PNG\r\n\x1a\n" + b"junk" * 50, MAX)

    def test_tiny_dimensions_rejected(self):
        with self.assertRaises(ifx.ImageError): ifx.analyse(png_bytes(size=(20, 20)), MAX)

    def test_editing_software_metadata_detected(self):
        ex = Image.Exif(); ex[0x0131] = "GIMP 2.10"
        r = ifx.analyse(jpg_bytes(exif=ex.tobytes()), MAX)
        self.assertIn("gimp", r["measurements"]["software_tag"].lower())
        self.assertTrue(any(f["level"] == "notable" for f in r["findings"]))

    def test_nothing_written_to_disk(self):
        import os, tempfile
        before = set(os.listdir(tempfile.gettempdir()))
        ifx.analyse(ifx.make_sample_image(), MAX)
        self.assertEqual(set(os.listdir(tempfile.gettempdir())) - before, set())


if __name__ == "__main__":
    unittest.main()
