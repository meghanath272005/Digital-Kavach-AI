"""Simulated digital identity + linked accounts with per-platform pseudonyms (HMAC-SHA256).

SIMULATION ONLY - no government identity verification takes place. Aadhaar numbers, biometrics,
documents and OTPs are never requested or stored. The HMAC pseudonym maths is real; the
verification behind it is not.
"""
import hashlib
import hmac
import re
import secrets

SIM_NOTICE = "Simulation only \u2014 no government identity verification has taken place."
CATEGORIES = {
    "personal": "Personal social media",
    "business": "Business or shop",
    "community": "Village or community",
    "religious": "Temple or religious organisation",
    "organisation": "Public service or organisation I represent",
}
PLATFORMS = ["Instagram", "Facebook", "X", "YouTube", "LinkedIn", "WhatsApp Business", "Telegram", "Other demo platform"]
HANDLE_RE = re.compile(r"^[A-Za-z0-9._-]{2,60}$")
ALIAS_RE = re.compile(r"^[A-Za-z0-9 ._-]{0,30}$")
IDENTITY_RE = re.compile(r"^DEMO-[0-9A-F]{8}$")
MAX_ACCOUNTS = 20
ACCOUNT_STATUSES = ["Active (demo)", "Paused (demo)"]

VERIFICATION_STEPS = [
    {"step": "Consent shown", "detail": "You confirmed this is a simulation and that no ID number, photo or OTP is entered."},
    {"step": "Hand-off to an authorised provider (placeholder)",
     "detail": "A real deployment would redirect to an approved identity provider. Nothing is contacted here."},
    {"step": "Provider result (placeholder)",
     "detail": "A real provider would return only pass/fail. Here a scripted 'pass' is generated locally."},
    {"step": "Pseudonymous demo identity created",
     "detail": "A random demo ID and a secret key are generated. The key never leaves the server."},
]


class ValidationError(ValueError):
    def __init__(self, errors):
        super().__init__("validation failed")
        self.errors = errors


class NotFound(LookupError):
    pass


class Conflict(ValueError):
    pass


def _derive_key(server_key: str, identity_secret: bytes) -> bytes:
    return hmac.new(server_key.encode(), identity_secret, hashlib.sha256).digest()


def pseudonym(server_key: str, identity_secret: bytes, platform: str, handle: str) -> str:
    msg = f"{platform.strip().lower()}|{handle.strip().lower()}".encode()
    return "pid_" + hmac.new(_derive_key(server_key, identity_secret), msg, hashlib.sha256).hexdigest()[:20]


def validate_start(data):
    errors = {}
    alias = str(data.get("alias", "") or "").strip()
    if not ALIAS_RE.match(alias):
        errors["alias"] = "Use up to 30 letters, digits, spaces, dots, underscores or hyphens."
    elif re.search(r"\d{6,}", alias.replace(" ", "")) or "@" in alias:
        errors["alias"] = "Do not enter an ID number, phone number or email. Use any nickname."
    if data.get("consent") is not True:
        errors["consent"] = "Tick the box to confirm you understand this is a simulation."
    if errors:
        raise ValidationError(errors)
    return alias


def _public_identity(row, account_count):
    return {"id": row["id"], "alias": row["alias"], "status": row["status"], "created_at": row["created_at"],
            "account_count": account_count, "simulated": True, "notice": SIM_NOTICE,
            "never_collected": ["Aadhaar number or image", "Biometrics", "Identity documents", "OTPs"],
            "platform_sees": ["A per-platform pseudonymous token (pid_...)", "A 'demo-verified person' flag"],
            "platform_does_not_see": ["Legal name", "Aadhaar or any ID number", "Your other accounts on other platforms"]}


def start_identity(db, data):
    alias = validate_start(data)
    iid = "DEMO-" + secrets.token_hex(4).upper()
    with db.tx() as c:
        c.execute("INSERT INTO demo_identities(id, alias, secret) VALUES (?,?,?)", (iid, alias, secrets.token_bytes(32)))
    db.bump("identity_started")
    out = _public_identity(db.one("SELECT * FROM demo_identities WHERE id=?", (iid,)), 0)
    out["steps"] = VERIFICATION_STEPS
    return out


def _identity_row(db, iid):
    if not IDENTITY_RE.match(iid or ""):
        raise NotFound("Identity not found.")
    row = db.one("SELECT * FROM demo_identities WHERE id=?", (iid,))
    if not row:
        raise NotFound("Identity not found.")
    return row


def get_identity(db, iid):
    row = _identity_row(db, iid)
    n = db.one("SELECT COUNT(*) AS n FROM linked_accounts WHERE identity_id=?", (iid,))["n"]
    out = _public_identity(row, n)
    out["steps"] = VERIFICATION_STEPS
    return out


def _public_account(r):
    return {"id": r["id"], "identity_id": r["identity_id"], "category": r["category"],
            "category_label": CATEGORIES.get(r["category"], r["category"]), "platform": r["platform"],
            "handle": r["handle"], "pseudonym": r["pseudonym"], "status": r["status"], "created_at": r["created_at"]}


def list_accounts(db, iid):
    _identity_row(db, iid)
    rows = db.all("SELECT * FROM linked_accounts WHERE identity_id=? ORDER BY id", (iid,))
    return [_public_account(r) for r in rows]


def add_account(db, server_key, iid, data):
    row = _identity_row(db, iid)
    errors = {}
    category = str(data.get("category", ""))
    platform = str(data.get("platform", ""))
    handle = str(data.get("handle", "")).strip().lstrip("@")
    if category not in CATEGORIES:
        errors["category"] = "Choose what this account is used for."
    if platform not in PLATFORMS:
        errors["platform"] = "Choose a platform from the list."
    if not HANDLE_RE.match(handle):
        errors["handle"] = "Use 2-60 letters, digits, dots, underscores or hyphens (a made-up demo handle)."
    if errors:
        raise ValidationError(errors)
    if db.one("SELECT COUNT(*) AS n FROM linked_accounts WHERE identity_id=?", (iid,))["n"] >= MAX_ACCOUNTS:
        raise ValidationError({"handle": f"A demo identity can have at most {MAX_ACCOUNTS} accounts."})
    tok = pseudonym(server_key, bytes(row["secret"]), platform, handle)
    try:
        with db.tx() as c:
            cur = c.execute("INSERT INTO linked_accounts(identity_id,category,platform,handle,pseudonym) VALUES (?,?,?,?,?)",
                            (iid, category, platform, handle, tok))
            new_id = cur.lastrowid
    except Exception as exc:  # UNIQUE(identity_id, platform, handle)
        if "UNIQUE" in str(exc):
            raise Conflict("That platform and handle are already linked.") from None
        raise
    db.bump("account_linked")
    return _public_account(db.one("SELECT * FROM linked_accounts WHERE id=?", (new_id,)))


def get_account(db, iid, aid):
    _identity_row(db, iid)
    r = db.one("SELECT * FROM linked_accounts WHERE id=? AND identity_id=?", (aid, iid))
    if not r:
        raise NotFound("Account not found.")
    return _public_account(r)


def set_account_status(db, iid, aid, status):
    get_account(db, iid, aid)
    if status not in ACCOUNT_STATUSES:
        raise ValidationError({"status": f"Status must be one of: {', '.join(ACCOUNT_STATUSES)}."})
    with db.tx() as c:
        c.execute("UPDATE linked_accounts SET status=? WHERE id=? AND identity_id=?", (status, aid, iid))
    return get_account(db, iid, aid)


def remove_account(db, iid, aid):
    get_account(db, iid, aid)
    with db.tx() as c:
        c.execute("DELETE FROM linked_accounts WHERE id=? AND identity_id=?", (aid, iid))
