"""Step 1 (inventory): click through every admin module on NSW staging and record
every /api/v1 call the UI makes - method, path, query, body shape, status, and
whether auth is a cookie or a bearer header. Read-only: navigation and opening
existing records only, no saves."""
import json
import re
import sys
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"
MODULES = ["Dashboard", "Projects", "All", "In Progress", "Action Required", "Being Assessed", "Completed",
           "Archived", "Exception Logs", "Installers", "Installer Users", "Matrix", "Admin Users", "CMS",
           "Activity", "Products", "Rebates", "Calculator", "Statistics", "Invoices"]

calls = []
current = {"module": "login"}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url=BASE_URL)
    page.set_default_timeout(30_000)

    def on_response(r):
        if "/api/v1/" not in r.url:
            return
        req = r.request
        u = urlparse(r.url)
        calls.append({
            "module": current["module"], "method": req.method, "path": u.path,
            "query_keys": sorted(parse_qs(u.query).keys()), "query": u.query[:300],
            "body": (req.post_data or "")[:400], "status": r.status,
            "auth": "bearer" if req.headers.get("authorization") else ("cookie" if req.headers.get("cookie") else "none"),
        })

    page.on("response", on_response)
    h.login(page)

    for m in MODULES:
        current["module"] = m
        try:
            page.get_by_role("link", name=m, exact=True).first.click(timeout=8000)
            page.wait_for_timeout(2500)
            print(f"{m:18} -> {page.url}")
        except Exception as e:
            print(f"{m:18} -> could not open ({type(e).__name__})")

    current["module"] = "Job detail M8N000078"
    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill("M8N000078")
    page.wait_for_timeout(1500)
    page.locator("table tbody tr").first.locator("svg, img, button").first.click()
    page.wait_for_timeout(2500)

    current["module"] = "Job detail (Photos Started)"
    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill("M8N000071")
    page.wait_for_timeout(1500)
    page.locator("table tbody tr").first.locator("svg, img, button").first.click()
    page.wait_for_timeout(3000)
    print("Photos Started job ->", page.url)
    tabs = []
    for b in page.get_by_role("button").all():
        try:
            t = b.inner_text().strip()
            if t and len(t) < 40:
                tabs.append(t)
        except Exception:
            pass
    print("Buttons on that page:", tabs)
    for t in tabs:
        if t in ("Job Information", "Products", "Post Install Details", "Photos", "Notes", "Documents", "History", "Activity"):
            current["module"] = f"Job tab: {t}"
            try:
                page.get_by_role("button", name=t, exact=True).first.click(timeout=5000)
                page.wait_for_timeout(1500)
            except Exception:
                pass

    browser.close()

with open("api_inventory.json", "w", encoding="utf-8") as f:
    json.dump(calls, f, indent=1)

uniq = {}
for c in calls:
    key = (c["method"], re.sub(r"/[0-9a-f]{24}", "/:id", c["path"]))
    uniq.setdefault(key, c)
print(f"\n{len(calls)} calls, {len(uniq)} unique endpoints:")
for (m, pth), c in sorted(uniq.items(), key=lambda x: x[0][1]):
    print(f"  {c['status']} {m:6} {pth}  q={c['query_keys']}  auth={c['auth']}  [{c['module']}]")
