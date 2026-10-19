const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobId = '6ab2438c7c29b5bf7379e390';
  await page.goto(`https://nswdev.rebatem8.com.au/jobs/${jobId}`);
  await page.waitForTimeout(3000);

  // Click on Notes tab
  console.log('Clicking Notes tab...');
  await page.getByRole('button', { name: 'Notes' }).click();
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'job-notes-tab.png' });
  console.log('Saved job-notes-tab.png');

  // Check buttons and inputs in Notes tab
  const buttons = await page.locator('button').allInnerTexts();
  console.log('Buttons on Notes tab:', buttons.filter(b => b.trim().length > 0));

  const fileInputs = await page.locator('input[type="file"]').all();
  console.log(`Notes tab file inputs: ${fileInputs.length}`);
  for (let i = 0; i < fileInputs.length; i++) {
    console.log(`File input ${i}:`, await fileInputs[i].evaluate(el => el.outerHTML));
  }

  await browser.close();
})();
