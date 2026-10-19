"""
Lesson 2: Locators, Form Controls & Web Assertions (expect)
------------------------------------------------------------
In this lesson, we will master:
1. User-centric locators: `get_by_label`, `get_by_role`, `get_by_placeholder`
2. Form interactions: `.fill()`, `.click()`
3. Web Assertions with `expect`:
   - `expect(locator).to_be_visible()`
   - `expect(locator).to_contain_text()`
   - `expect(page).to_have_url()`
   
Why `expect()` from Playwright is better than Python's standard `assert`:
-> `assert element.is_visible()` checks only once at that microsecond (can fail if page is loading).
-> `expect(element).to_be_visible()` RETRIES automatically for up to 5 seconds until it becomes true!
"""

from playwright.sync_api import sync_playwright, expect

def test_login_and_assertions():
    print("\n--- Lesson 2: Forms & Assertions ---")
    
    with sync_playwright() as p:
        # Launch browser in headed mode with a comfortable 400ms delay to watch the test
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        
        print("[1] Navigating to practice login portal...")
        page.goto("https://practicetestautomation.com/practice-test-login/")
        
        # ------------------------------------------------------------------
        # STEP 1: Assertions on initial page state
        # ------------------------------------------------------------------
        print("[2] Validating page header...")
        heading = page.get_by_role("heading", name="Test login")
        # Auto-waiting assertion: waits until heading is attached and visible
        expect(heading).to_be_visible()
        print("    -> Confirmed: 'Test login' heading is visible")
        
        # ------------------------------------------------------------------
        # STEP 2: Locating and filling input fields
        # ------------------------------------------------------------------
        print("[3] Filling username and password...")
        
        # Locating by label: finds input associated with <label for="username">Username</label>
        username_input = page.get_by_label("Username")
        username_input.fill("student")
        
        # Locating by label for password
        password_input = page.get_by_label("Password")
        password_input.fill("Password123")
        
        # ------------------------------------------------------------------
        # STEP 3: Clicking Submit Button
        # ------------------------------------------------------------------
        print("[4] Clicking Submit button...")
        submit_button = page.get_by_role("button", name="Submit")
        submit_button.click()
        
        # ------------------------------------------------------------------
        # STEP 4: Validating Successful Login with expect()
        # ------------------------------------------------------------------
        print("[5] Verifying successful login...")
        
        # 1. Verify URL changed to logged-in URL
        expect(page).to_have_url("https://practicetestautomation.com/logged-in-successfully/")
        print("    -> URL matches success page!")
        
        # 2. Verify success heading is displayed
        success_heading = page.get_by_role("heading", name="Logged In Successfully")
        expect(success_heading).to_be_visible()
        print("    -> Success heading is visible!")
        
        # 3. Verify 'Log out' button appears
        logout_button = page.get_by_role("link", name="Log out")
        expect(logout_button).to_be_visible()
        print("    -> 'Log out' button is available!")
        
        # ------------------------------------------------------------------
        # STEP 5: Logging out
        # ------------------------------------------------------------------
        print("[6] Clicking 'Log out'...")
        logout_button.click()
        
        # Verify redirected back to login page
        expect(page).to_have_url("https://practicetestautomation.com/practice-test-login/")
        print("    -> Successfully redirected back to Login page!")
        
        print("[7] Closing browser...")
        browser.close()

    print("\nSUCCESS: All assertions passed perfectly!\n")

if __name__ == "__main__":
    test_login_and_assertions()
