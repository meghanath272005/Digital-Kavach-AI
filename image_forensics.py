"""Image checks with Pillow / NumPy / OpenCV.

HONEST SCOPE: this is NOT a deepfake detector. No trained model is used. It runs a few classic,
explainable file-level checks (metadata, Error Level Analysis, face-region detection) and reports raw
measurements. It never outputs a "percent fake" or "percent genuine" figure, and "no indicators
found" never means "authentic". Images are processed in memory and are never written to disk.
"""
import base64
import hashlib
import io

import cv2
import numpy as np
from PIL import ExifTags, Image, ImageChops

Image.MAX_IMAGE_PIXELS = 25_000_000  # decompression-bomb guard

DISCLAIMER = ("Image analysis cannot establish whether an image is genuine or manipulated with complete "
              "certainty. Treat every result as one clue, not proof.")

JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MIN_SIDE, MAX_SIDE = 64, 8000

EDITING_TOOLS = ["photoshop", "lightroom", "gimp", "snapseed", "facetune", "picsart", "canva", "faceapp",
                 "pixelmator", "affinity photo", "capture one", "paint.net", "remini", "meitu", "beautycam"]
AI_TOOLS = ["stable diffusion", "midjourney", "dall-e", "dall·e", "firefly", "comfyui", "automatic1111",
            "novelai", "leonardo.ai", "imagen", "sdxl", "invokeai", "fooocus"]
AI_PNG_KEYS = {"parameters", "prompt", "workflow", "sd-metadata", "invokeai_metadata", "dream"}


class ImageError(ValueError):
    pass


def sniff_format(data: bytes):
    if data.startswith(JPEG_MAGIC):
        return "JPEG"
    if data.startswith(PNG_MAGIC):
        return "PNG"
    return None


def _finding(fid, title, level, detail):
    return {"id": fid, "title": title, "level": level, "detail": detail}


def _metadata(img, raw, fmt):
    findings, facts = [], {}
    software, make, model, has_gps = "", "", "", False
    exif = img.getexif()
    if exif:
        tagmap = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        software = str(tagmap.get("Software", "")).strip()
        make, model = str(tagmap.get("Make", "")).strip(), str(tagmap.get("Model", "")).strip()
        try:
            has_gps = bool(exif.get_ifd(0x8825))
        except Exception:
            has_gps = False
    facts["exif_present"] = bool(exif)
    facts["camera"] = (f"{make} {model}").strip() or None
    facts["software_tag"] = software or None

    text_keys = {str(k).lower(): str(v) for k, v in (img.info or {}).items() if isinstance(k, str)}
    blob = (software + " " + " ".join(text_keys.get(k, "") for k in ("software", "comment", "description", "source"))).lower()

    ai_hit = next((t for t in AI_TOOLS if t in blob), None)
    png_key = next((k for k in text_keys if k in AI_PNG_KEYS), None) if fmt == "PNG" else None
    if ai_hit or png_key:
        what = f"'{ai_hit}'" if ai_hit else f"a '{png_key}' text field used by AI image tools"
        findings.append(_finding("M1", "AI-generation tool recorded in metadata", "notable",
            f"The file's metadata contains {what}. This suggests the image passed through an AI generator. "
            "Metadata can be added or removed by anyone, so it is a clue, not proof."))
    else:
        ed = next((t for t in EDITING_TOOLS if t in blob), None)
        if ed:
            findings.append(_finding("M2", "Editing software recorded in metadata", "notable",
                f"The Software tag mentions '{ed}'. Many harmless photos are edited (crop, colour); this only "
                "shows the file was saved by editing software."))
    if not exif and fmt == "JPEG":
        findings.append(_finding("M3", "No camera (EXIF) metadata", "weak",
            "Most social apps strip metadata when uploading, so this is common and proves nothing alone."))
    elif exif and facts["camera"] and not software:
        findings.append(_finding("M4", "Camera make/model present, no editing software tag", "info",
            f"Recorded camera: {facts['camera']}. This is metadata the file claims; it can be edited."))
    if has_gps:
        findings.append(_finding("M5", "Location data (GPS) is embedded", "info",
            "The image carries location coordinates (not displayed here). Remove them before sharing publicly."))
    if b"c2pa" in raw[:200_000].lower() or b"jumbf" in raw[:200_000].lower():
        findings.append(_finding("M6", "Content Credentials (C2PA) marker found", "info",
            "A provenance marker is present, but this prototype does NOT validate its signature. Use an official "
            "Content Credentials verifier to check it."))
    return findings, facts


def _ela(img_rgb: Image.Image, quality=90):
    buf = io.BytesIO()
    img_rgb.save(buf, "JPEG", quality=quality)
    buf.seek(0)
    resaved = Image.open(buf).convert("RGB")
    diff = ImageChops.difference(img_rgb, resaved)
    arr = np.asarray(diff, dtype=np.float32).mean(axis=2)
    return arr


def _block_stats(arr, grid=12):
    h, w = arr.shape
    bh, bw = max(h // grid, 1), max(w // grid, 1)
    means = []
    for y in range(0, h - bh + 1, bh):
        for x in range(0, w - bw + 1, bw):
            means.append(float(arr[y:y + bh, x:x + bw].mean()))
    means = np.array(means)
    median = float(np.median(means))
    return {"global_mean": float(arr.mean()), "median_block": median, "max_block": float(means.max()),
            "ratio": float(means.max() / max(median, 0.25))}


def _heatmap_data_url(arr):
    mx = float(arr.max())
    scaled = (arr / mx * 255.0) if mx > 0 else arr
    gray = np.clip(scaled, 0, 255).astype(np.uint8)
    colour = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
    h, w = colour.shape[:2]
    if max(h, w) > 640:
        s = 640 / max(h, w)
        colour = cv2.resize(colour, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    ok, png = cv2.imencode(".png", colour)
    return "data:image/png;base64," + base64.b64encode(png.tobytes()).decode()


def detect_faces(bgr):
    try:
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(48, 48))
        if cascade.empty():
            return None
        return [tuple(int(v) for v in f) for f in faces]
    except Exception:
        return None  # detector unavailable: reported honestly, never faked


def _sharpness_ratio(bgr, faces):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    mask = np.zeros(gray.shape, bool)
    for x, y, w, h in faces:
        mask[y:y + h, x:x + w] = True
    if mask.sum() < 500 or (~mask).sum() < 500:
        return None
    face_v, rest_v = float(lap[mask].var()), float(lap[~mask].var())
    return face_v / max(rest_v, 1e-6)


def analyse(raw: bytes, max_bytes: int) -> dict:
    if not raw:
        raise ImageError("The file is empty.")
    if len(raw) > max_bytes:
        raise ImageError(f"File is too large. The maximum is {max_bytes // (1024 * 1024)} MB.")
    fmt = sniff_format(raw)
    if not fmt:
        raise ImageError("Only JPG, JPEG or PNG images are accepted (the file content did not match).")
    try:
        probe = Image.open(io.BytesIO(raw))
        probe.verify()
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        raise ImageError("The image could not be read. It may be corrupted or too large.") from None
    w, h = img.size
    if min(w, h) < MIN_SIDE or max(w, h) > MAX_SIDE:
        raise ImageError(f"Image dimensions must be between {MIN_SIDE}px and {MAX_SIDE}px per side.")

    findings, facts = _metadata(img, raw, fmt)
    rgb = img.convert("RGB")
    bgr = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)

    heatmap, ela = None, None
    if fmt == "JPEG":
        arr = _ela(rgb)
        ela = _block_stats(arr)
        heatmap = _heatmap_data_url(arr)
        if ela["ratio"] >= 4.0 and ela["max_block"] >= 2.0:
            findings.append(_finding("E1", "Uneven recompression error levels", "weak",
                f"One region's error level is {ela['ratio']:.1f}x the typical region. Edited or pasted areas can "
                "show this, but so can sharp edges, text and ordinary textured photos."))
        else:
            findings.append(_finding("E0", "Error levels look fairly even", "info",
                "No region stands out strongly in this simple check. Skilled edits can still pass it."))
    else:
        findings.append(_finding("E2", "Error Level Analysis skipped for PNG", "info",
            "ELA relies on JPEG compression history, which PNG files do not have, so it would be misleading."))

    faces = detect_faces(bgr)
    detector_ok = faces is not None
    faces = faces or []
    facts["faces_detected"] = len(faces)
    facts["face_detector_available"] = detector_ok
    if not detector_ok:
        findings.append(_finding("F3", "Face-region detector unavailable", "info",
            "The OpenCV face detector could not run in this environment, so no face check was performed."))
    elif faces:
        ratio = _sharpness_ratio(bgr, faces)
        findings.append(_finding("F1", f"{len(faces)} face region(s) located", "info",
            "Faces were located with a classic OpenCV detector. This tool does NOT test whether a face is "
            "swapped, synthetic or edited - that needs a trained deepfake model (planned future work)."))
        if ratio is not None and (ratio < 0.15 or ratio > 6.0):
            findings.append(_finding("F2", "Face area differs strongly in sharpness from the rest", "weak",
                f"Face-region detail is {ratio:.2f}x the rest of the image. Composited faces sometimes differ in "
                "sharpness, but portrait blur and beauty filters do too."))
    else:
        findings.append(_finding("F0", "No frontal face region located", "info",
            "Either there is no clear front-facing face or the detector missed it. Face-swap checks are not "
            "performed in this prototype either way."))

    notable = [f for f in findings if f["level"] == "notable"]
    weak = [f for f in findings if f["level"] == "weak" and f["id"] != "M3"]
    if notable:
        verdict = "Indicators found"
        summary = "File metadata points to editing or AI-generation software. That is a clue to investigate, not proof of deception."
    elif weak:
        verdict = "Inconclusive"
        summary = "Only weak, easily-explained signals were found. These checks cannot settle whether the image was altered."
    else:
        verdict = "No indicators found by these limited checks"
        summary = "None of the simple checks flagged anything. This does NOT prove the image is authentic."

    return {
        "verdict": verdict,
        "summary": summary,
        "findings": findings,
        "measurements": {
            "format": fmt, "width": w, "height": h, "megapixels": round(w * h / 1e6, 2),
            "file_size_kb": round(len(raw) / 1024, 1),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "exif_present": facts["exif_present"], "camera": facts["camera"],
            "software_tag": facts["software_tag"], "faces_detected": facts["faces_detected"],
            "ela": ({k: round(v, 2) for k, v in ela.items()} if ela else None),
        },
        "ela_heatmap": heatmap,
        "method": {
            "type": "classical file-level checks", "ml_or_deepfake_model_used": False,
            "libraries": ["Pillow", "NumPy", "OpenCV (Haar face-region detector only)"],
            "not_performed": ["deepfake / face-swap classification", "AI-generated image classification",
                              "reverse image search", "C2PA signature validation"],
        },
        "guidance": [
            "Search for the image with a reverse-image-search tool to see where else it appears.",
            "Check whether trusted news or the named person has posted it on an official account.",
            "Do not forward the image if you are unsure; sharing a fake spreads the harm.",
            "If an image of you was edited or shared without consent, save the link, report it on the platform, "
            "and consider a complaint at cybercrime.gov.in or helpline 1930.",
        ],
        "disclaimer": DISCLAIMER,
        "stored": False,
    }


def make_sample_image() -> bytes:
    """Builds a SYNTHETIC demo JPEG (not a photograph of anyone) so judges can try the pipeline
    without uploading personal images. It is deliberately constructed to trigger the checks: a pasted
    patch with a different compression history, and an editing-software tag."""
    rng = np.random.default_rng(7)
    h, w = 420, 640
    y = np.linspace(0, 1, h)[:, None]
    base = np.zeros((h, w, 3), np.float32)
    base[..., 0] = 90 + 80 * y
    base[..., 1] = 140 + 60 * y
    base[..., 2] = 200 - 70 * y
    img = base + rng.normal(0, 6, base.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)
    cv2.circle(img, (200, 250), 90, (60, 120, 190), -1)
    cv2.rectangle(img, (380, 180), (580, 380), (70, 150, 90), -1)
    cv2.putText(img, "SAMPLE", (60, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255, 255, 255), 3)
    first = io.BytesIO()
    Image.fromarray(img[..., ::-1].copy()).save(first, "JPEG", quality=45)
    first.seek(0)
    comp = np.asarray(Image.open(first).convert("RGB")).copy()
    patch = rng.normal(128, 55, (110, 150, 3))
    patch = cv2.GaussianBlur(np.clip(patch, 0, 255).astype(np.uint8), (3, 3), 0)
    comp[120:230, 330:480] = patch  # "pasted" region that never went through the first compression
    out = Image.fromarray(comp)
    exif = Image.Exif()
    exif[0x0131] = "Adobe Photoshop 25.1 (Synthetic demo tag)"
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=92, exif=exif.tobytes())
    return buf.getvalue()