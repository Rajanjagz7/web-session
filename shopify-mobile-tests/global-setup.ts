import 'dotenv/config';
import { chromium, devices, type FullConfig } from '@playwright/test';
import path from 'path';

export const STORAGE_STATE_PATH = path.join(__dirname, '.auth', 'storefront.json');

/**
 * The store sits behind Shopify's "coming soon" password gate: any
 * unauthenticated request 302s to /password. Unlocking it once here and
 * reusing the resulting cookie via storageState avoids repeating the
 * password-modal flow (and its own touch interactions) inside every spec.
 */
export default async function globalSetup(config: FullConfig) {
  const password = process.env.STORE_PASSWORD;
  if (!password) {
    throw new Error(
      'STORE_PASSWORD env var is required to unlock the storefront password gate (see .env.example).'
    );
  }

  const baseURL = config.projects[0]?.use?.baseURL as string;
  const browser = await chromium.launch();
  const context = await browser.newContext({ ...devices['Pixel 9'], baseURL });
  const page = await context.newPage();

  await page.goto('/');

  if (page.url().includes('/password')) {
    await page.getByRole('button', { name: /enter using password/i }).click();
    await page.getByLabel('Your password').fill(password);
    await page.getByRole('button', { name: 'Enter', exact: true }).click();
    await page.waitForURL((url) => !url.pathname.includes('/password'));
  }

  await context.storageState({ path: STORAGE_STATE_PATH });
  await browser.close();
}
