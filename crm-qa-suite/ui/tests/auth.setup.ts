import { test as setup, expect } from '@playwright/test';
import { AUTH_FILE } from '../playwright.config';

// Logs in once and stores the session; credentials come only from environment variables.
setup('authenticate', async ({ page }) => {
  const email = process.env.CRM_EMAIL;
  const password = process.env.CRM_PASSWORD;
  if (!email || !password) throw new Error('CRM_EMAIL and CRM_PASSWORD must be set (see .env.example)');
  await page.goto('/login');
  await page.getByRole('textbox', { name: 'Email' }).fill(email);
  await page.getByRole('textbox', { name: 'Password' }).fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).not.toHaveURL(/\/login/);
  await page.context().storageState({ path: AUTH_FILE });
});
