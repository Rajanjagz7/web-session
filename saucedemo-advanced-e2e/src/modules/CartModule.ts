import { Page, expect } from '@playwright/test';
import { CartPage } from '@pages/CartPage';
import { Logger } from '@utils/Logger';

export class CartModule {
  private logger = new Logger('CartModule');

  constructor(
    private page: Page,
    private cartPage: CartPage,
  ) {}

  async verifyItemCount(expected: number): Promise<void> {
    await expect(this.cartPage.cartItems()).toHaveCount(expected);
    this.logger.info(`Cart item count verified: ${expected}`);
  }

  async verifyItemPresent(productName: string): Promise<void> {
    await expect(this.cartPage.cartItem(productName)).toBeVisible();
  }

  async removeItems(productNames: string[]): Promise<void> {
    for (const name of productNames) {
      await this.cartPage.clickRemove(name);
    }
  }

  async proceedToCheckout(): Promise<void> {
    await this.cartPage.clickCheckout();
    await expect(this.page).toHaveURL(/checkout-step-one\.html/);
  }

  async continueShopping(): Promise<void> {
    await this.cartPage.clickContinueShopping();
    await expect(this.page).toHaveURL(/inventory\.html/);
  }
}
