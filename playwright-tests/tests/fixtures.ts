import { test as base, expect, Page } from '@playwright/test';

const STORE_PASSWORD = process.env.STORE_PASSWORD || 'giecla';

/**
 * Unlocks the Shopify password gate before every test.
 * Generic selector on purpose: the real theme markup wasn't available
 * to inspect, so this targets the one input[type=password] on the page
 * rather than a guessed id/class.
 */
async function unlockStore(page: Page) {
  await page.goto('/');
  // The gate hides the password field behind an "Enter using password" toggle.
  const gateToggle = page.getByRole('button', { name: /enter using password/i });
  if (await gateToggle.isVisible().catch(() => false)) {
    await gateToggle.click();
  }
  const passwordInput = page.locator('input[type="password"]').first();
  if (await passwordInput.isVisible().catch(() => false)) {
    await passwordInput.fill(STORE_PASSWORD);
    await passwordInput.press('Enter');
    await page.waitForLoadState('networkidle');
  }
}

export const test = base.extend<{ unlockedPage: Page }>({
  unlockedPage: async ({ page }, use) => {
    await unlockStore(page);
    await use(page);
  },
});

export { expect };
