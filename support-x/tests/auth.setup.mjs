// Logs in via the email/password form and saves the session.
// Credentials come from env vars (SUPPORTX_EMAIL / SUPPORTX_PASSWORD); never hard-code them.
import { chromium } from '@playwright/test';
const { SUPPORTX_EMAIL: email, SUPPORTX_PASSWORD: password } = process.env;
if (!email || !password) throw new Error('Set SUPPORTX_EMAIL and SUPPORTX_PASSWORD');
const browser = await chromium.launch({ headless: false, channel: 'chrome' });
const page = await (await browser.newContext()).newPage();
await page.goto('https://dev.pmx.softwareco.com/login');
await page.locator('input[type=text]').fill(email);
await page.locator('input[type=password]').fill(password);
await page.getByRole('button', { name: 'Login', exact: true }).click();
await page.waitForURL(u => !u.pathname.includes('/login'), { timeout: 60000 });
await page.waitForLoadState('networkidle');
await page.context().storageState({ path: 'test-data/auth.json' });
console.log('Saved test-data/auth.json at', page.url());
await page.screenshot({ path: 'test-data/after-login.png' });
await browser.close();
