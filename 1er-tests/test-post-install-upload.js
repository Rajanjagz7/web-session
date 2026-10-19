const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('api') || res.url().includes('s3')) {
      if (res.request().method() !== 'GET') {
        console.log(`[UPLOAD RES] ${res.status()} ${res.request().method()} ${res.url()}`);
      }
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobId = '6ab2438c7c29b5bf7379e390';
  await page.goto(`https://nswdev.rebatem8.com.au/jobs/${jobId}`);
  await page.waitForTimeout(3000);

  // Click Post Install Details tab
  await page.getByRole('button', { name: 'Post Install Details' }).click();
  await page.waitForTimeout(2000);

  const testImg = path.resolve(__dirname, 'test-images/air-conditioner-outdoor-unit.jpg');

  // Find all file inputs on this tab
  const fileInputs = await page.locator('input[type="file"]').all();
  console.log(`Found ${fileInputs.length} file inputs`);

  // Upload to first input (Tax Invoice)
  if (fileInputs.length > 0) {
    console.log('Uploading image to first file input (Tax Invoice)...');
    await fileInputs[0].setInputFiles(testImg);
    await page.waitForTimeout(4000);
  }

  // Upload to CCEW input
  if (fileInputs.length > 2) {
    console.log('Uploading image to CCEW file input...');
    const ccewImg = path.resolve(__dirname, 'test-images/heat-pump-nameplate.jpg');
    await fileInputs[2].setInputFiles(ccewImg);
    await page.waitForTimeout(4000);
  }

  // Click Save button if present
  const saveBtn = page.getByRole('button', { name: 'Save' });
  if (await saveBtn.isVisible()) {
    console.log('Clicking Save button...');
    await saveBtn.click();
    await page.waitForTimeout(4000);
  }

  await page.screenshot({ path: 'm8n000380-post-install-uploaded.png' });
  console.log('Saved m8n000380-post-install-uploaded.png');

  await browser.close();
})();
