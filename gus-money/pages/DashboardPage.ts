import { Page, Locator, expect } from "@playwright/test";

export class DashboardPage {
  readonly page: Page;
  readonly navRewards: Locator;
  readonly navDeals: Locator;
  readonly navStores: Locator;
  readonly navUsers: Locator;

  constructor(page: Page) {
    this.page = page;
    this.navRewards = page.locator('a[href*="/reward"]');
    this.navDeals = page.locator('a[href*="/deal"]');
    this.navStores = page.locator('a[href*="/store"]');
    this.navUsers = page.locator('a[href*="/user"], a[href*="/customer"]');
  }

  async isLoaded(): Promise<boolean> {
    return !this.page.url().includes("/sign-in");
  }
}