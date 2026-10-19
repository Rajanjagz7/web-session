import { test, expect } from './fixtures';

test.describe('Home page — blog posts (BL-01..BL-04)', () => {
  test('BL-01 post cards without an image show a placeholder, not a broken icon', async ({ unlockedPage: page }) => {
    const blogSection = page.locator('[class*="blog"], [id*="blog"]').first();
    if (!(await blogSection.isVisible().catch(() => false))) {
      test.skip(true, 'No blog section detected on Home page.');
      return;
    }
    const images = blogSection.locator('img');
    const imgCount = await images.count();
    for (let i = 0; i < imgCount; i++) {
      const naturalWidth = await images.nth(i).evaluate((img: HTMLImageElement) => img.naturalWidth).catch(() => -1);
      expect(naturalWidth, `image ${i} in blog section should load, not be a broken icon`).not.toBe(0);
    }
  });

  test('BL-03 long post titles wrap inside their card, no overflow', async ({ unlockedPage: page }) => {
    const titles = page.locator('[class*="blog"] [class*="title"], [class*="blog"] h3');
    const count = await titles.count();
    if (count === 0) {
      test.skip(true, 'No blog post titles detected on Home page.');
      return;
    }
    for (let i = 0; i < count; i++) {
      const el = titles.nth(i);
      const overflowing = await el.evaluate((node) => node.scrollWidth > node.clientWidth + 1);
      expect(overflowing, `blog title ${i} should wrap, not overflow its container`).toBeFalsy();
    }
  });

  test('BL-04 nonexistent blog post URL returns a themed 404, not a raw error', async ({ unlockedPage: page }) => {
    const response = await page.goto('/blogs/news/invalid-slug-does-not-exist');
    expect(response?.status()).toBe(404);
    await expect(page.locator('body')).not.toContainText(/internal server error|500/i);
  });
});
