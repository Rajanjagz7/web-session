"""Visits the Notes tab where the img onerror payload was stored, watches for
a JS dialog (alert) or a console error from the onerror firing, screenshots
the rendered note. Read-only navigation - the note was already created via API."""
import sys
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
import helpers as h
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(20000)
    fired = {"dialog": False, "console_errors": []}
    page.on("dialog", lambda d: (fired.update(dialog=True), d.dismiss()))
    page.on("console", lambda m: fired["console_errors"].append(m.text[:200]) if m.type == "error" else None)

    h.login(page)
    h.open_job_detail(page, "M8N000071")
    page.get_by_role("button", name="Notes", exact=True).click()
    page.wait_for_timeout(2500)
    page.screenshot(path=r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\dbg-xss-notes.png", full_page=True)

    # does a broken/missing image icon render (proves innerHTML), and did onerror fire?
    img_count = page.locator('img[src="x"]').count()
    print("raw <img src=x> element present in DOM:", img_count)
    print("JS alert() dialog fired:", fired["dialog"])
    print("console errors seen:", fired["console_errors"][:5])
    b.close()
