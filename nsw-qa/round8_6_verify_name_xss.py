import sys
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
import helpers as h
from playwright.sync_api import sync_playwright

JOB_NUMBER = "M8N000208"
with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(20000)
    fired = {"dialog": False}
    page.on("dialog", lambda d: (fired.update(dialog=True), d.dismiss()))
    h.login(page)
    page.goto("/jobs")
    page.get_by_placeholder(__import__("re").compile("search jobs", __import__("re").I)).fill(JOB_NUMBER)
    page.wait_for_timeout(1800)
    print("Jobs list: dialog fired on list render:", fired["dialog"])
    page.screenshot(path=r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\dbg-name-xss-list.png", full_page=True)

    fired["dialog"] = False
    page.locator("table tbody tr").first.locator("svg, img, button").first.click()
    page.wait_for_timeout(2500)
    print("Job detail: dialog fired on detail render:", fired["dialog"])
    page.screenshot(path=r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\dbg-name-xss-detail.png", full_page=True)
    b.close()
