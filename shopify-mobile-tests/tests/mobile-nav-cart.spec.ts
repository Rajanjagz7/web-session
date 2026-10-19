import { test, expect } from '@playwright/test';
import { CartPage } from './pages/CartPage';
import { HeaderNavPage } from './pages/HeaderNavPage';
import { CollectionPage } from './pages/CollectionPage';
import { swipeUp } from './utils/touch';

// Scope: mobile burger-menu navigation and cart-page behaviour only.
// The store's mobile "Log in" entry point redirects off-domain to
// Shopify's passwordless hosted Customer Accounts (shopify.com/.../account)
// - there's no on-site username/password login reachable from mobile and no
// test credentials for it, so that step is intentionally out of scope here.
test.describe('Mobile cart & navigation (Pixel 9, dark mode)', () => {
  test('burger menu expands, exposes nav links, and a tapped link navigates correctly', async ({ page }) => {
    const cart = new CartPage(page);
    const header = new HeaderNavPage(page);

    await test.step('Load the cart page', async () => {
      await cart.goto();
      await expect(page).toHaveScreenshot('cart-page-empty.png', { fullPage: true });
    });

    await test.step('Mobile burger menu is visible', async () => {
      await expect(header.burgerButton).toBeVisible();
    });

    await test.step('Tap the burger menu to expand the drawer', async () => {
      await header.open();
      await expect(page).toHaveScreenshot('menu-drawer-open.png');
    });

    await test.step('Drawer exposes the store nav links', async () => {
      await expect(header.navLink('CLIPPERS & ELECTRICALS')).toBeVisible();
      await expect(header.navLink('HAIR PRODUCTS')).toBeVisible();
      await expect(header.navLink('BARBER ESSENTIALS')).toBeVisible();
      await expect(header.navLink('BUNDLES & KITS')).toBeVisible();
    });

    await test.step('Tapping a nav link navigates to its collection', async () => {
      await header.navLink('CLIPPERS & ELECTRICALS').tap();
      await page.waitForURL(/\/collections\/barbercon/);

      const collection = new CollectionPage(page);
      await collection.expectLoaded(/BarberCon/i);
      await expect(page).toHaveScreenshot('collection-page-loaded.png', { fullPage: true });
    });

    await test.step('Swipe up scrolls the collection page', async () => {
      const scrollBefore = await page.evaluate(() => window.scrollY);
      await swipeUp(page);
      await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(scrollBefore);
    });
  });

  test('burger menu closes via its close button', async ({ page }) => {
    const cart = new CartPage(page);
    const header = new HeaderNavPage(page);

    await cart.goto();
    await header.open();
    await header.close();
  });
});
