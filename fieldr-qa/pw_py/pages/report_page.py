"""Add Report (Job Report submission): choose a job, choose a template (Type), fill the template's fields.

The form renders the template's own fields, so required fields differ per template. This page object fills
the "Site Safety Inspection Report" template that the seeded jobs carry (see the converted field schema
in TIMESHEET_JOBREPORT_DATA_2026-09-21.md).
"""
import re

from .base_page import BasePage


class ReportPage(BasePage):
    def open_new(self) -> None:
        self.open_create_menu("New Report", "Report Setup")
        self.page.locator("main [role=combobox]").nth(1).wait_for(state="attached", timeout=15_000)

    def _open_combobox(self, combo) -> None:
        try:
            combo.click(timeout=3000)
        except Exception:
            combo.focus()
            self.page.keyboard.press("ArrowDown")

    def pick_job(self, search: str) -> str:
        """Pick the first job whose label matches the search text."""
        self._open_combobox(self.page.locator("main [role=combobox]").nth(0))
        self.page.keyboard.type(search, delay=40)
        options = self.page.locator("[role=option]")
        options.first.wait_for(timeout=15_000)
        label = options.first.inner_text().strip()
        options.first.click()
        return label

    def pick_type(self) -> str:
        """The Type list only fills in once a job is chosen (it lists the templates attached to that job)."""
        combo = self.page.locator("main [role=combobox]").nth(1)
        for _ in range(20):
            if combo.is_enabled():
                break
            self.page.wait_for_timeout(500)
        self._open_combobox(combo)
        options = self.page.locator("[role=option]")
        options.first.wait_for(timeout=15_000)
        label = options.first.inner_text().strip()
        options.first.click()
        self.page.get_by_text("Report Fields").first.wait_for(timeout=15_000)
        return label

    def pick_date(self, field_placeholder: str, day: int) -> None:
        self.page.get_by_placeholder(field_placeholder).click()
        self.page.locator("[role=dialog] button").filter(has_text=re.compile(rf"^{day}$")).first.click(timeout=5000)

    def fill_site_safety_report(self, site: str, inspector: str, hazards: str, supervisor_email: str) -> None:
        self.page.get_by_placeholder("Enter Site address").fill(site)
        self.pick_date("Enter Inspection date", 15)
        self.page.get_by_placeholder("Enter Inspector name").fill(inspector)
        radios = self.page.locator("main input[type=radio]")
        radios.nth(0).check(force=True)  # PPE worn by all crew: Yes
        radios.nth(2).check(force=True)  # SWMS on site: Yes
        self.page.get_by_placeholder("Enter Hazards identified").fill(hazards)
        self.page.get_by_placeholder("Enter Supervisor email").fill(supervisor_email)

    def save(self):
        return self.page.get_by_role("button", name="Save").last

    def inline_errors(self) -> list[str]:
        text = self.page.locator("main").first.inner_text()
        return [t.strip() for t in text.split("\n") if re.search(r"\b(required|please|valid)\b", t, re.I)]
