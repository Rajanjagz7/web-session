import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class InventoryPage extends BasePage {
  readonly pageTitle: Locator;
  readonly sortDropdown: Locator;
  readonly inventoryItems: Locator;
  readonly cartBadge: Locator;
  readonly cartLink: Locator;

  constructor(page: Page) {
    super(page);
    this.pageTitle = page.getByTestId('title');
    this.sortDropdown = page.getByTestId('product-sort-container');
    this.inventoryItems = page.getByTestId('inventory-item');
    this.cartBadge = page.getByTestId('shopping-cart-badge');
    this.cartLink = page.getByTestId('shopping-cart-link');
  }

  async goto(): Promise<void> {
    await this.navigate('/inventory.html');
  }

  productCard(name: string): Locator {
    return this.inventoryItems.filter({ hasText: name });
  }

  async addToCart(productName: string): Promise<void> {
    await this.productCard(productName)
      .getByRole('button', { name: 'Add to cart' })
      .click();
  }

  async removeFromCart(productName: string): Promise<void> {
    await this.productCard(productName)
      .getByRole('button', { name: 'Remove' })
      .click();
  }

  async sortBy(option: 'az' | 'za' | 'lohi' | 'hilo'): Promise<void> {
    await this.sortDropdown.selectOption(option);
  }

  async getProductPrices(): Promise<number[]> {
    const priceLocators = this.inventoryItems.getByTestId('inventory-item-price');
    const texts = await priceLocators.allTextContents();
    return texts.map((t) => parseFloat(t.replace('$', '')));
  }

  async getProductNames(): Promise<string[]> {
    return this.inventoryItems.getByTestId('inventory-item-name').allTextContents();
  }

  async expectCartCount(count: number): Promise<void> {
    if (count === 0) {
      await expect(this.cartBadge).toBeHidden();
    } else {
      await expect(this.cartBadge).toHaveText(String(count));
    }
  }

  async goToCart(): Promise<void> {
    await this.cartLink.click();
  }
}
