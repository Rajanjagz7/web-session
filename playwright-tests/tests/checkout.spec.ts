import { test, expect } from './fixtures';
import { addFirstProductToCart } from './helpers';
import { Page } from '@playwright/test';

/**
 * Reaches a live Shopify checkout by adding a product and using the cart's
 * checkout button. The /checkouts/cn/<token> URL is single-session, so it
 * can't be hard-coded; set CHECKOUT_URL to test one specific session instead.
 * Tests stop before payment — no real orders are placed.
 */
async function goToCheckout(page: Page) {
  if (process.env.CHECKOUT_URL) {
    await page.goto(process.env.CHECKOUT_URL);
  } else {
    await addFirstProductToCart(page);
    await page.goto('/cart');
    const checkoutBtn = page
      .locator('button[name="checkout"], input[name="checkout"], a[href*="/checkout"]')
      .or(page.getByRole('button', { name: /check\s?out/i }))
      .locator('visible=true')
      .first();
    await expect(checkoutBtn, 'expected a checkout button on /cart').toBeVisible({ timeout: 20_000 });
    await checkoutBtn.click();
  }
  await page.waitForURL(/\/checkouts\//, { timeout: 30_000 });
  await page.waitForLoadState('domcontentloaded');
}

test.describe.configure({ timeout: 120_000 });

const emailInput = (page: Page) =>
  page.locator('input[name="email"], input[autocomplete="email"], input[type="email"]').first();

test.describe('Checkout — page load (CO-01..CO-03)', () => {
  test('CO-01 checkout URL loads on the store domain with /checkouts/ path', async ({ unlockedPage: page }) => {
    await goToCheckout(page);
    expect(page.url()).toMatch(/\/checkouts\//);
    await expect(page.locator('body')).not.toContainText(/404|page not found/i);
  });

  test('CO-02 contact email field is present', async ({ unlockedPage: page }) => {
    await goToCheckout(page);
    await expect(emailInput(page)).toBeVisible({ timeout: 20_000 });
  });

  test('CO-03 order summary shows the product and a total', async ({ unlockedPage: page }) => {
    await goToCheckout(page);
    const summary = page.getByRole('complementary');
    await expect(summary.getByRole('heading', { name: /order summary/i })).toBeVisible({ timeout: 20_000 });
    await expect(summary.getByRole('row').filter({ hasText: /^Total/ })).toContainText(/AUD\s*\$\d/);
    await expect(summary.getByRole('row').filter({ hasText: /^Subtotal/ })).toContainText(/\$\d/);
  });
});

test.describe('Checkout — validation (CV-01..CV-03)', () => {
  test('CV-01 invalid email format is rejected', async ({ unlockedPage: page }) => {
    await goToCheckout(page);
    const email = emailInput(page);
    await expect(email).toBeVisible({ timeout: 20_000 });
    await email.fill('not-an-email');
    await email.blur();
    await expect(page.getByText(/enter a valid email|invalid email|valid email/i).first()).toBeVisible();
  });

  test('CV-02 submitting with required fields empty shows errors and does not advance', async ({ unlockedPage: page }) => {
    await goToCheckout(page);
    const submit = page
      .getByRole('button', { name: /pay now|continue to shipping/i })
      .first();
    await expect(submit).toBeVisible({ timeout: 20_000 });
    await submit.click();
    await expect(page.getByText(/enter an? |required|can't be blank|select a/i).first()).toBeVisible();
    expect(page.url()).toMatch(/\/checkouts\//);
  });

  test('CV-03 discount code field rejects an invalid code', async ({ unlockedPage: page }) => {
    await goToCheckout(page);
    const code = page.getByRole('textbox', { name: /discount code/i }).first();
    // On narrow viewports the field is collapsed behind an "Add discount" toggle.
    if (!(await code.isVisible({ timeout: 5_000 }).catch(() => false))) {
      await page.getByRole('button', { name: /add discount/i }).click({ force: true });
    }
    if (!(await code.isVisible({ timeout: 10_000 }).catch(() => false))) {
      test.skip(true, 'No discount field visible on this checkout.');
      return;
    }
    await code.fill('INVALID-CODE-123');
    await page.getByRole('button', { name: /apply discount code/i }).click();
    await expect(page.getByText(/enter a valid discount code|unable to apply|couldn't be applied/i).first()).toBeVisible({
      timeout: 15_000,
    });
  });
});

test.describe('Checkout — region (CR-01)', () => {
  test('CR-01 en-au checkout shows Australia as the default country', async ({ unlockedPage: page }) => {
    await goToCheckout(page);
    const country = page.getByRole('combobox', { name: /country\/region/i });
    await expect(country).toBeVisible({ timeout: 20_000 });
    await expect(country.locator('option:checked')).toHaveText('Australia');
  });
});
