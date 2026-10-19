const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('api')) {
      console.log(`[API ${res.request().method()}] ${res.status()} ${res.url()}`);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const searchInput = page.getByPlaceholder('Search Jobs...');
  await searchInput.fill('M8N000380');
  await page.waitForTimeout(1500);

  const row = page.locator('tr').filter({ hasText: 'M8N000380' }).first();
  const eyeIcon = row.locator('.cursor-pointer').first();
  await eyeIcon.click();
  await page.waitForTimeout(2000);

  // Find file input
  const fileInputs = await page.locator('input[type="file"]').all();
  console.log(`Found ${fileInputs.length} file inputs on M8N000380`);
  for (let i = 0; i < fileInputs.length; i++) {
    const html = await fileInputs[i].evaluate(el => el.outerHTML);
    console.log(`File input ${i}: ${html}`);
  }

  // Also inspect any other tabs or sections in the modal/page
  const allTexts = await page.locator('[role="dialog"], [class*="drawer"], [class*="modal"]').innerText();
  console.log('--- Modal Content ---');
  console.log(allTexts);

  await browser.close();
})();
