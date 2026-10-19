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

  // Click on "Post Install Details" tab
  console.log('Clicking Post Install Details tab...');
  await page.getByRole('button', { name: 'Post Install Details' }).click();
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'post-install-details.png' });
  console.log('Saved post-install-details.png');

  // Check file inputs
  const fileInputs = await page.locator('input[type="file"]').all();
  console.log(`Post Install Details file inputs count: ${fileInputs.length}`);
  for (let i = 0; i < fileInputs.length; i++) {
    const html = await fileInputs[i].evaluate(el => el.outerHTML);
    console.log(`File input ${i}: ${html}`);
  }

  // Also check upload buttons
  const uploadBtns = await page.locator('button:has-text("Upload"), span:has-text("Upload")').all();
  console.log(`Found ${uploadBtns.length} Upload buttons/spans`);
  for (const b of uploadBtns) {
    console.log('Upload btn text:', (await b.innerText().catch(() => '')).trim());
  }

  await browser.close();
})();
