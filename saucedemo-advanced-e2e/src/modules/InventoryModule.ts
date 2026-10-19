import { Page, expect } from '@playwright/test';
import { InventoryPage } from '@pages/InventoryPage';
import { Logger } from '@utils/Logger';

export class InventoryModule {
  private logger = new Logger('InventoryModule');

  constructor(
    private page: Page,
    private inventoryPage: InventoryPage,
  ) {}

  async addProductsToCart(productNames: string[]): Promise<void> {
    for (const name of productNames) {
      this.logger.info(`Adding "${name}" to cart`);
      await this.inventoryPage.clickAddToCart(name);
    }
  }

  async removeProductsFromCart(productNames: string[]): Promise<void> {
    for (const name of productNames) {
      this.logger.info(`Removing "${name}" from cart`);
      await this.inventoryPage.clickRemove(name);
    }
  }

  async verifyCartCount(expected: number): Promise<void> {
    if (expected === 0) {
      await expect(this.inventoryPage.cartBadge()).toBeHidden();
    } else {
      await expect(this.inventoryPage.cartBadge()).toHaveText(String(expected));
    }
    this.logger.info(`Cart count verified: ${expected}`);
  }

  async sortBy(option: 'az' | 'za' | 'lohi' | 'hilo'): Promise<string[]> {
    await this.inventoryPage.selectSort(option);
    return this.inventoryPage.getProductNames();
  }

  async getSortedPrices(option: 'lohi' | 'hilo'): Promise<number[]> {
    await this.inventoryPage.selectSort(option);
    const texts = await this.inventoryPage.getProductPriceTexts();
    return texts.map((t) => parseFloat(t.replace('$', '')));
  }

  async goToCart(): Promise<void> {
    await this.inventoryPage.clickCartLink();
  }
}
