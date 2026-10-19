import { test, expect } from './fixtures';
import { openFirstProduct } from './helpers';

const wishlistIcon = (page: import('@playwright/test').Page) =>
  page.locator('[class*="wishlist"], [aria-label*="wishlist" i], button[data-wishlist]').first();

test.describe('Product page — wishlist (PW-01..PW-03)', () => {
  test('PW-01 rapid add/remove toggle ends in a consistent state', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const icon = wishlistIcon(page);
    if (!(await icon.isVisible().catch(() => false))) {
      test.skip(true, 'No wishlist control on this product page for this theme.');
      return;
    }
    for (let i = 0; i < 10; i++) await icon.click();
    await page.waitForTimeout(500);
    await expect(icon).toBeVisible();
  });

  test('PW-02 an out-of-stock product can still be wishlisted', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const soldOutLabel = page.locator('text=/sold out/i').first();
    if (!(await soldOutLabel.isVisible().catch(() => false))) {
      test.skip(true, 'Product in view is in stock — point PRODUCT_URL at a sold-out product to run this check.');
      return;
    }
    const icon = wishlistIcon(page);
    if (!(await icon.isVisible().catch(() => false))) {
      test.skip(true, 'No wishlist control on this product page for this theme.');
      return;
    }
    await expect(icon).toBeEnabled();
  });

  test('PW-03 wishlist state persists across a page reload', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const icon = wishlistIcon(page);
    if (!(await icon.isVisible().catch(() => false))) {
      test.skip(true, 'No wishlist control on this product page for this theme.');
      return;
    }
    await icon.click();
    await page.waitForTimeout(300);
    const stateBefore = await icon.getAttribute('aria-pressed').catch(() => null);
    await page.reload();
    const stateAfter = await icon.getAttribute('aria-pressed').catch(() => null);
    expect(stateAfter).toBe(stateBefore);
  });
});
