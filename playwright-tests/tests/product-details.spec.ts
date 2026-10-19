import { test, expect } from './fixtures';
import { openFirstProduct } from './helpers';

test.describe('Product page — details (PD-01..PD-05)', () => {
  test('PD-01 product images load, no broken image icons', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const images = page.locator('[class*="product"] img, [class*="gallery"] img').first();
    if (!(await images.isVisible().catch(() => false))) {
      test.skip(true, 'No product image detected — product may genuinely have none; verify placeholder manually.');
      return;
    }
    const naturalWidth = await images.evaluate((img: HTMLImageElement) => img.naturalWidth);
    expect(naturalWidth).toBeGreaterThan(0);
  });

  test('PD-02 long title/description wraps within layout, no horizontal overflow', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const title = page.locator('h1').first();
    const overflowing = await title.evaluate((node) => node.scrollWidth > node.clientWidth + 1);
    expect(overflowing).toBeFalsy();
    const bodyOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    expect(bodyOverflow, 'page should not scroll horizontally').toBeFalsy();
  });

  test('PD-03 an out-of-stock product shows "sold out" and disables Add to Cart', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const soldOutLabel = page.locator('text=/sold out/i').first();
    if (!(await soldOutLabel.isVisible().catch(() => false))) {
      test.skip(true, 'First product in catalogue is in stock — point PRODUCT_URL at a sold-out product to run this check.');
      return;
    }
    const addButton = page.getByRole('button', { name: /add to cart/i });
    expect(await addButton.isDisabled()).toBeTruthy();
  });

  test('PD-04 a single-variant product does not render an empty/broken variant dropdown', async ({ unlockedPage: page }) => {
    await openFirstProduct(page);
    const variantSelect = page.locator('select[name*="option" i], [class*="variant"] select').first();
    if (await variantSelect.isVisible().catch(() => false)) {
      const optionCount = await variantSelect.locator('option').count();
      expect(optionCount).toBeGreaterThan(0);
    } else {
      test.skip(true, 'No variant selector present — likely a single-variant product, which is the expected pass case.');
    }
  });
});
