const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const searchInput = page.getByPlaceholder('Search Jobs...');
  await searchInput.fill('M8N000378');
  await page.waitForTimeout(1500);

  const row = page.locator('tr').filter({ hasText: 'M8N000378' }).first();
  const eyeIcon = row.locator('.cursor-pointer').first();
  await eyeIcon.click();
  await page.waitForTimeout(2500);

  await page.screenshot({ path: 'job-view-M8N000378.png' });
  console.log('Saved job-view-M8N000378.png');

  const fileInput = page.locator('input[type="file"].upload-input');
  if (await fileInput.count() > 0) {
    const testImagePath = path.resolve(__dirname, 'test-images/energy-bill-sydney-tech.png');
    console.log('Attaching energy bill image to M8N000378...');
    await fileInput.setInputFiles(testImagePath);
    await page.waitForTimeout(5000);
    await page.screenshot({ path: 'm8n000378-after-upload.png' });
    console.log('Saved m8n000378-after-upload.png');
  } else {
    console.log('No file input found on M8N000378');
  }

  await browser.close();
})();
