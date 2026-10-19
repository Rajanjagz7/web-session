import { expect, type Locator, type Page } from '@playwright/test';

export class CartPage {
  readonly page: Page;
  // Scoped to #MainContent: the same "Your cart is empty" copy also exists
  // (permanently, off-screen) inside the header's cart-drawer component, so
  // an unscoped role query would hit Playwright's strict-mode ambiguity.
  readonly mainContent: Locator;
  readonly emptyCartHeading: Locator;
  readonly continueShoppingLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.mainContent = page.locator('#MainContent');
    this.emptyCartHeading = this.mainContent.getByRole('heading', { name: 'Your cart is empty' });
    this.continueShoppingLink = this.mainContent.getByRole('link', { name: 'Continue shopping' });
  }

  async goto() {
    await this.page.goto('/cart');
    await expect(this.emptyCartHeading).toBeVisible();
  }
}
