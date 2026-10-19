import { Page, expect } from '@playwright/test';

/** Opens a real product page, either from PRODUCT_URL env var or the first product on /collections/all. */
export async function openFirstProduct(page: Page) {
  if (process.env.PRODUCT_URL) {
    await page.goto(process.env.PRODUCT_URL);
    return;
  }
  await page.goto('/collections/all');
  const firstProductLink = page.locator('a[href*="/products/"]').first();
  await expect(firstProductLink, 'expected at least one product on /collections/all').toBeVisible();
  await firstProductLink.click();
  await page.waitForLoadState('networkidle');
}

/** Opens a real category/collection page, either from CATEGORY_URL env var or the first link under /collections. */
export async function openFirstCategory(page: Page) {
  if (process.env.CATEGORY_URL) {
    await page.goto(process.env.CATEGORY_URL);
    return;
  }
  await page.goto('/collections');
  const firstCollectionLink = page.locator('a[href*="/collections/"]').first();
  await expect(firstCollectionLink, 'expected at least one collection link on /collections').toBeVisible();
  await firstCollectionLink.click();
  await page.waitForLoadState('networkidle');
}

/** Opens a product and adds it to cart, leaving the browser on that product page afterwards. */
export async function addFirstProductToCart(page: Page, qty?: string) {
  await openFirstProduct(page);
  const qtyInput = page.locator('input[type="number"][name="quantity"], input[name="quantity"]').first();
  if (qty && (await qtyInput.isVisible().catch(() => false))) {
    await qtyInput.fill(qty);
  }
  const addButton = page.getByRole('button', { name: /add to cart/i });
  await addButton.click();
  await page.waitForTimeout(1000);
}

export function cartLineItems(page: Page) {
  return page.locator('[class*="cart-item"], [class*="line-item"], tr[class*="cart"]');
}

export function couponInput(page: Page) {
  return page.getByPlaceholder(/discount|coupon|promo/i).first();
}

export function quantityInput(page: Page) {
  return page.locator('input[type="number"][name="quantity"], input[name="quantity"]').first();
}
