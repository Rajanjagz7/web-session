import { test as base } from './index';
import { InventoryPage } from '@pages/InventoryPage';
import { config } from '@config/index';

type AuthFixtures = {
  authenticatedInventoryPage: InventoryPage;
};

/**
 * Extends the base fixtures with a `storageState` override so the browser
 * context starts already logged in (cookies + localStorage captured once via
 * a real UI login), instead of re-running the login flow in every test.
 * Only import this `test` for suites that want to start authenticated
 * (Inventory/Cart/Checkout) -- Login and AccessControl suites must stay on
 * the plain @fixtures import so they start logged out.
 */
export const test = base.extend<AuthFixtures>({
  storageState: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(config.ui.baseUrl);
    await page.getByPlaceholder('Username').fill(config.credentials.username);
    await page.getByPlaceholder('Password').fill(config.credentials.password);
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL(/inventory\.html/);
    const storage = await context.storageState();
    await context.close();
    await use(storage);
  },

  authenticatedInventoryPage: async ({ page, inventoryPage }, use) => {
    await page.goto('/inventory.html');
    await use(inventoryPage);
  },
});

export { expect } from '@playwright/test';
