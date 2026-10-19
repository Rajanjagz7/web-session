import { test, expect } from '@playwright/test';
import { PROJECT } from './helpers';

const sections = ['', '/contacts', '/companies', '/deals', '/pipelines', '/reports', '/imports', '/exports', '/files', '/settings'];

for (const s of sections) {
  test(`[edge] no horizontal page scroll on mobile: ${s || 'overview'}`, async ({ page }) => {
    await page.goto(`/projects/${PROJECT}${s}`);
    await expect(page.locator('h1').first()).toBeVisible();
    const { scrollW, clientW } = await page.evaluate(() => ({
      scrollW: document.documentElement.scrollWidth,
      clientW: document.documentElement.clientWidth,
    }));
    expect(scrollW).toBeLessThanOrEqual(clientW);
  });
}
