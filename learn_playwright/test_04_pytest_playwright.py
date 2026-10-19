"""
Lesson 4: Pytest with Playwright (The Industry Standard Setup)
--------------------------------------------------------------
When using `pytest-playwright`, you DO NOT need:
❌ `with sync_playwright() as p:`
❌ `browser = p.chromium.launch()`
❌ `page = browser.new_page()`
❌ `browser.close()`

Instead, Pytest automatically provides a pre-configured `page` fixture for every test function!

Each test gets:
- A completely fresh, isolated browser context (no shared cookies/cache)
- Automatic browser teardown/cleanup
- Built-in CLI superpowers (--headed, --slowmo, --screenshot, --tracing)
"""

import pytest
from playwright.sync_api import Page, expect

# --------------------------------------------------------------------------
# Test 1: Simple Positive Login using the 'page' fixture
# --------------------------------------------------------------------------
def test_positive_login(page: Page):
    print("\n[Pytest 1] Running Positive Login Test...")
    
    # 1. Navigate
    page.goto("https://practicetestautomation.com/practice-test-login/")
    
    # 2. Fill inputs
    page.get_by_label("Username").fill("student")
    page.get_by_label("Password").fill("Password123")
    
    # 3. Click submit
    page.get_by_role("button", name="Submit").click()
    
    # 4. Assert success
    expect(page).to_have_url("https://practicetestautomation.com/logged-in-successfully/")
    expect(page.get_by_role("heading", name="Logged In Successfully")).to_be_visible()
    expect(page.get_by_role("link", name="Log out")).to_be_visible()


# --------------------------------------------------------------------------
# Test 2: Negative Login Scenarios using Data-Driven Parametrization
# --------------------------------------------------------------------------
@pytest.mark.parametrize("username, password, expected_error", [
    ("incorrectUser", "Password123", "Your username is invalid!"),
    ("student", "incorrectPassword", "Your password is invalid!"),
])
def test_negative_login(page: Page, username, password, expected_error):
    print(f"\n[Pytest 2] Testing Negative Login with user: '{username}'...")
    
    # 1. Navigate
    page.goto("https://practicetestautomation.com/practice-test-login/")
    
    # 2. Fill invalid credentials
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Submit").click()
    
    # 3. Assert error message is visible and contains expected text
    error_element = page.locator("#error")
    expect(error_element).to_be_visible()
    expect(error_element).to_contain_text(expected_error)
