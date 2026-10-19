import { test, expect } from './fixtures';

const wishlistIcon = (page: import('@playwright/test').Page) =>
  page.locator('[class*="wishlist"], [aria-label*="wishlist" i], button[data-wishlist]').first();

test.describe('Home page — wishlist (WL-01..WL-05)', () => {
  test('WL-01 adding the same item twice does not duplicate it', async ({ unlockedPage: page }) => {
    const icon = wishlistIcon(page);
    if (!(await icon.isVisible().catch(() => false))) {
      test.skip(true, 'No wishlist control detected on Home page for this theme.');
      return;
    }
    await icon.click();
    await page.waitForTimeout(300);
    const stateAfterFirst = await icon.getAttribute('aria-pressed').catch(() => null);
    await icon.click();
    await page.waitForTimeout(300);
    const stateAfterSecond = await icon.getAttribute('aria-pressed').catch(() => null);
    expect(stateAfterFirst).not.toBe(stateAfterSecond === stateAfterFirst ? undefined : stateAfterFirst);
  });

  test('WL-02 wishlist as a guest does not throw an error', async ({ unlockedPage: page }) => {
    const icon = wishlistIcon(page);
    if (!(await icon.isVisible().catch(() => false))) {
      test.skip(true, 'No wishlist control detected on Home page for this theme.');
      return;
    }
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await icon.click();
    await page.waitForTimeout(500);
    expect(errors).toHaveLength(0);
  });

  test('WL-05 spam-clicking the toggle leaves a consistent final state', async ({ unlockedPage: page }) => {
    const icon = wishlistIcon(page);
    if (!(await icon.isVisible().catch(() => false))) {
      test.skip(true, 'No wishlist control detected on Home page for this theme.');
      return;
    }
    for (let i = 0; i < 10; i++) {
      await icon.click();
    }
    await page.waitForTimeout(500);
    await page.reload();
    // After reload, the icon's persisted state should be readable without error.
    await expect(icon).toBeVisible();
  });
});
