"""Add Quote: Overview tab (customer + description) then Sections tab (section name + line items).

Sections-tab dropdown order (mapped from the live page, 2026-09-21):
  combobox 0 = the hidden Customer field carried over from Overview
  combobox 1 = the contact to send to ("No one in particular. Send to the customer"), added in the Oct 2026 release
  combobox 2 = "Columns" (formula columns for the section)
  combobox 3 = "Select Item"  <- the item picker for the first line
Items are react-selects whose input is only a few pixels wide, so they are opened via the keyboard.
"""
import re

from .base_page import BasePage

ITEM_COMBOBOX_INDEX = 3


class QuotePage(BasePage):
    def open_new(self) -> None:
        self.open_create_menu("New Quote", re.compile("Add Quote"))
        self.page.locator("main [role=combobox]").first.wait_for(state="attached", timeout=15_000)

    def _open_combobox(self, combo) -> None:
        try:
            combo.click(timeout=3000)
        except Exception:
            combo.focus()
            self.page.keyboard.press("ArrowDown")

    def pick_customer(self, search: str) -> str:
        combo = self.page.locator("main [role=combobox]").first
        self._open_combobox(combo)
        self.page.keyboard.type(search, delay=40)
        options = self.page.locator("[role=option]")
        options.first.wait_for(timeout=10_000)
        label = options.first.inner_text().strip()
        options.first.click()
        return label

    def fill_description(self, text: str) -> None:
        self.page.get_by_placeholder("Enter Description").fill(text)

    def next(self) -> None:
        self.page.get_by_role("button", name="Next").click()
        self.page.get_by_placeholder("Section Name").wait_for(timeout=15_000)

    def fill_section_name(self, name: str) -> None:
        self.page.get_by_placeholder("Section Name").fill(name)

    def pick_item(self, search: str) -> str:
        combo = self.page.locator("main [role=combobox]").nth(ITEM_COMBOBOX_INDEX)
        self._open_combobox(combo)
        self.page.keyboard.type(search, delay=40)
        options = self.page.locator("[role=option]")
        options.first.wait_for(timeout=10_000)
        label = options.first.inner_text().strip()
        options.first.click()
        return label

    def set_quantity(self, value: str) -> None:
        field = self.page.get_by_placeholder("Quantity").first
        field.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.type(value, delay=30)

    def line_values(self) -> dict:
        get = lambda ph: self.page.get_by_placeholder(ph).first.input_value()  # noqa: E731
        return {"unit": get("Unit"), "quantity": get("Quantity"), "rate": get("Rate")}

    def save(self):
        return self.page.get_by_role("button", name="Save").last

    def inline_errors(self) -> list[str]:
        return [t.strip() for t in self.page.locator("main").first.inner_text().split("\n")
                if t.strip().lower().startswith("please enter")]
