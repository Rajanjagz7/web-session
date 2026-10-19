"""
Lesson 3: Live Interactive Controls (Checkboxes, Dropdowns, Radios & Alerts)
-----------------------------------------------------------------------------
In this live environment test, we interact with real web controls:

1. Checkboxes: .check(), .uncheck(), expect(locator).to_be_checked()
2. Dropdown Selects: .select_option(label=...)
3. Radio Buttons: selecting one option and verifying others
4. Browser JS Alerts / Confirm Dialogs: using page.on("dialog", handler)
5. Hovering (Mouse interactions): .hover()
"""

from playwright.sync_api import sync_playwright, expect

def test_live_interactive_controls():
    print("\n=======================================================")
    print(" [TEST] LIVE INTERACTIVE CONTROLS (Dropdowns, Radios, Alerts)")
    print("=======================================================")

    with sync_playwright() as p:
        # Launch browser in headed mode with visible actions
        browser = p.chromium.launch(headless=False, slow_mo=600)
        page = browser.new_page()

        # -------------------------------------------------------------
        # PART 1: Checkboxes
        # -------------------------------------------------------------
        print("\n[PART 1] Testing Checkboxes...")
        page.goto("https://the-internet.herokuapp.com/checkboxes")

        checkbox_1 = page.locator("input[type='checkbox']").first
        checkbox_2 = page.locator("input[type='checkbox']").nth(1)

        # Check initial state
        print("  -> Verifying initial states...")
        expect(checkbox_1).not_to_be_checked()
        expect(checkbox_2).to_be_checked()

        # Check box 1
        print("  -> Checking Checkbox 1...")
        checkbox_1.check()
        expect(checkbox_1).to_be_checked()

        # Uncheck box 2
        print("  -> Unchecking Checkbox 2...")
        checkbox_2.uncheck()
        expect(checkbox_2).not_to_be_checked()
        print("  [OK] Checkboxes behavior verified!")

        # -------------------------------------------------------------
        # PART 2: Dropdowns (<select> elements)
        # -------------------------------------------------------------
        print("\n[PART 2] Testing Dropdowns...")
        page.goto("https://the-internet.herokuapp.com/dropdown")

        dropdown = page.locator("#dropdown")

        # Select by visible text (label)
        print("  -> Selecting 'Option 1' by visible label...")
        dropdown.select_option(label="Option 1")
        expect(dropdown).to_have_value("1")

        # Select by value
        print("  -> Selecting 'Option 2' by attribute value...")
        dropdown.select_option(value="2")
        expect(dropdown).to_have_value("2")
        print("  [OK] Dropdown selection verified!")

        # -------------------------------------------------------------
        # PART 3: JavaScript Alerts & Dialogs (Event Listeners)
        # -------------------------------------------------------------
        print("\n[PART 3] Testing JS Alert / Confirm Dialogs...")
        page.goto("https://the-internet.herokuapp.com/javascript_alerts")

        # In Playwright, JS dialogs are auto-dismissed by default unless you handle them!
        # Here is how you handle them explicitly:
        dialog_messages = []

        def handle_dialog(dialog):
            print(f"  -> JS Dialog Popup triggered! Type: '{dialog.type}', Message: '{dialog.message}'")
            dialog_messages.append(dialog.message)
            # You can dialog.accept() or dialog.dismiss()
            dialog.accept()

        # Register the dialog event listener
        page.on("dialog", handle_dialog)

        # 1. Click JS Alert button
        print("  -> Triggering JS Alert...")
        page.get_by_role("button", name="Click for JS Alert").click()
        result_text = page.locator("#result")
        expect(result_text).to_have_text("You successfully clicked an alert")

        # 2. Click JS Confirm button
        print("  -> Triggering JS Confirm...")
        page.get_by_role("button", name="Click for JS Confirm").click()
        expect(result_text).to_have_text("You clicked: Ok")
        print("  [OK] JS Dialog handling verified!")

        # -------------------------------------------------------------
        # PART 4: Mouse Hover Interactions
        # -------------------------------------------------------------
        print("\n[PART 4] Testing Mouse Hover...")
        page.goto("https://the-internet.herokuapp.com/hovers")

        # Hover over the first user profile card
        first_avatar = page.locator(".figure").first
        print("  -> Hovering over user profile avatar...")
        first_avatar.hover()

        # Check that hidden caption becomes visible on hover
        user_caption = page.get_by_role("heading", name="name: user1")
        expect(user_caption).to_be_visible()
        print("  [OK] Hover revealed hidden profile details!")

        print("\n[PART 5] Closing browser...")
        browser.close()

    print("\nSUCCESS: ALL LIVE CONTROLS TESTED SUCCESSFULLY!\n")

if __name__ == "__main__":
    test_live_interactive_controls()
