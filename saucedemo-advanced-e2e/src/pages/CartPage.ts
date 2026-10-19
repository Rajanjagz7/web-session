import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class CartPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  cartItems = () => this.page.getByTestId('inventory-item');
  checkoutBtn = () => this.page.getByTestId('checkout');
  continueShoppingBtn = () => this.page.getByTestId('continue-shopping');

  cartItem(name: string): Locator {
    return this.cartItems().filter({ hasText: name });
  }

  removeButton(name: string): Locator {
    return this.cartItem(name).getByRole('button', { name: 'Remove' });
  }

  async clickRemove(name: string): Promise<void> {
    await this.removeButton(name).click();
  }

  async clickCheckout(): Promise<void> {
    await this.checkoutBtn().click();
  }

  async clickContinueShopping(): Promise<void> {
    await this.continueShoppingBtn().click();
  }

  async getItemCount(): Promise<number> {
    return this.cartItems().count();
  }
}
