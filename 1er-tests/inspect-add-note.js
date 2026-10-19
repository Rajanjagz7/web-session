const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('api') || res.url().includes('storage') || res.url().includes('s3')) {
      if (res.request().method() !== 'GET') {
        console.log(`[NET] ${res.status()} ${res.request().method()} ${res.url()}`);
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

  // Click Notes tab
  await page.getByRole('button', { name: 'Notes' }).click();
  await page.waitForTimeout(2000);

  // Click Add Note button
  const addNoteBtn = page.getByRole('button', { name: 'Add Note' }).or(page.locator('button:has-text("Add Note")'));
  console.log('Clicking Add Note button...');
  await addNoteBtn.click();
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'after-click-add-note.png' });
  console.log('Saved after-click-add-note.png');

  // Find note input / textarea
  const textareas = await page.locator('textarea, [contenteditable="true"], input[type="text"]').all();
  console.log(`Found ${textareas.length} text inputs`);

  // Find file input
  const fileInputs = await page.locator('input[type="file"]').all();
  console.log(`File inputs: ${fileInputs.length}`);
  for (let i = 0; i < fileInputs.length; i++) {
    console.log(`Input ${i}:`, await fileInputs[i].evaluate(el => el.outerHTML));
  }

  await browser.close();
})();
