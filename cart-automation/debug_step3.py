import re
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://plumbsaverstage.softwareco.com"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"{BASE_URL}/customer/sign-up")

    page.get_by_role("button", name="Next").click()

    page.get_by_label("First name").fill("Test")
    page.get_by_label("Last name").fill("User")
    page.get_by_label("Email address").fill(f"qa.debug.{int(time.time())}@softwareco.com")
    page.get_by_label("Phone number").fill("412345678")
    page.get_by_label("Password", exact=True).fill("TestPass123!")
    page.get_by_label("Confirm Password").fill("TestPass123!")

    print("first name value:", page.get_by_label("First name").input_value())
    print("email value:", page.get_by_label("Email address").input_value())
    print("phone value:", page.get_by_label("Phone number").input_value())
    print("password value:", page.get_by_label("Password", exact=True).input_value())
    print("confirm value:", page.get_by_label("Confirm Password").input_value())

    page.keyboard.press("Tab")
    page.wait_for_timeout(300)

    next_btn = page.get_by_role("button", name="Next")
    box = next_btn.bounding_box()
    print("next bounding box:", box)
    el_at_point = page.evaluate(
        "([x, y]) => { const el = document.elementFromPoint(x, y); return el ? el.outerHTML.slice(0, 200) : null }",
        [box["x"] + box["width"] / 2, box["y"] + box["height"] / 2],
    )
    print("element at Next's center point:", el_at_point)
    print("next enabled before click:", next_btn.is_enabled())

    console_msgs = []
    page.on("console", lambda m: console_msgs.append(f"{m.type}: {m.text}"))

    next_btn.click()
    page.wait_for_timeout(500)
    print("toast/notification text at 500ms:", page.inner_text("body")[-800:])
    page.wait_for_timeout(5000)
    print("url after next click (5.5s total):", page.url)
    print("still see Basic Details heading:", page.get_by_text("Basic Details").count())
    print("Address Details heading count:", page.get_by_text("Address Details").count())
    print("console messages:", console_msgs)
    page.screenshot(path="debug_step2_stuck.png")

    comboboxes = page.get_by_role("combobox").all()
    print(f"combobox count: {len(comboboxes)}")
    for i, cb in enumerate(comboboxes):
        try:
            name = cb.evaluate("el => el.getAttribute('aria-label') || el.textContent || el.value")
        except Exception as e:
            name = f"<error: {e}>"
        print(f"  [{i}] {name!r}")

    print("--- page text near 'Country' ---")
    print(page.inner_text("body")[:1500])

    browser.close()
