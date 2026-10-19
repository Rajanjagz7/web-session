const { chromium } = require('playwright');

const BASE_URL = 'https://nswdev.rebatem8.com.au';
const EMAIL = 'johns@softwareco.com';
const PASSWORD = 'admin@123';

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  console.log('Navigating to', BASE_URL);
  await page.goto(`${BASE_URL}/log-in`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  console.log('Current URL:', page.url());

  const emailBox = page.getByPlaceholder(/email/i);
  if (await emailBox.isVisible({ timeout: 5000 }).catch(() => false)) {
    console.log('Filling login form...');
    await emailBox.fill(EMAIL);
    await page.getByPlaceholder(/password/i).fill(PASSWORD);
    await page.getByRole('button', { name: /log in/i }).click();
    await page.waitForTimeout(4000);
    console.log('URL after login:', page.url());
  } else {
    console.log('Email box not visible. Page text:');
    console.log(await page.locator('body').innerText());
  }

  // Go to /jobs
  await page.goto(`${BASE_URL}/jobs`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  console.log('URL at jobs:', page.url());

  // Check Add Job button
  const addJobBtn = page.getByRole('button', { name: /add job/i });
  if (await addJobBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    console.log('Add Job button found! Clicking...');
    await addJobBtn.click();
    await page.waitForTimeout(2000);
    
    // Dump modal/form fields
    const modal = page.locator('div[role="dialog"], .modal, form').first();
    console.log('Modal visible:', await modal.isVisible().catch(() => false));
    console.log('Modal text content:');
    console.log(await modal.innerText().catch(() => 'none'));
  } else {
    console.log('Add Job button not found.');
    console.log('Page content summary:');
    console.log(await page.locator('body').innerText());
  }

  await browser.close();
}

main().catch(console.error);
