import asyncio
import re
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://practice2.dev.ozmed.health/"
EMAIL = "fep5@yopmail.com"
PASSWORD = "Test@1234"
OTP = "489567"


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

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
            otp_inputs = await page.locator("input").all()
            for i, digit in enumerate(OTP):
                if i < len(otp_inputs):
                    await otp_inputs[i].fill(digit)
            await page.get_by_role("button", name="Submit").click()
            await page.wait_for_timeout(2500)

        await page.get_by_role("link", name="Appointments").click()
        await page.wait_for_timeout(3000)

        # Search for Lucas Thomas specifically to see all his appointments
        search = page.get_by_placeholder("Search patient name...")
        await search.click()
        await search.fill("Lucas Thomas")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="dup_search_results.png", full_page=True)

        rows = await page.locator("table tbody tr").all()
        print(f"Rows for 'Lucas Thomas': {len(rows)}")
        for r in rows:
            txt = (await r.inner_text()).replace("\n", " | ")
            print(" -", txt)

        # The second row (17:25-17:29) is the duplicate from a debug run.
        # Open its action menu and look for Cancel/Delete.
        dup_row = rows[1]
        action_btn = dup_row.locator("button").last
        await action_btn.click()
        await page.wait_for_timeout(800)
        await page.screenshot(path="dup_action_menu.png")

        menu_items = await page.get_by_role("menuitem").all()
        print(f"\nMenu items: {len(menu_items)}")
        for m in menu_items:
            print(" -", (await m.inner_text()).strip())

        await page.get_by_role("menuitem", name="Cancel Appointment").click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path="dup_cancel_dialog.png")

        # Confirm dialog titled "Cancel Appointment" has a "Cancel" button (orange)
        confirm_dialog = page.locator("[class*='MuiDialog-paper']", has_text="Are you sure you want to cancel")
        confirm_btn = confirm_dialog.get_by_role("button", name="Cancel", exact=True)
        if await confirm_btn.count() > 0:
            await confirm_btn.click()
            await page.wait_for_timeout(1500)
        else:
            print("Confirm button not found!")

        await page.screenshot(path="dup_after_cancel.png")

        await page.get_by_placeholder("Search patient name...").fill("Lucas Thomas")
        await page.wait_for_timeout(1500)
        rows_after = await page.locator("table tbody tr").all()
        print(f"\nRows for 'Lucas Thomas' after cancel: {len(rows_after)}")
        for r in rows_after:
            print(" -", (await r.inner_text()).replace("\n", " | "))

        await page.wait_for_timeout(10_000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
