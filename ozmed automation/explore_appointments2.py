import asyncio
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
        await page.wait_for_timeout(4000)
        await page.get_by_role("button", name="Book Appointment").click()
        await page.wait_for_timeout(1500)

        dialog = page.locator("[class*='MuiDialog-paper']")
        await dialog.locator("button[aria-label='Choose date']").click()
        await page.wait_for_timeout(500)
        day_buttons = await page.locator("button.MuiPickersDay-root").all()
        for b in day_buttons:
            cls = await b.get_attribute("class") or ""
            if "Mui-disabled" not in cls:
                await b.click()
                break
        await page.wait_for_timeout(1000)

        prac_input = dialog.locator("input[role='combobox']").first
        await prac_input.click()
        await page.wait_for_timeout(300)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(3000)
        prac_options = await page.get_by_role("option").all()
        prac_names = [(await o.inner_text()).strip() for o in prac_options]
        print(f"Found {len(prac_names)} practitioners")
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)

        for idx, name in enumerate(prac_names):
            print(f"\n=== Trying practitioner [{idx}]: {name!r} ===")
            await prac_input.click()
            await page.wait_for_timeout(300)
            await prac_input.fill("")
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(2500)
            opts = await page.get_by_role("option").all()
            if idx >= len(opts):
                print("  index out of range, stopping")
                break
            await opts[idx].click()
            await page.wait_for_timeout(1200)

            combo_inputs = await dialog.locator("input[role='combobox']").all()
            if len(combo_inputs) < 2:
                print("  No Appointment Type field appeared")
                continue
            appt_type_input = combo_inputs[1]
            await appt_type_input.click()
            await page.wait_for_timeout(300)
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(4000)
            type_opts = await page.get_by_role("option").all()
            print(f"  Appointment types found: {len(type_opts)}")
            for t in type_opts:
                print("   -", (await t.inner_text()).strip())

            if type_opts:
                await type_opts[0].click()
                await page.wait_for_timeout(1500)
                await page.screenshot(path=f"appt_prac{idx}_type_selected.png")
                labels = await dialog.locator("label").all()
                label_texts = [(await l.inner_text()).strip() for l in labels]
                print("  Labels now:", label_texts)
                print("  >>> Found a working practitioner+type combo, stopping search")

                # Scroll down inside the dialog to find the slot picker
                avail = dialog.locator("text=Practitioner Availability")
                await avail.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                # Try mouse-wheel scrolling the dialog body itself
                box = await avail.bounding_box()
                if box:
                    await page.mouse.move(box["x"] + 10, box["y"] + 10)
                for _ in range(5):
                    await page.mouse.wheel(0, 300)
                    await page.wait_for_timeout(300)
                await page.screenshot(path=f"appt_prac{idx}_slots.png")

                all_buttons = await dialog.locator("button").all()
                print(f"\n  --- all buttons in dialog: {len(all_buttons)} ---")
                for b in all_buttons:
                    txt = (await b.inner_text()).strip()
                    if txt:
                        print("    ", repr(txt))

                # Dump the full dialog HTML for inspection
                html = await dialog.inner_html()
                with open("appt_dialog_with_slots.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("  Saved dialog HTML, length:", len(html))

                # Slots are plain divs with start/end time text, not buttons.
                # Find one via its time-pattern text and click it.
                slot_start = page.locator("span", has_text=__import__("re").compile(r"^\d{2}:\d{2}$")).first
                print("  Clicking first available slot...")
                await slot_start.click()
                await page.wait_for_timeout(800)
                await page.screenshot(path=f"appt_prac{idx}_slot_selected.png")

                next_btn2 = dialog.get_by_role("button", name="Next")
                disabled = await next_btn2.get_attribute("disabled")
                print("  Next button disabled attr:", disabled)

                concern = page.get_by_role("textbox", name="Concern")
                await concern.click()
                await concern.fill("Patient reports mild headache and fatigue for the past two days.")
                await page.wait_for_timeout(500)

                await next_btn2.scroll_into_view_if_needed()
                await next_btn2.click()
                await page.wait_for_timeout(2000)
                await page.screenshot(path="appt_step2_patient.png")
                print("\nDialog text on step 2:")
                print((await dialog.inner_text())[:400])

                step2_inputs = await dialog.locator("input").all()
                print(f"\n--- step2 inputs: {len(step2_inputs)} ---")
                for i, inp in enumerate(step2_inputs):
                    ph = await inp.get_attribute("placeholder")
                    role = await inp.get_attribute("role")
                    name = await inp.get_attribute("name")
                    print(f"  [{i}] name={name!r} placeholder={ph!r} role={role!r}")

                # Search for a specific real patient by name
                search_input = dialog.get_by_role("combobox", name="Search Patient")
                await search_input.click()
                await search_input.fill("Lucas Thomas")
                print("  Typed 'Lucas Thomas' — waiting for results...")
                await page.wait_for_timeout(3000)
                await page.screenshot(path="appt_patient_search_results.png")

                results = await page.get_by_role("option").all()
                print(f"\n  --- patient search results: {len(results)} ---")
                for r in results:
                    print("   -", (await r.inner_text()).strip())

                if results:
                    await results[0].click()
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path="appt_patient_selected.png")
                break
            else:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(300)

        await page.wait_for_timeout(20_000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
