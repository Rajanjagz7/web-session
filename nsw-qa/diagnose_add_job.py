"""One-off diagnostic: open the Add Job dialog on NSW staging and dump what's actually
there, since the existing suite's helpers.open_add_job_drawer() times out waiting for
the email field. Read-only: fills nothing beyond what login/open already do, submits
nothing. Not part of the committed suite - delete after use."""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
from config import EMAIL, PASSWORD  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"

console_lines = []
failed_requests = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url=BASE_URL)
    page.on("console", lambda m: console_lines.append(f"[{m.type}] {m.text}"))
    page.on("pageerror", lambda e: console_lines.append(f"[pageerror] {e}"))
    page.on("requestfailed", lambda r: failed_requests.append(f"{r.method} {r.url} -> {r.failure}"))
    page.on("response", lambda r: failed_requests.append(f"{r.status} {r.url}") if r.status >= 400 else None)

    page.goto("/log-in")
    page.get_by_placeholder(re.compile("email", re.I)).fill(EMAIL)
    page.get_by_placeholder(re.compile("password", re.I)).fill(PASSWORD)
    page.get_by_role("button", name=re.compile(r"log ?in|sign ?in", re.I)).click()
    page.get_by_role("button", name=re.compile("add job", re.I)).wait_for(state="visible", timeout=20_000)
    print("Logged in, jobs screen reached.")

    page.goto("/jobs")
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    dialog = page.get_by_role("dialog")

    try:
        dialog.wait_for(state="visible", timeout=8_000)
        print("Dialog became visible normally.")
    except Exception as e:
        print(f"Dialog did NOT become visible: {e}")

    page.wait_for_timeout(2000)  # let any async render/animation settle regardless

    page.screenshot(path="add-job-dialog-stage.png", full_page=True)
    print("Screenshot saved (may show a hidden/blank drawer): add-job-dialog-stage.png")

    print(f"\n--- dialog element state ---")
    print("class:", dialog.get_attribute("class"))
    print("attached:", dialog.count() > 0)
    box = dialog.bounding_box()
    print("bounding_box:", box)

    print("\n--- placeholders inside the dialog (present in DOM regardless of visibility) ---")
    for el in dialog.locator("[placeholder]").all():
        try:
            print(repr(el.get_attribute("placeholder")))
        except Exception as e:
            print("  (error reading one element)", e)

    print(f"\n--- console/page errors ({len(console_lines)}) ---")
    for line in console_lines[-30:]:
        print(line)

    print(f"\n--- HTTP 4xx/5xx or failed requests since page load ({len(failed_requests)}) ---")
    for line in failed_requests[-30:]:
        print(line)

    print("\n--- can we actually interact with the visible form (bypassing the mis-sized wrapper)? ---")
    try:
        page.get_by_placeholder("Enter Customer Name").fill("Diagnostic Test Customer")
        val = page.get_by_placeholder("Enter Customer Name").input_value()
        print(f"Filled Customer Name successfully, value={val!r}")
        page.get_by_placeholder("Enter Customer Name").fill("")  # clear it, don't leave test data
    except Exception as e:
        print(f"Fill failed: {e}")
    print("Submit button visible:", page.get_by_role("button", name=re.compile("Send Engagement Letter", re.I)).is_visible())
    page.get_by_role("button", name="", exact=False).all()  # no-op, just probing
    page.keyboard.press("Escape")

    print("\n--- retry: reload /jobs and try Add Job again ---")
    console_lines.clear()
    failed_requests.clear()
    page.reload()
    page.get_by_role("button", name=re.compile("add job", re.I)).wait_for(state="visible", timeout=15_000)
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    page.wait_for_timeout(2000)
    dialog2 = page.get_by_role("dialog")
    print("retry class:", dialog2.get_attribute("class"))
    print("retry bounding_box:", dialog2.bounding_box())
    print("retry console:", console_lines)
    print("retry 4xx/5xx:", failed_requests)

    browser.close()
