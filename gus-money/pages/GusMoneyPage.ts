import { Page, Locator, expect } from "@playwright/test";

export class GusMoneyPage {
  readonly page: Page;
  readonly globalRewardsTable: Locator;
  readonly exportButton: Locator;
  readonly searchInput: Locator;

  constructor(page: Page) {
    this.page = page;
    this.globalRewardsTable = page.locator('table, [role="grid"]');
    this.exportButton = page.locator('button:has-text("Export"), button:has-text("Download")');
    this.searchInput = page.locator('input[placeholder*="Search"]');
  }

  async goto() {
    await this.page.goto("/reward/global-rewards", { waitUntil: "domcontentloaded" });
  }
}