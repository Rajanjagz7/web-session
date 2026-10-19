import { test, expect } from './fixtures';
import { openFirstProduct, quantityInput } from './helpers';

const addToCartButton = (page: import('@playwright/test').Page) =>
  page.getByRole('button', { name: /add to cart/i });

test.describe('Product page — add to cart (PA-01..PA-08)', () => {
  test('PA-01 quantity zero blocks add to cart', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const qty = quantityInput(page);
    if (!(await qty.isVisible().catch(() => false))) {
      test.skip(true, 'No visible quantity input on this theme — check variant/quantity selector manually.');
      return;
    }
    await qty.fill('0');
    const button = addToCartButton(page);
    const isDisabled = await button.isDisabled().catch(() => false);
    if (!isDisabled) {
      await button.click();
      await expect(page.locator('body')).not.toContainText(/added to your cart/i);
    } else {
      expect(isDisabled).toBeTruthy();
    }
  });

  test('PA-02 negative quantity is rejected', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const qty = quantityInput(page);
    if (!(await qty.isVisible().catch(() => false))) {
      test.skip(true, 'No visible quantity input on this theme.');
      return;
    }
    await qty.fill('-1');
    const value = await qty.inputValue();
    expect(Number(value)).toBeGreaterThanOrEqual(0);
  });

  test('PA-03 decimal quantity is rejected or rounded, never silently accepted as-is', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const qty = quantityInput(page);
    if (!(await qty.isVisible().catch(() => false))) {
      test.skip(true, 'No visible quantity input on this theme.');
      return;
    }
    const step = await qty.getAttribute('step');
    await qty.fill('2.5');
    const value = await qty.inputValue();
    if (step === '1' || step === null) {
      expect(Number.isInteger(Number(value)), 'expected decimal input to be rounded to a whole number').toBeTruthy();
    }
  });

  test('PA-06 very large quantity is capped, not an overflow error', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const qty = quantityInput(page);
    if (!(await qty.isVisible().catch(() => false))) {
      test.skip(true, 'No visible quantity input on this theme.');
      return;
    }
    await qty.fill('99999');
    const button = addToCartButton(page);
    await button.click();
    await page.waitForTimeout(1000);
    await expect(page.locator('body')).not.toContainText(/500|internal server error|overflow/i);
  });

  test('PA-07 add without selecting a required variant is blocked with a prompt', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const variantSelect = page.locator('select[name*="option" i]').first();
    if (!(await variantSelect.isVisible().catch(() => false))) {
      test.skip(true, 'No variant selector on this product — nothing to leave unselected.');
      return;
    }
    // Only meaningful if the theme ships with a blank/placeholder first option.
    const firstOptionValue = await variantSelect.locator('option').first().getAttribute('value');
    if (firstOptionValue) {
      test.skip(true, 'Variant selector has no blank placeholder option on this theme.');
      return;
    }
    const button = addToCartButton(page);
    const isDisabled = await button.isDisabled().catch(() => false);
    expect(isDisabled).toBeTruthy();
  });

  test('PA-08 rapid double-click does not duplicate the line item', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const button = addToCartButton(page);
    await expect(button).toBeVisible();
    await Promise.all([button.click(), button.click()]);
    await page.waitForTimeout(1000);
    await page.goto('/cart');
    const lineItems = page.locator('[class*="cart-item"], [class*="line-item"], tr[class*="cart"]');
    const count = await lineItems.count();
    expect(count, 'expected exactly one line item, not a duplicate').toBeLessThanOrEqual(1);
  });
});
