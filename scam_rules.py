"""Scam-message detector - TRANSPARENT RULES ONLY (no ML, no LLM).

Links found in a message are only *described* (defanged). They are never opened,
resolved or fetched by this code.
"""
import re
from urllib.parse import urlparse

DISCLAIMER = "Risk assessment is preliminary and may be incorrect. Rules mainly cover English and some Hinglish."

SENSITIVE = r"(otp|one[- ]time (password|pin|code)|password|passcode|\bpin\b|cvv|cvc|mpin|upi pin|secret code|verification code)"
REQUEST_VERB = r"(share|send|tell|give|provide|enter|reply(?: with)?|forward|confirm|verify|submit|read out|type)"
NEGATION = re.compile(r"(do not|don't|dont|never|not to|won't ask|will never ask|nobody should)\W+(\w+\W+){0,3}$", re.I)

ORGS = [
    "sbi", "state bank", "hdfc", "icici", "axis bank", "kotak", "punjab national bank", "rbi",
    "reserve bank", "uidai", "aadhaar", "aadhar", "income tax", "it department", "police", "cbi",
    "customs", "trai", "department of telecom", "fedex", "dhl", "blue ?dart", "electricity board",
    "amazon", "flipkart", "paytm", "phonepe", "npci", "epfo", "irctc", "microsoft", "customer care",
    "cyber ?crime", "narcotics",
]
OFFICIAL_DOMAINS = {
    "sbi": ["sbi.co.in", "onlinesbi.sbi"], "hdfc": ["hdfcbank.com"], "icici": ["icicibank.com"],
    "amazon": ["amazon.in", "amazon.com"], "flipkart": ["flipkart.com"], "paytm": ["paytm.com"],
    "phonepe": ["phonepe.com"], "irctc": ["irctc.co.in"], "uidai": ["uidai.gov.in"],
    "rbi": ["rbi.org.in"], "epfo": ["epfindia.gov.in"],
}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy", "shorturl.at",
              "ow.ly", "tiny.cc", "rebrand.ly", "wa.me"}
SUSPICIOUS_TLDS = {"xyz", "top", "click", "icu", "tk", "ml", "ga", "cf", "gq", "buzz", "cyou", "work",
                   "rest", "support", "zip", "mov", "sbs", "cfd"}
COMMON_TLDS = "ly|gl|cc|com|in|net|org|co|info|xyz|top|click|icu|tk|ml|ga|cf|gq|buzz|cyou|work|rest|support|me|io|link|live|online|site|shop|sbs|cfd"
URL_RE = re.compile(
    rf"(https?://[^\s<>\"']+|www\.[^\s<>\"']+|\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:{COMMON_TLDS})(?:/[^\s<>\"']*)?(?![a-z0-9@]))",
    re.I,
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")


def _defang(url: str) -> str:
    return url.replace("http", "hxxp", 1).replace(".", "[.]")


def _rule(rid, title, points, explanation, evidence, kind="rule"):
    sev = "high" if points >= 25 else "medium" if points >= 15 else "low"
    return {"id": rid, "title": title, "points": points, "severity": sev,
            "explanation": explanation, "evidence": evidence[:5]}


def _not_negated(text: str, match: re.Match) -> bool:
    return not NEGATION.search(text[max(0, match.start() - 40):match.start()])


def _requests(text, noun_pattern):
    out = []
    pat = re.compile(rf"\b{REQUEST_VERB}\b\W+(?:\w+\W+){{0,5}}?{noun_pattern}", re.I)
    for m in pat.finditer(text):
        if _not_negated(text, m):
            out.append(m.group(0))
    return out


def analyse_links(text):
    links, seen = [], set()
    for m in URL_RE.finditer(text):
        raw = m.group(0).rstrip(".,);:!?")
        if EMAIL_RE.fullmatch(raw) or raw.lower() in seen:
            continue
        seen.add(raw.lower())
        candidate = raw if re.match(r"https?://", raw, re.I) else "http://" + raw
        try:
            p = urlparse(candidate)
            host = (p.hostname or "").lower()
        except ValueError:
            continue
        if not host or "." not in host:
            continue
        labels = host.split(".")
        reg = ".".join(labels[-2:])
        tld = labels[-1]
        reasons = []
        if raw.lower().startswith("http://"):
            reasons.append("uses unencrypted http")
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
            reasons.append("uses a raw IP address")
        if "xn--" in host:
            reasons.append("uses an encoded (punycode) domain")
        if reg in SHORTENERS:
            reasons.append("is a link shortener that hides the destination")
        if tld in SUSPICIOUS_TLDS:
            reasons.append(f"ends in .{tld}, an extension frequently abused in scams")
        if host.count("-") >= 2:
            reasons.append("has many hyphens, common in fake 'verification' sites")
        for brand, domains in OFFICIAL_DOMAINS.items():
            if brand in host and reg not in domains:
                reasons.append(f"mentions '{brand}' but is not that organisation's known domain ({domains[0]})")
                break
        links.append({"display": _defang(raw), "host_defanged": host.replace(".", "[.]"), "reasons": reasons})
    return links


def validate(data: dict):
    text = str(data.get("message", ""))
    if not text.strip():
        return None, {"message": "Paste the message you want to check."}
    if len(text) > 5000:
        return None, {"message": "Keep the message under 5,000 characters."}
    return text.strip(), {}


def analyse(text: str) -> dict:
    low = text.lower()
    findings = []

    # 1. OTP / password requests (ignores 'never share your OTP' style warnings)
    reqs = _requests(low, SENSITIVE)
    if reqs:
        findings.append(_rule("R1", "Asks for an OTP, PIN or password", 40,
            "No genuine bank, government office or delivery company asks you to share OTPs, PINs or passwords "
            "by message or call.", reqs))
    elif re.search(SENSITIVE, low):
        findings.append({"id": "R1i", "title": "Mentions OTP / PIN / password but does not appear to ask for it", "points": 0,
            "severity": "info", "explanation": "Genuine alerts often say 'never share your OTP'. Still confirm the sender.",
            "evidence": [re.search(SENSITIVE, low).group(0)]})

    # 2. Urgency
    urg_txt = [m.group(0) for m in re.finditer(
        r"\burgent(ly)?\b|immediately|within \d+\s*(hours?|hrs?|minutes?|mins?)|last chance|act now|"
        r"expires? (today|soon|tonight)|final notice|(account|card|sim|number|service)\W+(\w+\W+){0,3}"
        r"(blocked|suspended|closed|deactivated|disconnected)|today only|\basap\b|turant|jaldi", low)]
    if urg_txt:
        findings.append(_rule("R2", "Creates urgency or threatens to block something", 15,
            "Scammers rush you so you do not stop to verify.", urg_txt))

    # 3. Payment requests
    pay = [m.group(0) for m in re.finditer(
        r"\b(pay|transfer|send|deposit|remit|clear)\b\W+(?:\w+\W+){0,4}?(rs\.?|₹|inr|\$|usd|money|amount|fee|charges?|payment)"
        r"|(processing|registration|clearance|customs|delivery|release|refundable|security) (fee|charges?|deposit)"
        r"|gift cards?|scan (this |the )?qr|enter (your )?(upi )?pin to receive", low)
        if _not_negated(low, m)]
    if pay:
        findings.append(_rule("R3", "Requests a payment or fee", 25,
            "Upfront fees, gift cards and 'scan this QR / enter PIN to receive money' are classic fraud steps. "
            "You never enter a PIN to receive money.", pay))

    # 4. Links
    links = analyse_links(text)
    if links:
        extra = sum(1 for l in links if l["reasons"])
        pts = min(35, 10 + 12 * extra) if extra else 10
        findings.append(_rule("R4", "Contains link(s) - not opened by this tool" if not extra
                              else "Contains suspicious-looking link(s) - not opened by this tool", pts,
            "Scam links imitate banks and delivery firms to steal logins. This tool only inspects the text of the "
            "link; it never visits it.", [f"{l['display']}: {', '.join(l['reasons']) or 'no technical red flags in the text'}" for l in links]))

    # 5. Prizes
    prize = [m.group(0) for m in re.finditer(
        r"you(?:'ve| have)? (won|been selected|are selected)|lucky (draw|winner)|congratulations|lottery|jackpot|"
        r"\bprize\b|free (gift|iphone|recharge|laptop)|cashback of|\bkbc\b|inaam|you are (the )?winner", low)]
    if prize:
        findings.append(_rule("R5", "Unrealistic prize or reward claim", 30,
            "You cannot win a contest you never entered. Prizes that need a 'fee' or 'verification' are scams.", prize))

    # 6. Confidential-information requests
    conf = _requests(low, r"(aadhaar|aadhar|pan( card| number)?|card number|account number|bank details|date of birth|dob|selfie|photo id|passport|login (id|details))")
    if not conf:
        conf = [m.group(0) for m in re.finditer(r"(update|verify|complete) (your )?(kyc|aadhaar|pan)", low) if _not_negated(low, m)]
    if conf:
        findings.append(_rule("R6", "Asks for confidential or identity information", 30,
            "Requests to 'update KYC', or to send Aadhaar, PAN or card details by message are a common route to identity theft.", conf))

    # 7. Impersonation of official organisations
    orgs = []
    for o in ORGS:
        m = re.search(rf"\b{o}\b", low)
        if m:
            orgs.append(m.group(0))
    claims = re.search(r"your (kyc|parcel|package|sim)\b|kyc (is |has |was )?(expired|pending|suspended|incomplete)", low)
    if orgs and (claims or links or reqs or pay or conf or urg_txt):
        findings.append(_rule("R7", "May be impersonating an official organisation", 20,
            "The message names an organisation and also pressures or asks you to act. Anyone can type a bank's "
            "name - contact the organisation using the number on its official website or your card.", sorted(set(orgs))))
    elif orgs:
        findings.append({"id": "R7i", "title": "Mentions an organisation (no suspicious request found)", "points": 0,
            "severity": "info", "explanation": "Naming a company is not suspicious by itself.", "evidence": sorted(set(orgs))[:5]})

    # 8. Extra patterns
    threat = [m.group(0) for m in re.finditer(
        r"digital arrest|arrest warrant|case (has been )?registered against you|parcel (contains|has been seized|seized)|"
        r"legal action|court notice|narcotics|money laundering", low)]
    if threat:
        findings.append(_rule("R8", "Threat of arrest or legal action", 25,
            "'Digital arrest' does not exist. Police and courts do not demand payment or video calls to avoid arrest.", threat))
    remote = [m.group(0) for m in re.finditer(r"anydesk|teamviewer|quick ?support|rustdesk|screen ?shar(e|ing)|install (this |the )?(app|apk)|\.apk\b", low)]
    if remote:
        findings.append(_rule("R9", "Asks you to install an app or share your screen", 25,
            "Remote-access apps let a scammer see your screen and approve payments.", remote))
    job = [m.group(0) for m in re.finditer(r"work from home|part[- ]time job|earn\s*(rs\.?|₹)?\s*\d[\d,]*\s*(per|a|/)\s*day|like and subscribe|task (based )?(job|work)", low)]
    if job:
        findings.append(_rule("R10", "Easy-money job offer", 20,
            "Unsolicited 'earn daily' jobs that ask for a deposit or tasks are common advance-fee scams.", job))

    score = min(100, sum(f["points"] for f in findings))
    flagged = [f for f in findings if f["points"] > 0]
    if len(text) < 25 and not flagged:
        category = "Inconclusive"
    elif score >= 40:
        category = "High"
    elif score >= 15:
        category = "Medium"
    else:
        category = "Low"

    return {
        "category": category,
        "score": score,
        "thresholds": {"low": "0-14", "medium": "15-39", "high": "40 and above"},
        "findings": sorted(findings, key=lambda f: -f["points"]),
        "links": links,
        "recommendations": _recommendations(category, flagged, bool(links)),
        "method": {"type": "rule-based", "ml_or_llm_used": False,
                   "summary": "Keyword and pattern rules written by the team. No machine-learning model or LLM "
                              "reads your message. Text is not stored."},
        "limitations": [
            "Rules can miss new scam wording, other languages and images or voice notes.",
            "Rules can also flag genuine messages that happen to use similar words.",
        ],
        "disclaimer": DISCLAIMER,
    }


def _recommendations(category, flagged, has_links):
    ids = {f["id"] for f in flagged}
    recs = []
    if category == "Inconclusive":
        recs.append("The message is too short to judge. Paste the full text, including any links.")
    if has_links:
        recs.append("Do not tap or open the link. If you think the message is real, type the organisation's website address yourself.")
    if "R1" in ids:
        recs.append("Never share an OTP, PIN or password with anyone, even if they say they are from your bank.")
    if ids & {"R3", "R10"}:
        recs.append("Do not pay any fee to receive a prize, refund, loan or job. Genuine ones do not ask for it.")
    if ids & {"R7", "R6", "R8"}:
        recs.append("Call the organisation on the number printed on your card, bill or official website - not the number in the message.")
    if "R9" in ids:
        recs.append("Do not install any app or share your screen at the sender's request.")
    if category in ("High", "Medium"):
        recs.append("If money was already sent, call the National Cyber Crime Helpline 1930 immediately and report at cybercrime.gov.in.")
        recs.append("Block the sender and keep a screenshot as evidence.")
    if category == "Low":
        recs.append("No strong warning signs were found, but that does not prove the message is safe. Verify unexpected requests.")
    return recs