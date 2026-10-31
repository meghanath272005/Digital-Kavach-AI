"""Captures real screenshots of the RUNNING app with headless Chromium (Playwright).
Usage: python scripts/capture_screenshots.py [base_url]   (server must already be running)"""
import sys, pathlib
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8123"
OUT = pathlib.Path(__file__).resolve().parents[1] / "screenshots"
OUT.mkdir(exist_ok=True)
errors = []

def run():
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1366, "height": 860})
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(("console", m.text)) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(("pageerror", str(e))))
        def shot(name):
            # Resize the viewport to the page height so the sticky sidebar renders at the top like in real use.
            page.evaluate("window.scrollTo(0,0); document.getElementById('toast').hidden = true")
            h = page.evaluate("document.documentElement.scrollHeight + 40")
            page.set_viewport_size({"width": 1366, "height": max(860, h)}); page.wait_for_timeout(150)
            page.screenshot(path=str(OUT / name)); page.set_viewport_size({"width": 1366, "height": 860})
        def go(route):
            page.goto(f"{BASE}/#/{route}"); page.wait_for_load_state("networkidle"); page.wait_for_timeout(300)
        # dashboard with live scam check
        go("dashboard"); page.click("text=Use sample scam"); page.wait_for_selector(".hero .risk-badge")
        shot("01-desktop-dashboard.png")
        # identity
        go("identity"); page.screenshot(path=str(OUT / "02a-identity-start.png"))
        page.check("#consent"); page.fill("#alias", "DemoAsha"); page.click("text=Start demo verification"); page.wait_for_selector(".id-box")
        shot("02-digital-identity.png")
        # linked accounts
        go("accounts"); page.click("text=Load 5 sample accounts"); page.wait_for_selector(".account")
        shot("03-linked-accounts.png")
        # fake profile
        go("profile"); page.click("text=Suspicious sample profile"); page.click("text=Check profile"); page.wait_for_selector(".risk-badge")
        shot("04-fake-profile-checker.png")
        # image analysis
        go("image"); page.click("text=Use synthetic sample image"); page.wait_for_selector(".preview img"); page.click("text=Start analysis"); page.wait_for_selector(".img-pair")
        page.wait_for_timeout(400); shot("05-image-analysis.png")
        # scam detector
        go("scam"); page.click("text=Bank KYC phishing"); page.click("button:has-text('Analyse message')"); page.wait_for_selector(".risk-badge")
        shot("06-scam-detector.png")
        go("scam"); page.click("text=Genuine-style alert"); page.click("button:has-text('Analyse message')"); page.wait_for_selector(".risk-badge")
        shot("06b-scam-genuine-alert-not-high.png")
        # report: validation errors then success
        go("report"); page.click("button:has-text('Submit report')"); page.wait_for_selector(".err")
        page.screenshot(path=str(OUT / "07a-report-validation.png"))
        page.click("text=Fill a sample impersonation report"); page.click("button:has-text('Submit report')"); page.wait_for_selector(".ref-chip")
        page.click("text=Simulate next review step"); page.wait_for_timeout(300)
        shot("07-report-submission.png")
        for name, route in (("08-safety", "safety"), ("09-how-demo-works", "how"), ("10-future-development", "future")):
            go(route); shot(f"{name}.png")
        go("dashboard"); page.click("text=Use sample scam"); page.wait_for_selector(".hero .risk-badge")
        shot("01b-desktop-dashboard-with-activity.png")
        # mobile
        m = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        mp = m.new_page(); mp.on("pageerror", lambda e: errors.append(("mobile-pageerror", str(e))))
        mp.goto(f"{BASE}/#/dashboard"); mp.wait_for_load_state("networkidle"); mp.wait_for_timeout(300)
        mp.screenshot(path=str(OUT / "11-mobile-dashboard.png"))
        mp.click("#menuBtn"); mp.wait_for_timeout(400); mp.screenshot(path=str(OUT / "12-mobile-menu.png"))
        mp.keyboard.press("Escape")
        overflow = {}
        for route in ("dashboard", "identity", "accounts", "profile", "image", "scam", "report", "safety", "how", "future"):
            mp.goto(f"{BASE}/#/{route}"); mp.wait_for_load_state("networkidle"); mp.wait_for_timeout(250)
            overflow[route] = mp.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        mp.goto(f"{BASE}/#/scam"); mp.wait_for_timeout(300); mp.click("text=Bank KYC phishing"); mp.click("button:has-text('Analyse message')"); mp.wait_for_selector(".risk-badge")
        mp.screenshot(path=str(OUT / "13-mobile-scam-result.png"))
        overflow["scam-result"] = mp.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        print("horizontal overflow px per page (0 = none):", overflow)
        b.close()
    print("browser errors:", errors or "none")

run()
