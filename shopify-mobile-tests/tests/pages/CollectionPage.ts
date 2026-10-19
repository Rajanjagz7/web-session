import { expect, type Locator, type Page } from '@playwright/test';

export class CollectionPage {
  readonly page: Page;
  readonly firstProductCard: Locator;

  constructor(page: Page) {
    this.page = page;
    this.firstProductCard = page.getByRole('heading', { level: 4 }).first();
  }

  async expectLoaded(titlePattern: RegExp) {
    await expect(this.page).toHaveTitle(titlePattern);
    await expect(this.firstProductCard).toBeVisible();
  }
}
