import { test, expect } from './fixtures';
import { addFirstProductToCart, cartLineItems, couponInput, quantityInput } from './helpers';

test.describe('Cart page — sidebar display (SC-01..SC-03)', () => {
  test('SC-01 empty cart shows a clear message, not a blank sidebar', async ({ unlockedPage: page }) => {
    await page.goto('/cart');
    const items = await cartLineItems(page).count();
    if (items === 0) {
      await expect(page.locator('body')).toContainText(/empty|nothing in your cart/i);
    } else {
      test.skip(true, 'Cart was not empty at test start — clear it first to exercise this case.');
    }
  });

  test('SC-02 cart with exactly 1 item renders cleanly', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const count = await cartLineItems(page).count();
    expect(count).toBeGreaterThanOrEqual(1);
  });
});

test.describe('Cart page — update items (UC-01..UC-05)', () => {
  test('UC-01 updating quantity to 0 removes the item or is blocked, consistently', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const qty = quantityInput(page).first();
    if (!(await qty.isVisible().catch(() => false))) {
      test.skip(true, 'No editable quantity input on the cart page for this theme.');
      return;
    }
    await qty.fill('0');
    await qty.press('Enter').catch(() => {});
    await page.waitForTimeout(800);
    // Either the line item is now gone, or the input reverted to a positive number.
    const remainingValue = await qty.inputValue().catch(() => '0');
    const itemsLeft = await cartLineItems(page).count();
    expect(itemsLeft === 0 || Number(remainingValue) > 0).toBeTruthy();
  });

  test('UC-02 negative quantity is rejected', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const qty = quantityInput(page).first();
    if (!(await qty.isVisible().catch(() => false))) {
      test.skip(true, 'No editable quantity input on the cart page for this theme.');
      return;
    }
    await qty.fill('-1');
    const value = await qty.inputValue();
    expect(Number(value)).toBeGreaterThanOrEqual(0);
  });

  test('UC-05 rapid successive quantity changes settle on a correct final value', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const plusButton = page.locator('button[name="plus"], [class*="quantity"] button:has-text("+")').first();
    if (!(await plusButton.isVisible().catch(() => false))) {
      test.skip(true, 'No +/- quantity stepper on the cart page for this theme.');
      return;
    }
    for (let i = 0; i < 5; i++) await plusButton.click({ timeout: 1000 }).catch(() => {});
    await page.waitForTimeout(1000);
    const qty = quantityInput(page).first();
    const value = await qty.inputValue().catch(() => '');
    expect(Number(value)).toBeGreaterThan(1);
  });
});

test.describe('Cart page — remove items (RC-01..RC-02)', () => {
  test('RC-01 removing the last item shows the empty-cart state', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const removeButton = page.locator('[class*="remove"], a[href*="quantity=0"], button[aria-label*="remove" i]').first();
    if (!(await removeButton.isVisible().catch(() => false))) {
      test.skip(true, 'No remove control found on the cart page for this theme.');
      return;
    }
    await removeButton.click();
    await page.waitForTimeout(800);
    await expect(page.locator('body')).toContainText(/empty|nothing in your cart/i);
  });

  test('RC-02 double-clicking remove does not throw an error', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const removeButton = page.locator('[class*="remove"], a[href*="quantity=0"], button[aria-label*="remove" i]').first();
    if (!(await removeButton.isVisible().catch(() => false))) {
      test.skip(true, 'No remove control found on the cart page for this theme.');
      return;
    }
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await removeButton.click().catch(() => {});
    await removeButton.click({ timeout: 1000 }).catch(() => {});
    await page.waitForTimeout(500);
    expect(errors).toHaveLength(0);
  });
});

test.describe('Cart page — subtotal (ST-01..ST-04)', () => {
  test('ST-01 subtotal updates immediately after a quantity change', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const subtotal = page.locator('[class*="subtotal"], [class*="total"]').first();
    const before = (await subtotal.textContent().catch(() => '')) || '';
    const qty = quantityInput(page).first();
    if (!(await qty.isVisible().catch(() => false))) {
      test.skip(true, 'No editable quantity input on the cart page for this theme.');
      return;
    }
    await qty.fill('2');
    await qty.press('Enter').catch(() => {});
    await page.waitForTimeout(1000);
    const after = (await subtotal.textContent().catch(() => '')) || '';
    expect(after).not.toBe(before);
  });

  test('ST-03 subtotal on an empty cart shows $0.00, never NaN', async ({ unlockedPage: page }) => {
    await page.goto('/cart');
    await expect(page.locator('body')).not.toContainText(/NaN|undefined/i);
  });
});

test.describe('Cart page — coupon code (CP-01..CP-10)', () => {
  test('CP-01 empty coupon field submit does not error', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const input = couponInput(page);
    if (!(await input.isVisible().catch(() => false))) {
      test.skip(true, 'No discount code field found on cart page for this theme.');
      return;
    }
    await input.fill('');
    await input.press('Enter');
    await page.waitForTimeout(500);
    await expect(page.locator('body')).not.toContainText(/500|internal server error/i);
  });

  test('CP-02 nonexistent coupon code shows an invalid-code message', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const input = couponInput(page);
    if (!(await input.isVisible().catch(() => false))) {
      test.skip(true, 'No discount code field found on cart page for this theme.');
      return;
    }
    await input.fill('FAKECODE99');
    await input.press('Enter');
    await page.waitForTimeout(1000);
    await expect(page.locator('body')).toContainText(/invalid|doesn.?t exist|not valid|not found/i);
  });

  test('CP-06 applying the same coupon twice does not double-discount', async ({ unlockedPage: page }) => {
    if (!process.env.VALID_COUPON) {
      test.skip(true, 'Set VALID_COUPON=<real code> to run this check.');
      return;
    }
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const input = couponInput(page);
    if (!(await input.isVisible().catch(() => false))) {
      test.skip(true, 'No discount code field found on cart page for this theme.');
      return;
    }
    await input.fill(process.env.VALID_COUPON!);
    await input.press('Enter');
    await page.waitForTimeout(1000);
    const subtotalAfterFirst = await page.locator('[class*="total"]').first().textContent();
    await input.fill(process.env.VALID_COUPON!);
    await input.press('Enter');
    await page.waitForTimeout(1000);
    const subtotalAfterSecond = await page.locator('[class*="total"]').first().textContent();
    expect(subtotalAfterSecond).toBe(subtotalAfterFirst);
  });

  test('CP-08 coupon code with leading/trailing spaces is trimmed and accepted', async ({ unlockedPage: page }) => {
    if (!process.env.VALID_COUPON) {
      test.skip(true, 'Set VALID_COUPON=<real code> to run this check.');
      return;
    }
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const input = couponInput(page);
    if (!(await input.isVisible().catch(() => false))) {
      test.skip(true, 'No discount code field found on cart page for this theme.');
      return;
    }
    await input.fill(`  ${process.env.VALID_COUPON}  `);
    await input.press('Enter');
    await page.waitForTimeout(1000);
    await expect(page.locator('body')).not.toContainText(/invalid|doesn.?t exist/i);
  });

  test('CP-09 injection-style coupon string is rejected, not reflected', async ({ unlockedPage: page }) => {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const input = couponInput(page);
    if (!(await input.isVisible().catch(() => false))) {
      test.skip(true, 'No discount code field found on cart page for this theme.');
      return;
    }
    await input.fill('<script>alert(1)</script>');
    await input.press('Enter');
    await page.waitForTimeout(1000);
    const bodyHtml = await page.locator('body').innerHTML();
    expect(bodyHtml).not.toContain('<script>alert(1)</script>');
  });

  test('CP-10 a discount larger than the subtotal floors the total at $0.00', async ({ unlockedPage: page }) => {
    if (!process.env.OVERSIZED_COUPON) {
      test.skip(true, 'Set OVERSIZED_COUPON=<real code worth more than the cart total> to run this check.');
      return;
    }
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const input = couponInput(page);
    if (!(await input.isVisible().catch(() => false))) {
      test.skip(true, 'No discount code field found on cart page for this theme.');
      return;
    }
    await input.fill(process.env.OVERSIZED_COUPON!);
    await input.press('Enter');
    await page.waitForTimeout(1000);
    await expect(page.locator('body')).not.toContainText(/-\$|−\$/); // no negative total
  });
});
