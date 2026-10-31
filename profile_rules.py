"""Fake-profile risk checker - TRANSPARENT RULES ONLY (no machine learning).

Looks only at text the user typed in. It never opens the URL, never scrapes a
platform and has no access to any platform database.  Every rule that fires is
returned with its points and a plain-language reason.
"""
import re
from urllib.parse import urlparse

DISCLAIMER = "Risk assessment is preliminary and may be incorrect."

KNOWN_PLATFORMS = {
    "instagram.com", "facebook.com", "x.com", "twitter.com", "linkedin.com", "youtube.com",
    "threads.net", "t.me", "telegram.me", "tiktok.com", "snapchat.com", "reddit.com", "github.com",
}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy", "shorturl.at",
              "ow.ly", "tiny.cc", "rebrand.ly"}
STRONG_AUTHORITY = ["official", "verified", "customercare", "helpdesk", "support", "authorised",
                    "authorized", "govt", "realaccount"]
BRAND_TOKENS = {"sbi", "hdfc", "icici", "axisbank", "rbi", "paytm", "phonepe", "amazon", "flipkart",
                "uidai", "irctc", "npci", "epfo", "google", "microsoft", "whatsapp", "instagram",
                "facebook", "police", "incometax", "cybercrime"}

MONEY_LURES = [
    r"guaranteed (returns?|profit)", r"double your money", r"invest(ment)?\b.{0,30}\b(daily|weekly|returns?)",
    r"\bforex\b", r"\bcrypto\b", r"trading signals?", r"earn\s*(rs\.?|₹)?\s*\d[\d,]*\s*(per|a|/)\s*(day|week|hour)",
    r"work from home", r"loan (approval|offer)", r"\bgiveaway\b", r"lucky (winner|draw)", r"send money",
    r"dm (me )?(to|for) (earn|invest|win|join)",
]
OFF_PLATFORM = [r"whats\s?app", r"telegram", r"\bt\.me/", r"wa\.me/", r"\b\d{10}\b", r"\+\d{2}[\s-]?\d{8,10}"]
URGENCY = [r"\burgent(ly)?\b", r"limited time", r"act now", r"\bhurry\b", r"last chance", r"today only"]
AUTHORITY_CLAIMS = [r"official (account|page|handle)", r"\bverified\b", r"government", r"\bgovt\b",
                    r"customer (care|support)", r"support team", r"authori[sz]ed (dealer|partner|agent)",
                    r"\bbank\b"]
TAKEOVER_PATTERNS = [
    r"(old|previous|main|original) (account|profile|id) (was |got |is )?(hacked|blocked|suspended|deleted|disabled)",
    r"\bnew (account|profile|id)\b", r"\bbackup account\b", r"follow (my|this) new",
]
CONCERNING_NOTES = [
    r"asked (me )?(for )?(money|otp|payment|upi|gift cards?)", r"(send|sent|shared) (me )?(a )?(link|qr)",
    r"(copied|stolen|using) (my )?(photos?|pictures?|pics?|images?)", r"blackmail", r"threat(en|s)?",
    r"morph(ed)?", r"pretend(ing)? to be", r"claims? to be", r"impersonat",
]

USERNAME_RE = re.compile(r"^@?[A-Za-z0-9._-]{2,60}$")


# ----------------------------------------------------------------- helpers
def _levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _registered_domain(host: str) -> str:
    labels = host.lower().strip(".").split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else host.lower()


def _find(patterns, text):
    hits = []
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            hits.append(m.group(0).strip())
    return hits


def _severity(points: int) -> str:
    if points >= 20:
        return "high"
    if points >= 10:
        return "medium"
    if points > 0:
        return "low"
    return "info"


def _finding(fid, title, points, detail, field):
    return {"id": fid, "title": title, "points": points, "severity": _severity(points),
            "detail": detail, "field": field}


def normalise_url(raw: str):
    """Returns (parsed_url_or_None, error_message_or_None). Never performs any network request."""
    raw = raw.strip()
    if not raw:
        return None, None
    if len(raw) > 500:
        return None, "Profile URL is too long (500 characters maximum)."
    if re.match(r"^[a-z][a-z0-9+.-]*:", raw, re.I) and not re.match(r"^https?://", raw, re.I):
        return None, "Only http:// or https:// profile URLs are accepted."
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
        host = parsed.hostname
    except ValueError:
        return None, "That does not look like a valid URL."
    if not host or "." not in host:
        return None, "That does not look like a valid URL."
    return parsed, None


def _handle_from_url(parsed):
    host = (parsed.hostname or "").lower()
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None
    if host.endswith("linkedin.com"):
        return parts[1] if parts[0] in ("in", "company", "school") and len(parts) > 1 else None
    first = parts[0]
    if first.lower() in {"profile.php", "channel", "c", "user", "people", "pages", "groups", "p", "reel"}:
        return None
    return first.lstrip("@")


# --------------------------------------------------------------- validation
def validate(data: dict):
    """Returns (clean_dict, field_errors)."""
    errors, clean = {}, {}
    username = str(data.get("username", "")).strip()
    if not username:
        errors["username"] = "Enter the username or handle you want to check."
    elif not USERNAME_RE.match(username):
        errors["username"] = "Use 2-60 letters, digits, dots, underscores or hyphens (an @ prefix is fine)."
    clean["username"] = username.lstrip("@")

    clean["url_raw"] = str(data.get("url", "")).strip()
    parsed, err = normalise_url(clean["url_raw"])
    if err:
        errors["url"] = err
    clean["parsed_url"] = parsed

    for key, limit in (("description", 2000), ("notes", 2000)):
        val = str(data.get(key, "") or "").strip()
        if len(val) > limit:
            errors[key] = f"Keep this under {limit} characters."
        clean[key] = val

    for key in ("account_age_days", "followers", "following"):
        raw = data.get(key)
        if raw in (None, ""):
            clean[key] = None
            continue
        try:
            n = int(raw)
            if n < 0 or n > 1_000_000_000:
                raise ValueError
            clean[key] = n
        except (TypeError, ValueError):
            errors[key] = "Enter a whole number (0 or more)."
            clean[key] = None
    return clean, errors


# ------------------------------------------------------------------ analysis
def analyse(clean: dict) -> dict:
    findings, passed = [], []
    username = clean["username"]
    ulow = username.lower()
    unorm = re.sub(r"[^a-z0-9]", "", ulow)
    tokens = set(t for t in re.split(r"[^a-z]+", ulow) if t)
    desc, notes = clean["description"], clean["notes"]
    desc_low, notes_low = desc.lower(), notes.lower()
    parsed = clean["parsed_url"]

    # ---- username rules
    hits = [w for w in STRONG_AUTHORITY if w in unorm]
    if hits:
        findings.append(_finding("U1", "Username claims authority", 10,
            f"The username contains '{hits[0]}'. Many genuine accounts use such words, but impersonators "
            "use them to look official. Check the account against the organisation's own website.", "username"))
    if re.search(r"\d{4,}$", ulow):
        findings.append(_finding("U2", "Username ends with a long number", 10,
            "Names ending in four or more digits are often auto-generated or throw-away accounts.", "username"))
    if re.search(r"[a-z][013][a-z]", ulow):
        findings.append(_finding("U3", "Digits that look like letters inside the name", 8,
            "Swapping letters for look-alike digits (0 for o, 1 for l, 3 for e) is a common trick to copy a "
            "real name.", "username"))
    if re.search(r"[._-]{2,}|([._-].*){4,}", ulow):
        findings.append(_finding("U4", "Many separators in the username", 5,
            "Repeated dots, underscores or hyphens can be used to create a near-copy of a real handle.", "username"))
    brands = sorted(b for b in BRAND_TOKENS if b in tokens or (len(b) >= 5 and b in unorm))
    if brands:
        findings.append(_finding("U5", "Username contains a well-known organisation name", 12,
            f"The username includes '{brands[0]}'. Accounts using big names are frequently fake. "
            "Genuine ones are normally linked from the organisation's official website.", "username"))
    if not any(f["field"] == "username" for f in findings):
        passed.append("No username warning signs matched (authority words, look-alike digits, brand names).")

    # ---- URL rules
    if parsed:
        host = (parsed.hostname or "").lower()
        reg = _registered_domain(host)
        name = reg.split(".")[0]
        flagged_url = False
        if parsed.scheme != "https":
            flagged_url = True
            findings.append(_finding("L1", "Link is not secure (http)", 8,
                "Genuine major platforms use https. Treat plain http profile links with caution.", "url"))
        if "@" in (parsed.netloc or ""):
            flagged_url = True
            findings.append(_finding("L2", "Link hides the real address with '@'", 25,
                "Text before an '@' in a link can disguise where it really leads.", "url"))
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
            flagged_url = True
            findings.append(_finding("L3", "Link uses a raw IP address", 25,
                "Real social platforms use named domains, not numeric addresses.", "url"))
        if "xn--" in host:
            flagged_url = True
            findings.append(_finding("L4", "Link uses an encoded (punycode) domain", 25,
                "Encoded domains can display look-alike foreign characters that imitate a known site.", "url"))
        if reg in SHORTENERS:
            flagged_url = True
            findings.append(_finding("L5", "Link is a URL shortener", 20,
                "A profile link should point directly at a platform. Shorteners hide the destination.", "url"))
        elif reg not in KNOWN_PLATFORMS:
            flagged_url = True
            lookalike = None
            subst = name.replace("rn", "m").replace("0", "o").replace("1", "l").replace("vv", "w")
            for known in KNOWN_PLATFORMS:
                kn = known.split(".")[0]
                if len(kn) >= 5 and (subst == kn or 1 <= _levenshtein(name, kn) <= 2):
                    lookalike = known
                    break
            embedded = next((k for k in KNOWN_PLATFORMS
                             if len(k.split(".")[0]) >= 5 and k.split(".")[0] in host), None)
            if lookalike:
                findings.append(_finding("L6", "Domain imitates a well-known platform", 30,
                    f"'{reg}' is spelled almost like '{lookalike}'. Do not trust it.", "url"))
            elif embedded:
                findings.append(_finding("L7", "Platform name used inside a different domain", 30,
                    f"The name '{embedded.split('.')[0]}' appears in the address, but the real domain is '{reg}'.", "url"))
            else:
                findings.append(_finding("L8", "Domain is not a platform this tool recognises", 10,
                    f"'{reg}' is not in this prototype's short list of common platforms. It may simply be "
                    "a smaller site - this is a weak signal.", "url"))
        if not flagged_url:
            passed.append(f"Link points to a recognised platform domain ({reg}) over https.")
        handle = _handle_from_url(parsed)
        if handle:
            if handle.lower() != ulow:
                findings.append(_finding("C1", "Handle in the link differs from the username", 15,
                    f"You entered '{username}' but the link's handle is '{handle}'. Inconsistent details "
                    "are a warning sign (or a typo).", "url"))
            else:
                passed.append("The handle inside the link matches the username you entered.")

    # ---- description rules
    if not desc:
        findings.append(_finding("D1", "No profile description supplied", 12,
            "An empty or missing bio gives little to verify. (If you simply did not paste it, add it for a "
            "better assessment.)", "description"))
    elif len(desc) < 20:
        findings.append(_finding("D1", "Very short profile description", 6,
            "Under 20 characters gives little to verify.", "description"))
    else:
        h = _find(AUTHORITY_CLAIMS, desc_low)
        if h:
            findings.append(_finding("D2", "Description makes authority or official claims", 12,
                f"The text says '{h[0]}'. Claims like this are easy to type and should be checked elsewhere.",
                "description"))
        h = _find(MONEY_LURES, desc_low)
        if h:
            findings.append(_finding("D3", "Money-making or investment lure", 25,
                f"The text includes '{h[0]}'. Promises of easy money are the most common profile-based scam.",
                "description"))
        h = _find(OFF_PLATFORM, desc_low)
        if h:
            findings.append(_finding("D4", "Pushes contact off the platform", 10,
                "Moving the chat to WhatsApp, Telegram or a phone number is common in scams, although many "
                "genuine businesses do it too.", "description"))
        h = _find(URGENCY, desc_low)
        if h:
            findings.append(_finding("D5", "Urgency or pressure wording", 8,
                f"The text includes '{h[0]}'. Pressure to act quickly is a manipulation tactic.", "description"))
        h = _find(TAKEOVER_PATTERNS, desc_low)
        if h:
            findings.append(_finding("D6", "'My old account was hacked / this is my new account' pattern", 20,
                "Impersonators often claim the real account was lost so friends follow the fake one. Confirm "
                "through a phone call or another channel.", "description"))
        if re.search(r"https?://\S+|www\.\S+", desc_low):
            for short in SHORTENERS:
                if short in desc_low:
                    findings.append(_finding("D7", "Description contains a shortened link", 15,
                        "Shortened links hide where they lead. Do not open them from an unverified profile.", "description"))
                    break
        if not any(f["field"] == "description" for f in findings):
            passed.append("No description warning signs matched (authority claims, money lures, urgency, "
                          "off-platform contact, 'new account' stories).")

    # ---- supporting information
    age, followers, following = clean["account_age_days"], clean["followers"], clean["following"]
    if age is not None:
        if age < 7:
            findings.append(_finding("S1", "Account is less than a week old", 18,
                "Very new accounts that already claim an established identity deserve extra checking.", "account_age_days"))
        elif age < 30:
            findings.append(_finding("S1", "Account is less than a month old", 12,
                "New accounts are a weak warning sign on their own.", "account_age_days"))
        else:
            passed.append(f"Account age ({age} days) is not unusually new.")
    if followers is not None and following is not None:
        if following >= 1000 and following > 20 * max(followers, 1):
            findings.append(_finding("S2", "Follows far more accounts than follow it", 8,
                "A huge following count with almost no followers is typical of mass-follow or bot-like behaviour.",
                "following"))
    if notes:
        h = _find(CONCERNING_NOTES, notes_low)
        if h:
            findings.append(_finding("S3", "You reported concerning behaviour", 25,
                f"Your notes mention '{h[0]}'. First-hand reports of money requests, copied photos or "
                "threats are strong indicators.", "notes"))

    score = min(100, sum(f["points"] for f in findings))
    dims = sum([bool(parsed), len(desc) >= 20, len(notes) >= 10,
                any(clean[k] is not None for k in ("account_age_days", "followers", "following"))])
    if score >= 40:
        category = "High"
    elif dims < 2 and score < 40:
        category = "Inconclusive"
    elif score >= 15:
        category = "Medium"
    else:
        category = "Low"
    limited = dims < 2 and score >= 40  # high on username alone: say so
    return {
        "category": category,
        "score": score,
        "thresholds": {"low": "0-14", "medium": "15-39", "high": "40 and above"},
        "findings": sorted(findings, key=lambda f: -f["points"]),
        "checks_passed": passed,
        "inputs_considered": [k for k, v in (("username", username), ("url", bool(parsed)),
                              ("description", len(desc) >= 20), ("notes", len(notes) >= 10),
                              ("account details", dims and any(clean[k] is not None for k in
                               ("account_age_days", "followers", "following")))) if v],
        "limited_information": limited or category == "Inconclusive",
        "recommendations": _recommendations(category, findings),
        "method": {"type": "rule-based", "ml_or_llm_used": False,
                   "summary": "Fixed, published rules add points; the total decides the category. "
                              "No model, no scraping, no platform data."},
        "disclaimer": DISCLAIMER,
    }


def _recommendations(category, findings):
    ids = {f["id"] for f in findings}
    recs = []
    if category == "Inconclusive":
        recs.append("Add the profile link, bio text and anything you noticed so the checker has more to work with.")
    if category in ("High", "Medium"):
        recs.append("Do not send money, OTPs, passwords or personal documents to this account.")
        recs.append("Confirm the person or organisation through a channel you already trust (phone call, official website).")
    if ids & {"L2", "L3", "L4", "L5", "L6", "L7", "D7"}:
        recs.append("Do not open the link. Type the platform's address yourself instead.")
    if ids & {"D3", "S3"}:
        recs.append("Stop replying if money or private details were requested, and keep screenshots as evidence.")
    if "D6" in ids:
        recs.append("Ask your real contact on a call whether they really created a new account.")
    if category == "High":
        recs.append("Use the platform's 'Report' tool and consider a complaint at cybercrime.gov.in or helpline 1930.")
    if category == "Low":
        recs.append("A low result does not prove the profile is genuine. Stay careful with any request for money or data.")
    recs.append("This is a preliminary check. A risk score never proves that someone is a criminal - do not accuse anyone publicly.")
    return recs