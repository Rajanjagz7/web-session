"""
Quick exploration: open the Book Appointment modal and print all form fields
including the new Visit Type field and its options.
"""
import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://practice2.dev.ozmed.health/"
EMAIL = "fep5@yopmail.com"
PASSWORD = "Test@1234"
OTP = "489567"


async def login(page):
    await page.goto(URL, wait_until="networkidle", timeout=30_000)
    await page.wait_for_function(
        "() => { const r = document.getElementById('root'); return r && r.children.length > 0; }",
        timeout=15_000,
    )
    inputs = await page.locator("input").all()
    await inputs[0].fill(EMAIL)
    await inputs[1].fill(PASSWORD)
    await page.get_by_role("button", name="Sign In").click()
    await page.wait_for_timeout(2500)
    if "verify" in page.url:
        for attempt in range(4):
            for i, digit in enumerate(OTP):
                for _ in range(3):
                    try:
                        otp_inputs = await page.locator("input").all()
                        if i < len(otp_inputs):
                            await otp_inputs[i].fill(digit, timeout=5000)
                        break
                    except Exception:
                        await page.wait_for_timeout(300)
            await page.wait_for_timeout(300)
            try:
                await page.get_by_role("button", name="Submit").click(timeout=5000)
            except Exception:
                pass
            await page.wait_for_timeout(3000)
            if "verify" not in page.url:
                break


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("Logging in...")
        await login(page)
        print("Logged in. URL:", page.url)

        # Navigate to Appointments
        await page.get_by_role("link", name="Appointments").click()
        await page.wait_for_timeout(3000)

        # Open Book Appointment modal
        await page.get_by_role("button", name="Book Appointment").click()
        await page.wait_for_timeout(2000)

        dialog = page.locator("[class*='MuiDialog-paper']")
        print("\n--- Modal content labels ---")
        labels = await dialog.locator("label").all()
        for lbl in labels:
            txt = (await lbl.inner_text()).strip()
            if txt:
                print(f"  Label: {txt!r}")

        print("\n--- All inputs in modal ---")
        inputs = await dialog.locator("input").all()
        for i, inp in enumerate(inputs):
            ph = await inp.get_attribute("placeholder") or ""
            tp = await inp.get_attribute("type") or ""
            role = await inp.get_attribute("role") or ""
            print(f"  input[{i}]: type={tp!r} role={role!r} placeholder={ph!r}")

        # Pick a date first so more fields appear
        print("\nPicking a date to reveal all fields...")
        try:
            await dialog.locator("button[aria-label='Choose date']").click(timeout=8000)
            await page.wait_for_timeout(500)
            day_buttons = await page.locator("button.MuiPickersDay-root").all()
            for b in day_buttons:
                cls = await b.get_attribute("class") or ""
                if "Mui-disabled" not in cls:
                    await b.click()
                    break
            await page.wait_for_timeout(1500)
        except Exception as e:
            print(f"  Date pick failed: {e}")

        print("\n--- Labels after date pick ---")
        labels = await dialog.locator("label").all()
        for lbl in labels:
            txt = (await lbl.inner_text()).strip()
            if txt:
                print(f"  Label: {txt!r}")

        # Look for Visit Type or any select/combobox not yet explored
        print("\n--- All combobox inputs after date pick ---")
        combos = await dialog.locator("input[role='combobox']").all()
        for i, c in enumerate(combos):
            ph = await c.get_attribute("placeholder") or ""
            val = await c.input_value() or ""
            print(f"  combobox[{i}]: placeholder={ph!r} value={val!r}")

        # Try to open the first combobox that looks like visit type
        # by clicking each one and printing its options
        print("\n--- Exploring each combobox options ---")
        combos = await dialog.locator("input[role='combobox']").all()
        for i, c in enumerate(combos):
            ph = await c.get_attribute("placeholder") or ""
            print(f"\n  combobox[{i}] (placeholder={ph!r}) options:")
            try:
                await c.click()
                await page.wait_for_timeout(300)
                await page.keyboard.press("ArrowDown")
                await page.wait_for_timeout(2000)
                opts = await page.get_by_role("option").all()
                if opts:
                    for o in opts[:20]:
                        print(f"    - {(await o.inner_text()).strip()!r}")
                else:
                    print("    (no options found)")
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(300)
            except Exception as ex:
                print(f"    Error: {ex}")

        # Also check for native <select> elements
        print("\n--- Native <select> elements ---")
        selects = await dialog.locator("select").all()
        for i, sel in enumerate(selects):
            opts = await sel.locator("option").all()
            print(f"  select[{i}]:")
            for o in opts:
                print(f"    - {(await o.inner_text()).strip()!r}")

        print("\n--- Full modal text (abbreviated) ---")
        modal_text = (await dialog.inner_text()).strip()
        print(modal_text[:1500])

        await page.screenshot(path="explore_visit_types.png", full_page=True)
        print("\nScreenshot saved: explore_visit_types.png")
        await page.wait_for_timeout(5000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
