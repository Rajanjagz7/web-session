import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class InventoryPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  pageTitle = () => this.page.getByTestId('title');
  sortDropdown = () => this.page.getByTestId('product-sort-container');
  inventoryItems = () => this.page.getByTestId('inventory-item');
  cartBadge = () => this.page.getByTestId('shopping-cart-badge');
  cartLink = () => this.page.getByTestId('shopping-cart-link');
  menuButton = () => this.page.getByRole('button', { name: 'Open Menu' });

  productCard(name: string): Locator {
    return this.inventoryItems().filter({ hasText: name });
  }

  addToCartButton(name: string): Locator {
    return this.productCard(name).getByRole('button', { name: 'Add to cart' });
  }

  removeButton(name: string): Locator {
    return this.productCard(name).getByRole('button', { name: 'Remove' });
  }

  async clickAddToCart(name: string): Promise<void> {
    await this.addToCartButton(name).click();
  }

  async clickRemove(name: string): Promise<void> {
    await this.removeButton(name).click();
  }

  async selectSort(option: 'az' | 'za' | 'lohi' | 'hilo'): Promise<void> {
    await this.sortDropdown().selectOption(option);
  }

  async getCartBadgeText(): Promise<string | null> {
    return this.cartBadge().textContent();
  }

  async clickCartLink(): Promise<void> {
    await this.cartLink().click();
  }

  async clickMenuButton(): Promise<void> {
    await this.menuButton().click();
  }

  async getProductNames(): Promise<string[]> {
    return this.inventoryItems().getByTestId('inventory-item-name').allTextContents();
  }

  async getProductPriceTexts(): Promise<string[]> {
    return this.inventoryItems().getByTestId('inventory-item-price').allTextContents();
  }
}
