import { test as setup, expect } from '@playwright/test';
import fs from 'fs';

const FOOD_ID = process.env.FOOD_ID!;

// Logs in once, saves the session, and captures the food's ORIGINAL saved payload
// (by pressing Update unchanged) so every test can restore staging data afterwards.
setup('login and capture original food payload', async ({ page }) => {
  await page.goto('/sign-in');
  await page.getByRole('textbox', { name: 'Email address' }).fill(process.env.WP_EMAIL!);
  await page.getByRole('textbox', { name: 'Password' }).fill(process.env.WP_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/user/);
  await page.context().storageState({ path: '.auth/user.json' });

  if (fs.existsSync('.auth/original.json')) return; // keep first-ever capture as the source of truth

  await page.goto(`/foods/edit/${FOOD_ID}`);
  await expect(page.getByRole('textbox', { name: 'Serving name' }).first()).toBeVisible();
  const [req] = await Promise.all([
    page.waitForRequest((r) => r.method() === 'PUT' && r.url().includes('/food-search/edit/')),
    page.getByRole('button', { name: 'Update' }).click(),
  ]);
  const headers = { ...req.headers() };
  for (const h of ['content-length', 'host', 'cookie', 'origin', 'referer']) delete headers[h];
  fs.writeFileSync('.auth/original.json', JSON.stringify({ data: req.postDataJSON(), headers }, null, 2));
});
