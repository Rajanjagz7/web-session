const { chromium } = require('playwright');

async function debugFormValidation() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Click submit immediately to see what validation errors appear
  console.log('Clicking submit on empty form to see error messages:');
  await page.locator('#submitButton').click();
  await page.waitForTimeout(1000);

  const errors = await page.locator('.text-red-500, .error, [class*="errorMessage"]').allInnerTexts();
  console.log('Errors on empty form:', errors);

  await browser.close();
}

debugFormValidation().catch(console.error);
