"""Shared helpers all page objects build on."""
from playwright.sync_api import Page

from utils.config import BASE_URL


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def goto(self, path: str) -> None:
        self.page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")

    def open_sidebar(self, name: str) -> None:
        self.page.locator("nav").get_by_role("link", name=name, exact=False).first.click(timeout=8000)
        self.page.wait_for_timeout(3000)

    def main_text(self) -> str:
        return self.page.get_by_role("main").inner_text()

    def open_create_menu(self, label: str, marker) -> None:
        """Click Create > <label> and wait for a marker (text or regex) unique to that form,
        because the URL changes before the old page's content finishes swapping out (finding C9)."""
        self.page.get_by_role("button", name="Create").first.click()
        item = self.page.get_by_text(label, exact=True).first
        item.wait_for(state="visible", timeout=8000)
        item.click(timeout=5000)
        self.page.get_by_text(marker).first.wait_for(timeout=30_000)
