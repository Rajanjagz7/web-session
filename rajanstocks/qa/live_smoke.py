"""Read-only smoke test of a deployed site in a real browser (web + mobile): boots, opens every screen, paints a chart.

    python qa/live_smoke.py [https://rajanstocks.vercel.app]
"""
import sys
import time

from playwright.sync_api import sync_playwright

URL = (sys.argv[1] if len(sys.argv) > 1 else "https://rajanstocks.vercel.app").rstrip("/")
VIEWPORTS = {"web": dict(viewport={"width": 1366, "height": 800}),
             "mobile": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)}
NO_PUSH = "new MutationObserver(() => { const e = document.getElementById('pushAsk'); if (e) e.remove(); }).observe(document, {childList: true, subtree: true});"
bad = []
with sync_playwright() as p:
    try:
        b = p.chromium.launch(channel="chrome")
    except Exception:
        b = p.chromium.launch()
    for kind, opts in VIEWPORTS.items():
        ctx = b.new_context(**opts)
        ctx.add_init_script(NO_PUSH)
        page = ctx.new_page()
        js, http = [], []
        page.on("pageerror", lambda e: js.append(str(e)[:160]))
        page.on("console", lambda m: js.append("console: " + m.text[:160]) if m.type == "error" and "Failed to load resource" not in m.text else None)
        page.on("response", lambda r: http.append(f"{r.status} {r.url.replace(URL, '')[:80]}") if r.status >= 400 and "/api/" in r.url else None)
        t0 = time.time()
        page.goto(URL + "/#picks")
        page.wait_for_function("!document.getElementById('boot')", timeout=120000)
        boot = time.time() - t0
        for v in ("picks", "options", "markets", "ipo", "journal", "indicators", "vedic", "daily"):
            page.evaluate(f"go('{v}')")
            page.wait_for_timeout(6000 if v == "vedic" else 2500)      # the Vedic report is computed on first use (~2 s cold)
            n = page.evaluate("document.querySelector('.view.on') ? document.querySelector('.view.on').innerText.length : 0")
            ov = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            if n < 120 or ov > 0:
                bad.append(f"[{kind}] {v}: text={n} overflow={ov}")
        page.evaluate("go('options')")
        t1 = time.time()
        try:
            page.wait_for_function("OPT.sel && OPT.ochart && (OPT.ochart.data || []).length > 30", timeout=60000)
            chart = time.time() - t1
        except Exception:
            chart = -1
            bad.append(f"[{kind}] option chart never painted")
        print(f"[{kind}] boot {boot:.1f}s, option chart ready {chart:.1f}s, js errors {len(js)}, failing api calls {len(http)}")
        bad += [f"[{kind}] JS: {x}" for x in js[:4]] + [f"[{kind}] HTTP: {x}" for x in http[:4]]
        ctx.close()
    b.close()
print("LIVE SMOKE: " + ("OK" if not bad else "PROBLEMS\n - " + "\n - ".join(bad)))
sys.exit(1 if bad else 0)
