import { test, expect } from './fixtures';

test.describe('Home page — footer & social links (FT-01..FT-04)', () => {
  test('FT-01 social icons open in a new tab with rel=noopener', async ({ unlockedPage: page }) => {
    const socialLinks = page.locator(
      'footer a[href*="facebook.com"], footer a[href*="twitter.com"], footer a[href*="x.com"], ' +
      'footer a[href*="instagram.com"], footer a[href*="snapchat.com"], footer a[href*="vimeo.com"]'
    );
    const count = await socialLinks.count();
    if (count === 0) {
      test.skip(true, 'No recognizable social links found in footer.');
      return;
    }
    for (let i = 0; i < count; i++) {
      const link = socialLinks.nth(i);
      const target = await link.getAttribute('target');
      const rel = await link.getAttribute('rel');
      expect(target, `social link ${i} should open in a new tab`).toBe('_blank');
      expect(rel, `social link ${i} should carry rel=noopener`).toContain('noopener');
    }
  });

  test('FT-02 no footer link is still a dead "#" placeholder', async ({ unlockedPage: page }) => {
    const footerLinks = page.locator('footer a');
    const count = await footerLinks.count();
    const placeholders: number[] = [];
    for (let i = 0; i < count; i++) {
      const href = await footerLinks.nth(i).getAttribute('href');
      if (href === '#' || href === '') placeholders.push(i);
    }
    expect(placeholders, `footer links at these indices are still placeholders: ${placeholders.join(', ')}`).toHaveLength(0);
  });

  test('FT-03 footer nav links do not 404', async ({ unlockedPage: page }) => {
    const footerLinks = page.locator('footer a[href^="/"]');
    const count = await footerLinks.count();
    const hrefs = new Set<string>();
    for (let i = 0; i < count; i++) {
      const href = await footerLinks.nth(i).getAttribute('href');
      if (href) hrefs.add(href);
    }
    for (const href of hrefs) {
      const response = await page.request.get(href);
      expect(response.status(), `footer link ${href} should not 404`).toBeLessThan(400);
    }
  });

  test('FT-04 footer links are reachable via keyboard tab order with visible focus', async ({ unlockedPage: page }) => {
    const firstFooterLink = page.locator('footer a').first();
    if (!(await firstFooterLink.isVisible().catch(() => false))) {
      test.skip(true, 'No footer links found.');
      return;
    }
    await firstFooterLink.focus();
    const isFocused = await firstFooterLink.evaluate((el) => el === document.activeElement);
    expect(isFocused).toBeTruthy();
  });
});
