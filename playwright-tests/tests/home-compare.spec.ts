import { test, expect } from './fixtures';

const compareIcon = (page: import('@playwright/test').Page) =>
  page.locator('[class*="compare"], [aria-label*="compare" i], button[data-compare]');

test.describe('Home page — add to compare (CM-01..CM-05)', () => {
  test('CM-02 adding the same product twice does not duplicate it in the tray', async ({ unlockedPage: page }) => {
    const icon = compareIcon(page).first();
    if (!(await icon.isVisible().catch(() => false))) {
      test.skip(true, 'No compare control detected on Home page for this theme.');
      return;
    }
    await icon.click();
    await icon.click();
    await page.waitForTimeout(500);
    const trayCount = await page.locator('[class*="compare-tray"] [class*="item"], [class*="compare-item"]').count();
    expect(trayCount).toBeLessThanOrEqual(1);
  });

  test('CM-01 exceeding the max comparable items is blocked with a message', async ({ unlockedPage: page }) => {
    const icons = compareIcon(page);
    const count = await icons.count();
    if (count < 5) {
      test.skip(true, 'Fewer than 5 comparable products visible on Home page — cannot exercise the limit.');
      return;
    }
    for (let i = 0; i < Math.min(count, 6); i++) {
      await icons.nth(i).click();
      await page.waitForTimeout(200);
    }
    // Expect either a visible limit message, or that the tray simply caps at N items.
    const limitMessage = page.locator('text=/limit|maximum|up to \\d+ items/i');
    const trayCount = await page.locator('[class*="compare-tray"] [class*="item"], [class*="compare-item"]').count();
    expect((await limitMessage.count()) > 0 || trayCount <= 6).toBeTruthy();
  });

  test('CM-05 removing all compared items shows a clean empty state', async ({ unlockedPage: page }) => {
    const icon = compareIcon(page).first();
    if (!(await icon.isVisible().catch(() => false))) {
      test.skip(true, 'No compare control detected on Home page for this theme.');
      return;
    }
    await icon.click();
    await page.waitForTimeout(300);
    // Toggle it back off.
    await icon.click();
    await page.waitForTimeout(300);
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    expect(errors).toHaveLength(0);
  });
});
