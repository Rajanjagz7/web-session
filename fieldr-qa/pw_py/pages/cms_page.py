"""CMS create form. Type selection swaps the body fields (FAQ -> Question/Answer,
others -> a rich-text Content field) — see SECURITY/CRASH reports for the FAQ case."""
import re

from .base_page import BasePage


class CmsPage(BasePage):
    def open_new(self) -> None:
        self.open_create_menu("New CMS", "Add New CMS")

    def type_combobox(self):
        return self.page.locator("main [role=combobox]").first

    def pick_type(self, type_name: str) -> None:
        """The dropdown is a react-select: its options are plain divs (class contains 'option'),
        not role=option, and its input can be hidden, so fall back to keyboard-opening it."""
        combo = self.type_combobox()
        try:
            combo.click(timeout=4000)
        except Exception:
            combo.focus()
            self.page.keyboard.press("ArrowDown")
        self.page.wait_for_timeout(600)
        option = self.page.locator("[class*=option], [id*=option]").filter(
            has_text=re.compile(rf"^\s*{re.escape(type_name)}\s*$"))
        option.first.click(timeout=5000)

    def fill_title(self, title: str) -> None:
        self.page.get_by_placeholder("Title", exact=False).first.fill(title)

    def fill_faq(self, question: str, answer: str) -> None:
        self.page.get_by_placeholder("Enter Question").fill(question)
        self.page.locator("main textarea").first.fill(answer)

    def fill_rich_content(self, text: str) -> None:
        body = self.page.locator("main [contenteditable=true], main .ql-editor, main textarea").first
        body.click()
        body.press_sequentially(text, delay=8)

    def save(self):
        return self.page.get_by_role("button", name="Save").last
