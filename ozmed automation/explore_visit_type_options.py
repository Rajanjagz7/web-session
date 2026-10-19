"""
Specifically target the Visit Type field and print its options.
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
        print("Logged in:", page.url)

        await page.get_by_role("link", name="Appointments").click()
        await page.wait_for_timeout(3000)
        await page.get_by_role("button", name="Book Appointment").click()
        await page.wait_for_timeout(2000)

        dialog = page.locator("[class*='MuiDialog-paper']")

        # Pick today's date first
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
            print(f"Date pick error: {e}")

        # Find MUI Select components (role="combobox" on div, or aria-haspopup="listbox")
        print("\n--- Elements with aria-haspopup='listbox' ---")
        listbox_triggers = await dialog.locator("[aria-haspopup='listbox']").all()
        for i, el in enumerate(listbox_triggers):
            tag = await el.evaluate("el => el.tagName")
            txt = (await el.inner_text()).strip()
            role = await el.get_attribute("role") or ""
            cls = (await el.get_attribute("class") or "")[:80]
            print(f"  [{i}] <{tag}> role={role!r} text={txt!r} class={cls!r}")

        print("\n--- Elements with role='button' in dialog (potential MUI Select) ---")
        btn_divs = await dialog.locator("div[role='button']").all()
        for i, el in enumerate(btn_divs):
            txt = (await el.inner_text()).strip()
            aria = await el.get_attribute("aria-labelledby") or ""
            print(f"  [{i}] text={txt!r} aria-labelledby={aria!r}")

        # Try clicking 'Visit Type' label area
        print("\n--- Clicking Visit Type label/field ---")
        try:
            vt = page.get_by_label("Visit Type")
            count = await vt.count()
            print(f"  get_by_label('Visit Type') count: {count}")
            if count > 0:
                tag = await vt.first.evaluate("el => el.tagName")
                cls = (await vt.first.get_attribute("class") or "")[:80]
                print(f"  tag={tag} class={cls!r}")
                await vt.first.click()
                await page.wait_for_timeout(1500)
                # Check for options
                opts = await page.get_by_role("option").all()
                if opts:
                    print("  Options found:")
                    for o in opts:
                        print(f"    - {(await o.inner_text()).strip()!r}")
                else:
                    # Check for listbox
                    listbox = page.get_by_role("listbox")
                    if await listbox.count() > 0:
                        items = await listbox.locator("li").all()
                        print(f"  Listbox items ({len(items)}):")
                        for li in items:
                            print(f"    - {(await li.inner_text()).strip()!r}")
                    else:
                        print("  No options or listbox found after click")
                await page.keyboard.press("Escape")
        except Exception as ex:
            print(f"  Error: {ex}")

        # Try finding MuiSelect specifically
        print("\n--- MuiSelect elements ---")
        mui_selects = await dialog.locator("[class*='MuiSelect']").all()
        for i, el in enumerate(mui_selects[:10]):
            tag = await el.evaluate("el => el.tagName")
            cls = (await el.get_attribute("class") or "")[:100]
            txt = (await el.inner_text()).strip()[:60]
            print(f"  [{i}] <{tag}> class={cls!r} text={txt!r}")

        # Try clicking anything near "Visit Type" text
        print("\n--- Trying to find Visit Type via text proximity ---")
        try:
            # Find the Visit Type section
            vt_label = dialog.get_by_text("Visit Type", exact=True).first
            if await vt_label.count() > 0:
                parent = vt_label.locator("xpath=..")
                siblings = parent.locator("xpath=following-sibling::*").first
                sib_txt = (await siblings.inner_text()).strip()[:100]
                print(f"  Following sibling of 'Visit Type': {sib_txt!r}")
        except Exception as ex:
            print(f"  Error: {ex}")

        # Dump entire dialog HTML (abbreviated) to find Visit Type structure
        print("\n--- Dialog inner HTML excerpt (Visit Type section) ---")
        try:
            html = await dialog.inner_html()
            # Find "Visit Type" in the HTML
            idx = html.lower().find("visit type")
            if idx >= 0:
                print(html[max(0, idx-200):idx+500])
        except Exception as ex:
            print(f"  Error: {ex}")

        await page.screenshot(path="explore_visit_type_options.png", full_page=True)
        print("\nScreenshot saved.")
        await page.wait_for_timeout(5000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
