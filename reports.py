"""Impersonation reports kept ONLY in the local demo database. Never sent to any platform or authority."""
import re
import secrets
from datetime import datetime, timezone

from .identity import NotFound, ValidationError

NOT_SENT_NOTICE = ("Your report is not sent anywhere. This prototype does not submit reports to any social media "
                   "platform or to law enforcement. To report for real, use the platform's own Report option and "
                   "file a complaint at cybercrime.gov.in or call 1930.")
REPORT_TYPES = ["Fake profile using my identity", "Profile impersonating someone I know",
                "Profile impersonating an organisation or business", "Manipulated or deepfake image/video of me",
                "Scam or fraud through a profile", "Harassment through a fake account", "Other"]
PLATFORMS = ["Instagram", "Facebook", "X", "YouTube", "LinkedIn", "WhatsApp", "Telegram", "Other"]
STATUSES = ["Submitted", "Under Review", "Additional Information Required", "Resolved"]
REF_RE = re.compile(r"^DKA-\d{8}-[0-9A-F]{10}$")
USERNAME_RE = re.compile(r"^@?[A-Za-z0-9._-]{2,60}$")
CONTACT_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$|^\+?[0-9][0-9 -]{6,17}$")
SENSITIVE_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b|\b(?:\d[ -]?){13,19}\b")
STEP_NOTES = {
    "Submitted": "Report validated and saved in this prototype's local database.",
    "Under Review": "Simulated step: a real service would assign a reviewer. No review is happening.",
    "Additional Information Required": "Simulated step: a real service might ask for more evidence.",
    "Resolved": "Simulated step: shown only to demonstrate the timeline. Nothing was actioned anywhere.",
}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"


def validate(data):
    errors, clean = {}, {}

    def text(key, limit, required=False, msg=None):
        val = str(data.get(key, "") or "").strip()
        if required and not val:
            errors[key] = msg or "This field is required."
        elif len(val) > limit:
            errors[key] = f"Keep this under {limit} characters."
        clean[key] = val
        return val

    name = text("reporter_name", 80)
    if name and not re.match(r"^[^<>]{1,80}$", name):
        errors["reporter_name"] = "Remove special characters such as < and >."
    contact = text("contact", 120)
    if contact and not CONTACT_RE.match(contact):
        errors["contact"] = "Enter a valid email address or phone number, or leave this blank."
    user = text("username", 120, True, "Enter the impersonating username.")
    if user and not USERNAME_RE.match(user):
        errors["username"] = "Use 2-60 letters, digits, dots, underscores or hyphens (an @ prefix is fine)."
    clean["username"] = user.lstrip("@")
    plat = str(data.get("platform", ""))
    if plat not in PLATFORMS:
        errors["platform"] = "Choose the platform."
    clean["platform"] = plat
    url = text("profile_url", 500)
    if url and not re.match(r"^https?://[^\s<>\"']+$", url, re.I):
        errors["profile_url"] = "Enter a link that starts with http:// or https://, or leave this blank."
    rtype = str(data.get("report_type", ""))
    if rtype not in REPORT_TYPES:
        errors["report_type"] = "Choose the type of impersonation."
    clean["report_type"] = rtype
    desc = text("description", 2000, True, "Describe what happened in at least 20 characters.")
    if desc and len(desc) < 20 and "description" not in errors:
        errors["description"] = "Describe what happened in at least 20 characters."
    ev = text("evidence_description", 2000)
    for key, val in (("description", desc), ("evidence_description", ev)):
        if val and SENSITIVE_RE.search(val) and key not in errors:
            errors[key] = "This looks like an Aadhaar or card number. Remove it - never enter these here."
    if errors:
        raise ValidationError(errors)
    return clean


def submit(db, data):
    c = validate(data)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    for _ in range(5):
        ref = f"DKA-{stamp}-{secrets.token_hex(5).upper()}"
        if not db.one("SELECT 1 FROM impersonation_reports WHERE reference_id=?", (ref,)):
            break
    now = _now()
    with db.tx() as conn:
        conn.execute("INSERT INTO impersonation_reports(reference_id,reporter_name,contact,username,platform,profile_url,"
                     "report_type,description,evidence_description,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     (ref, c["reporter_name"], c["contact"], c["username"], c["platform"], c["profile_url"],
                      c["report_type"], c["description"], c["evidence_description"], "Submitted", now, now))
        conn.execute("INSERT INTO report_status_history(reference_id,status,note,changed_at) VALUES (?,?,?,?)",
                     (ref, "Submitted", STEP_NOTES["Submitted"], now))
    db.bump("report_submitted")
    out = lookup(db, ref)
    out["message"] = "Report saved locally. Keep this reference ID."
    return out


def lookup(db, ref):
    """Returns status and timeline only - never the report text, contact or evidence."""
    ref = (ref or "").strip().upper()
    if not REF_RE.match(ref):
        raise ValidationError({"reference_id": "Reference IDs look like DKA-20261030-3FF2E0961A."})
    row = db.one("SELECT reference_id, report_type, platform, status, created_at, updated_at FROM impersonation_reports "
                 "WHERE reference_id=?", (ref,))
    if not row:
        raise NotFound("No demonstration report was found with that reference ID.")
    hist = db.all("SELECT status, note, changed_at FROM report_status_history WHERE reference_id=? ORDER BY id", (ref,))
    done = {h["status"] for h in hist}
    timeline = [{"status": s, "reached": s in done, "note": next((h["note"] for h in hist if h["status"] == s), ""),
                 "at": next((h["changed_at"] for h in hist if h["status"] == s), None)} for s in STATUSES]
    return {"reference_id": row["reference_id"], "report_type": row["report_type"], "platform": row["platform"],
            "status": row["status"], "created_at": row["created_at"], "updated_at": row["updated_at"],
            "timeline": timeline, "stored_locally_only": True, "sent_to_platform_or_authority": False,
            "notice": "Demonstration status only. This report has NOT been sent to any platform or authority.",
            "can_simulate_next_step": row["status"] != STATUSES[-1]}


def advance(db, ref):
    """DEMO ONLY: moves the report to the next status so judges can see the timeline. No real review exists."""
    cur = lookup(db, ref)
    idx = STATUSES.index(cur["status"])
    if idx >= len(STATUSES) - 1:
        raise ValidationError({"reference_id": "This report is already at the final status."})
    nxt, now = STATUSES[idx + 1], _now()
    with db.tx() as conn:
        conn.execute("UPDATE impersonation_reports SET status=?, updated_at=? WHERE reference_id=?", (nxt, now, cur["reference_id"]))
        conn.execute("INSERT INTO report_status_history(reference_id,status,note,changed_at) VALUES (?,?,?,?)",
                     (cur["reference_id"], nxt, STEP_NOTES[nxt], now))
    return lookup(db, ref)
