const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('api') && res.request().method() !== 'GET') {
      console.log(`[NET RES] ${res.status()} ${res.request().method()} ${res.url()}`);
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

  // Check if energy bill is already attached or upload again if needed
  const fileInput = page.locator('input[type="file"].upload-input');
  if (await fileInput.count() > 0) {
    const testImagePath = path.resolve(__dirname, 'test-images/energy-bill-coastal-enterprises.png');
    console.log('Attaching energy bill image...');
    await fileInput.setInputFiles(testImagePath);
    await page.waitForTimeout(4000);
  } else {
    console.log('Energy bill already attached!');
  }

  // Select Plumber if not selected
  const plumberVal = await page.locator('div').filter({ hasText: /^Dhruti Patel$/ }).first().count();
  if (plumberVal === 0) {
    console.log('Selecting Plumber...');
    await page.locator('.select__control').first().click();
    await page.waitForTimeout(1000);
    const option = page.locator('[class*="-option"]').filter({ hasText: 'Dhruti Patel' }).first();
    await option.click();
    await page.waitForTimeout(1000);
  }

  // Click "No" for Electrical Wiring Work Undertaken
  console.log('Clicking No for Electrical Wiring Work Undertaken...');
  const noBtn = page.getByRole('button', { name: 'No' });
  await noBtn.click();
  await page.waitForTimeout(1000);

  await page.screenshot({ path: 'm8n000380-before-valid-send.png' });

  // Click Send
  const sendBtn = page.getByRole('button', { name: 'Send' });
  console.log('Clicking Send...');
  await sendBtn.click();
  await page.waitForTimeout(5000);

  await page.screenshot({ path: 'm8n000380-after-valid-send.png' });
  console.log('Saved m8n000380-after-valid-send.png. URL:', page.url());

  // Check updated status
  const jobStatus = await page.evaluate(async () => {
    const res = await fetch('/api/v1/jobs?search=M8N000380');
    const data = await res.json();
    return data.data?.jobs?.[0]?.status;
  });
  console.log('Updated M8N000380 Status:', jobStatus);

  await browser.close();
})();
