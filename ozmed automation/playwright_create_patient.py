"""
Playwright script — OzMed Create Patient
Navigates to the sign-in page, clicks "Create an account", then fills in
the registration form with test patient data.

Install dependencies:
    pip install playwright
    playwright install chromium

Run:
    python playwright_create_patient.py
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

URL = "https://practice2.dev.ozmed.health/"

# ── Test patient data ─────────────────────────────────────────────────────────
PATIENT = {
    "first_name":   "Jane",
    "last_name":    "Smith",
    "email":        "jane.smith.test@example.com",
    "password":     "TestPass123!",
    "dob":          "15/03/1985",   # DD/MM/YYYY — adjust if the field expects another format
    "phone":        "0412345678",
    "gender":       "Female",
    "address":      "123 Test Street",
    "suburb":       "Sydney",
    "state":        "NSW",
    "postcode":     "2000",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

async def try_fill(page, label_or_placeholder: str, value: str, timeout: int = 4_000) -> bool:
    """Try several strategies to fill a field. Returns True on success."""
    strategies = [
        lambda: page.get_by_label(label_or_placeholder, exact=False),
        lambda: page.get_by_placeholder(label_or_placeholder, exact=False),
        lambda: page.locator(f'input[name*="{label_or_placeholder.lower().replace(" ", "")}"]'),
        lambda: page.locator(f'input[id*="{label_or_placeholder.lower().replace(" ", "")}"]'),
    ]
    for strategy in strategies:
        try:
            locator = strategy()
            await locator.wait_for(state="visible", timeout=timeout)
            await locator.fill(value)
            print(f"      Filled '{label_or_placeholder}' ✓")
            return True
        except Exception:
            continue
    print(f"      ⚠ Could not fill '{label_or_placeholder}' — field not found")
    return False


async def try_select(page, label_or_name: str, value: str, timeout: int = 4_000) -> bool:
    """Try to select a dropdown option."""
    strategies = [
        lambda: page.get_by_label(label_or_name, exact=False),
        lambda: page.locator(f'select[name*="{label_or_name.lower()}"]'),
        lambda: page.locator(f'select[id*="{label_or_name.lower()}"]'),
    ]
    for strategy in strategies:
        try:
            locator = strategy()
            await locator.wait_for(state="visible", timeout=timeout)
            await locator.select_option(label=value)
            print(f"      Selected '{value}' for '{label_or_name}' ✓")
            return True
        except Exception:
            continue
    # Fallback: try clicking a radio/option with matching text
    try:
        option = page.get_by_text(value, exact=True)
        await option.wait_for(state="visible", timeout=timeout)
        await option.click()
        print(f"      Clicked option '{value}' for '{label_or_name}' ✓")
        return True
    except Exception:
        pass
    print(f"      ⚠ Could not select '{label_or_name}' = '{value}'")
    return False


# ── Main flow ─────────────────────────────────────────────────────────────────

async def create_patient() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page    = await context.new_page()

        try:
            # ── 1. Navigate ───────────────────────────────────────────────────
            print(f"[1/6] Navigating to {URL}")
            await page.goto(URL, wait_until="networkidle", timeout=30_000)

            # ── 2. Wait for React hydration ───────────────────────────────────
            print("[2/6] Waiting for React root …")
            await page.wait_for_function(
                "() => { const r = document.getElementById('root'); "
                "        return r && r.children.length > 0; }",
                timeout=15_000,
            )
            print("      React root ready.")

            # ── 3. Click "Create an account" ──────────────────────────────────
            print("[3/6] Clicking 'Create an account' …")
            for name, locator_fn in [
                ("role_button", lambda: page.get_by_role("button", name="Create an account")),
                ("role_link",   lambda: page.get_by_role("link",   name="Create an account")),
                ("text_exact",  lambda: page.get_by_text("Create an account", exact=True)),
                ("text_partial",lambda: page.get_by_text("Create an account")),
            ]:
                try:
                    loc = locator_fn()
                    await loc.wait_for(state="visible", timeout=8_000)
                    await loc.scroll_into_view_if_needed()
                    await loc.click()
                    print(f"      Clicked via {name!r}")
                    break
                except PWTimeout:
                    continue

            # ── 4. Wait for registration form ─────────────────────────────────
            print("[4/6] Waiting for registration form …")
            await page.wait_for_load_state("networkidle", timeout=10_000)
            await asyncio.sleep(1)   # allow SPA animation to settle

            print(f"\n      Current URL: {page.url}")
            print(f"      Page title : {await page.title()}\n")

            # ── 5. Fill in patient fields ─────────────────────────────────────
            print("[5/6] Filling patient registration form …")

            await try_fill(page, "First name",   PATIENT["first_name"])
            await try_fill(page, "Last name",    PATIENT["last_name"])
            await try_fill(page, "Email",        PATIENT["email"])
            await try_fill(page, "Password",     PATIENT["password"])
            await try_fill(page, "Confirm",      PATIENT["password"])   # "Confirm password"
            await try_fill(page, "Date of birth",PATIENT["dob"])
            await try_fill(page, "Phone",        PATIENT["phone"])
            await try_fill(page, "Mobile",       PATIENT["phone"])
            await try_fill(page, "Address",      PATIENT["address"])
            await try_fill(page, "Suburb",       PATIENT["suburb"])
            await try_fill(page, "Postcode",     PATIENT["postcode"])

            await try_select(page, "Gender", PATIENT["gender"])
            await try_select(page, "State",  PATIENT["state"])

            # ── 6. Submit the form ────────────────────────────────────────────
            print("\n[6/6] Submitting form …")
            submitted = False
            for btn_name in ["Register", "Create account", "Create patient",
                             "Sign up", "Submit", "Continue", "Next"]:
                try:
                    btn = page.get_by_role("button", name=btn_name, exact=False)
                    await btn.wait_for(state="visible", timeout=3_000)
                    await btn.scroll_into_view_if_needed()
                    await btn.click()
                    print(f"      Clicked submit button: '{btn_name}'")
                    submitted = True
                    break
                except PWTimeout:
                    continue

            if not submitted:
                print("      ⚠ Could not find a submit button — taking screenshot for manual review")
                await page.screenshot(path="form_before_submit.png", full_page=True)

            # Wait for post-submit result
            await asyncio.sleep(3)
            await page.screenshot(path="patient_created_result.png", full_page=True)

            print(f"\n--- Result ---")
            print(f"URL   : {page.url}")
            print(f"Title : {await page.title()}")
            print("Screenshot saved → patient_created_result.png")

        except Exception as exc:
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print(f"\n❌ Error: {exc}")
            print("   Screenshot saved → error_screenshot.png")
            raise

        finally:
            await asyncio.sleep(2)
            await browser.close()
            print("\nBrowser closed.")


if __name__ == "__main__":
    asyncio.run(create_patient())
