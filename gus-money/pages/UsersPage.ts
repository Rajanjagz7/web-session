import { Page, Locator, expect } from "@playwright/test";

export class UsersPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly statusFilter: Locator;
  readonly searchInput: Locator;
  readonly clearButton: Locator;
  readonly rows: Locator;
  readonly columnHeaders: Locator;
  readonly summary: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: "Users", level: 1 });
    this.statusFilter = page.getByRole("combobox", { name: "Account status" });
    this.searchInput = page.getByRole("textbox", { name: /search users/i });
    this.clearButton = page.getByRole("button", { name: "Clear", exact: true });
    this.rows = page.locator("tbody tr");
    this.columnHeaders = page.locator("thead th");
    this.summary = page.getByText(/^Showing /);
  }

  async goto() {
    await this.page.goto("/users");
    await expect(this.heading).toBeVisible();
    await expect(this.rows.first()).toBeVisible();
  }

  /** Runs `action` and returns the list API response it triggers. */
  async waitForList(action: () => Promise<void>) {
    const [resp] = await Promise.all([
      this.page.waitForResponse(
        (r) => r.url().includes("/api/proxy") && r.request().method() === "GET" && r.url().includes("scope=customer")
      ),
      action()
    ]);
    return resp;
  }

  async search(term: string) {
    await this.searchInput.fill(term);
    await this.page.keyboard.press("Enter");
  }

  async emails(): Promise<string[]> {
    return this.rows.locator("td:nth-child(2)").allInnerTexts();
  }
}
