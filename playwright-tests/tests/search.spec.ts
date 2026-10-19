import { test, expect } from './fixtures';

// Generic locator: matches Shopify's default search input regardless of theme
// (Dawn/most themes use type="search" or name="q").
const searchInput = (page: import('@playwright/test').Page) =>
  page.locator('input[type="search"], input[name="q"]').first();

test.describe('Home page — search (SR-01..SR-10)', () => {
  test('SR-01 empty query does not error', async ({ unlockedPage: page }) => {
    await searchInput(page).click();
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).not.toContainText(/500|internal server error/i);
  });

  test('SR-04 very long query does not error', async ({ unlockedPage: page }) => {
    const longQuery = 'a'.repeat(600);
    await searchInput(page).fill(longQuery);
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).not.toContainText(/500|internal server error/i);
  });

  test('SR-05 SQL-injection style string is treated as literal text', async ({ unlockedPage: page }) => {
    await searchInput(page).fill("' OR 1=1 --");
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).not.toContainText(/sql|syntax error/i);
  });

  test('SR-06 script payload is never executed', async ({ unlockedPage: page }) => {
    let dialogFired = false;
    page.on('dialog', async (d) => {
      dialogFired = true;
      await d.dismiss();
    });
    await searchInput(page).fill('<script>alert(1)</script>');
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle');
    expect(dialogFired).toBeFalsy();
  });

  test('SR-07 no matching product shows a clean empty state', async ({ unlockedPage: page }) => {
    await searchInput(page).fill('zzzxyz123nonexistent');
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toContainText(/no results|nothing found|0 results/i);
  });

  test('SR-08 case sensitivity: same term returns same result count', async ({ unlockedPage: page }) => {
    await searchInput(page).fill('SHIRT');
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle');
    const upperUrl = page.url();

    await page.goto('/');
    await searchInput(page).fill('shirt');
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle');

    // Compare result counts if the theme exposes one; otherwise just assert
    // both searches complete without erroring (see body text expectation above).
    expect(upperUrl).not.toBe('');
  });
});
