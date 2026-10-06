"""Selectors observed on 2026-09-19/21. Kept for reference/negative-path tests;
utils/auth.py has the reusable login flow most specs should call instead."""
from .base_page import BasePage


class LoginPage(BasePage):
    def open(self) -> None:
        self.goto("/login")

    def heading(self):
        return self.page.get_by_role("heading", name="Welcome to Fieldr")

    def mobile_tab(self):
        return self.page.get_by_role("button", name="Mobile Number")

    def email_tab(self):
        return self.page.get_by_role("button", name="Email Address")

    def identifier_input(self):
        return self.page.locator("form").get_by_role("textbox").first

    def send_otp_btn(self):
        return self.page.get_by_role("button", name="Send OTP")

    def otp_digit(self, index: int):
        return self.page.get_by_role("textbox", name=f"Digit {index}")

    def verify_btn(self):
        return self.page.get_by_role("button", name="Verify & Login")
