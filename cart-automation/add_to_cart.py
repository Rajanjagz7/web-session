"""
Add a product to cart on the Plumbsaver staging site, signing up a new
customer account automatically if login is required.

Usage:
    python add_to_cart.py
    python add_to_cart.py --email jainamb+cart1@softwareco.com --otp 489567
"""

import argparse
import re
import time

from playwright.sync_api import Page, sync_playwright

BASE_URL = "https://plumbsaverstage.softwareco.com"
STAGING_BYPASS_OTP = "489567"  # known staging bypass code, does not apply in prod
DEFAULT_PASSWORD = "TestPass123!"
DEFAULT_ADDRESS_SEARCH = "125 Nancy Ellis"
DEFAULT_ADDRESS_OPTION = re.compile(r"Leebold Drive, Bankstown Aerodrome")


def is_logged_in(page: Page) -> bool:
    return page.get_by_role("button", name="Sign In / Sign Up").count() == 0


def sign_up_new_customer(page: Page, email: str, otp: str) -> None:
    print(f"Signing up new customer: {email}")
    page.goto(f"{BASE_URL}/customer/sign-up")

    # Step 1: Account Type — "Individual" is selected by default.
    page.get_by_role("button", name="Next").click()

    # Step 2: Basic Details
    page.get_by_label("First name").fill("Test")
    page.get_by_label("Last name").fill("User")
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Phone number").fill("412345678")
    page.get_by_label("Password", exact=True).fill(DEFAULT_PASSWORD)
    page.get_by_label("Confirm Password").fill(DEFAULT_PASSWORD)
    page.get_by_role("button", name="Next").click()

    # Step 3: Address Details
    page.get_by_role("combobox", name="Country").click()
    page.get_by_role("option", name=re.compile(r"^AU Australia")).click()

    page.get_by_role("combobox", name="Address").click()
    page.keyboard.type(DEFAULT_ADDRESS_SEARCH, delay=40)
    page.get_by_role("option", name=DEFAULT_ADDRESS_OPTION).click()

    page.get_by_role("checkbox", name=re.compile(r"I agree")).check()
    page.wait_for_timeout(400)
    page.get_by_role("button", name="Create Account", exact=True).click()

    try:
        page.wait_for_url(f"{BASE_URL}/customer/verify", timeout=20000)
    except Exception:
        page.screenshot(path="signup_failure.png")
        print(f"Signup did not reach verify page. Current URL: {page.url}")
        print(f"Visible text snippet: {page.inner_text('body')[:800]}")
        raise
    print("OTP requested — verifying...")

    otp_boxes = page.get_by_role("textbox")
    otp_boxes_count = otp_boxes.count()
    for i, digit in enumerate(otp[:otp_boxes_count]):
        otp_boxes.nth(i).fill(digit)

    page.get_by_role("button", name="Verify").click()
    page.wait_for_load_state("networkidle")

    if not is_logged_in(page):
        print("Not auto-logged-in after verification, signing in explicitly...")
        page.goto(f"{BASE_URL}/customer/sign-in")
        page.get_by_label("Email address").fill(email)
        page.get_by_label("Password").fill(DEFAULT_PASSWORD)
        page.get_by_role("button", name="Sign in", exact=True).click()
        page.wait_for_load_state("networkidle")

    print("Signed up and logged in.")


def add_first_available_product_to_cart(page: Page) -> bool:
    page.goto(f"{BASE_URL}/products")
    add_buttons = page.get_by_role("button", name="Add to cart")
    add_buttons.first.wait_for(state="attached", timeout=15000)
    page.wait_for_timeout(1000)
    count = add_buttons.count()

    target = None
    for i in range(count):
        btn = add_buttons.nth(i)
        if btn.is_enabled():
            target = btn
            break

    if target is None:
        print("No available (in-stock) products found to add to cart.")
        return False

    target.click()
    page.wait_for_timeout(1500)

    if not is_logged_in(page):
        print("Add-to-cart requires sign-in.")
        return False

    print("Product add-to-cart click completed while logged in.")
    return True


def run(email: str, otp: str, headless: bool = True) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        added = add_first_available_product_to_cart(page)

        if not added:
            sign_up_new_customer(page, email=email, otp=otp)
            added = add_first_available_product_to_cart(page)

        if added:
            print("SUCCESS: product added to cart.")
        else:
            print("FAILED: could not add product to cart even after sign-up.")

        page.wait_for_timeout(2000)
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--email",
        default=f"qa.cart.{int(time.time())}@softwareco.com",
        help="Email for the new test account (needs to receive the OTP unless using the staging bypass code).",
    )
    parser.add_argument(
        "--otp",
        default=STAGING_BYPASS_OTP,
        help="6-digit verification code. Defaults to the known staging bypass code.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run with a visible browser window instead of headless.",
    )
    args = parser.parse_args()
    run(email=args.email, otp=args.otp, headless=not args.headed)
