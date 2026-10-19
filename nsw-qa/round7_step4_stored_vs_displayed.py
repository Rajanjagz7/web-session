import sys, json, re
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
import helpers as h
from playwright.sync_api import sync_playwright

JOB_NUMBER = "M8N000071"
with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(20000)
    h.login(page)
    h.open_job_detail(page, JOB_NUMBER)
    page.wait_for_timeout(1500)
    job = page.request.get(f"/api/v1/jobs?skip=0&limit=1&search={JOB_NUMBER}").json()["data"]["jobs"][0]
    full = page.request.get(f"/api/v1/jobs/{job['id']}").json()["data"]["job"]

    displayed_text = page.locator("body").inner_text()
    print("=== fields stored in API but NOT found anywhere in Job Information tab text ===")

    def leaf(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from leaf(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from leaf(v, f"{prefix}[{i}]")
        else:
            yield prefix, obj

    for path, val in leaf(full):
        if val in (None, "", [], {}) or isinstance(val, bool):
            continue
        sval = str(val)
        if len(sval) < 3 or sval.startswith("6a") and len(sval) == 24:  # skip ids/hashes
            continue
        norm = re.sub(r"[\s\-()+]", "", sval).lower()
        if norm and norm not in re.sub(r"[\s\-()+]", "", displayed_text).lower():
            print(f"  {path} = {sval!r}")

    for tab in ("Products", "Post Install Details"):
        try:
            page.get_by_role("button", name=tab, exact=True).click(timeout=5000)
            page.wait_for_timeout(1200)
            displayed_text += "\n" + page.locator("body").inner_text()
        except Exception:
            pass
    print("\n=== after including Products + Post Install Details tabs ===")
    for path, val in leaf(full):
        if val in (None, "", [], {}) or isinstance(val, bool):
            continue
        sval = str(val)
        if len(sval) < 3 or (sval.startswith("6a") and len(sval) == 24):
            continue
        norm = re.sub(r"[\s\-()+]", "", sval).lower()
        if norm and norm not in re.sub(r"[\s\-()+]", "", displayed_text).lower():
            print(f"  {path} = {sval!r}")
    b.close()
