import { test, expect } from '@playwright/test';
import { PROJECT } from './helpers';

const sections = ['', '/contacts', '/companies', '/deals', '/pipelines', '/reports', '/audit', '/imports', '/exports', '/settings'];

for (const s of sections) {
  test(`[a11y] structure basics: ${s || 'overview'}`, async ({ page }) => {
    await page.goto(`/projects/${PROJECT}${s}`);
    await expect(page.locator('h1').first()).toBeVisible(); // client-rendered: wait for the page heading
    const r = await page.evaluate(() => {
      const nameOf = (e: Element) => (e.getAttribute('aria-label') || e.textContent || (e as HTMLElement).title || '').trim();
      return {
        lang: document.documentElement.lang,
        h1: document.querySelectorAll('h1').length,
        unnamed: [...document.querySelectorAll('button,a[href]')].filter((e) => !nameOf(e) && !e.querySelector('img[alt]')).length,
        noAlt: document.querySelectorAll('img:not([alt])').length,
        positiveTabindex: [...document.querySelectorAll('[tabindex]')].filter((e) => +(e.getAttribute('tabindex') ?? 0) > 0).length,
      };
    });
    expect(r.lang).not.toBe('');
    expect(r.h1).toBe(1);
    expect(r.unnamed).toBe(0);
    expect(r.noAlt).toBe(0);
    expect(r.positiveTabindex).toBe(0);
  });
}

test('[known_bug] heading levels should not skip (Reports)', async ({ page }) => {
  test.fail(true, 'BUG: Reports skips from h1 to h3');
  await page.goto(`/projects/${PROJECT}/reports`);
  await expect(page.locator('h1').first()).toBeVisible();
  await page.waitForLoadState('networkidle');
  const skipped = await page.evaluate(() => {
    const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map((h) => +h.tagName[1]);
    return hs.some((n, i) => i > 0 && n - hs[i - 1] > 1);
  });
  expect(skipped).toBe(false);
});
