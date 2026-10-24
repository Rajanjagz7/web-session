import { Page, Locator, expect } from "@playwright/test";

export class CmsPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly addButton: Locator;
  readonly table: Locator;
  readonly rows: Locator;
  readonly columnHeaders: Locator;
  readonly typeFilter: Locator;
  readonly clearButton: Locator;

  // New CMS Form locators
  readonly newHeading: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: "CMS", level: 1 });
    this.addButton = page.getByRole("button", { name: "Add CMS" });
    this.table = page.locator("table");
    this.rows = page.locator("tbody tr");
    this.columnHeaders = page.locator("thead th");
    this.typeFilter = page.getByRole("combobox", { name: "Content type" });
    this.clearButton = page.getByRole("button", { name: "Clear", exact: true });

    // Form elements
    this.newHeading = page.getByRole("heading", { name: /add cms/i });
    this.submitButton = page.getByRole("button", { name: /add cms/i });
    this.cancelButton = page.getByRole("button", { name: "Cancel" });
  }

  async gotoList() {
    await this.page.goto("/cms");
    await expect(this.heading).toBeVisible();
    await expect(this.rows.first()).toBeVisible();
  }

  async gotoNew() {
    await this.page.goto("/cms/new");
    await expect(this.cancelButton).toBeVisible();
  }

  /** Intercepts list calls with mock CMS records */
  async mockList(items: any[], status = 200) {
    await this.page.route("**/api/proxy*", async (route) => {
      const req = route.request();
      if (req.method() === "GET" && req.headers()["x-target-endpoint"]?.startsWith("/cms")) {
        return route.fulfill({
          status,
          contentType: "application/json",
          body: JSON.stringify({
            success: true,
            message: "CMS retrieved",
            data: items
          })
        });
      }
      return route.fallback();
    });
  }
}
