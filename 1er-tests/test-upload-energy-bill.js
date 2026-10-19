const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => console.log(`[PAGE LOG] ${msg.type()}: ${msg.text()}`));
  page.on('request', req => {
    if (req.method() !== 'GET' || req.url().includes('upload') || req.url().includes('s3')) {
      console.log(`[REQ] ${req.method()} ${req.url()}`);
    }
  });
  page.on('response', res => {
    if (res.request().method() !== 'GET' || res.url().includes('upload') || res.url().includes('s3')) {
      console.log(`[RES] ${res.status()} ${res.url()}`);
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

  const testImagePath = path.resolve(__dirname, 'test-images/energy-bill-coastal-enterprises.png');
  console.log('Uploading file:', testImagePath);

  const fileInput = page.locator('input[type="file"].upload-input');
  await fileInput.setInputFiles(testImagePath);

  console.log('File set. Waiting 5 seconds...');
  await page.waitForTimeout(5000);

  await page.screenshot({ path: 'after-upload-energy-bill.png' });
  console.log('Saved after-upload-energy-bill.png');

  // Check if Send button is enabled
  const sendBtn = page.getByRole('button', { name: 'Send' });
  const isEnabled = await sendBtn.isEnabled();
  console.log('Send button is enabled:', isEnabled);

  if (isEnabled) {
    console.log('Clicking Send button...');
    await sendBtn.click();
    await page.waitForTimeout(4000);
    await page.screenshot({ path: 'after-send-bill.png' });
    console.log('Saved after-send-bill.png. URL:', page.url());
  }

  await browser.close();
})();
