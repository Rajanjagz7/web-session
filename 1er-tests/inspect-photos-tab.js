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

  // Click on Photos tab
  console.log('Clicking Photos tab...');
  const photosTab = page.getByRole('button', { name: 'Photos' });
  await photosTab.click();
  await page.waitForTimeout(2500);

  await page.screenshot({ path: 'job-detail-photos-tab.png' });
  console.log('Saved job-detail-photos-tab.png');

  // Inspect elements inside photos tab
  const buttons = await page.locator('button').allInnerTexts();
  console.log('Buttons on Photos tab:', buttons.filter(b => b.trim().length > 0));

  const fileInputs = await page.locator('input[type="file"]').all();
  console.log(`Photos tab file inputs count: ${fileInputs.length}`);
  for (let i = 0; i < fileInputs.length; i++) {
    const html = await fileInputs[i].evaluate(el => el.outerHTML);
    console.log(`File input ${i}: ${html}`);
  }

  // Also click on "Existing Unit Photos", "Decommission Unit Photos", "New Unit Photos" cards at top
  const cards = await page.locator('div:has-text("Existing Unit Photos"), div:has-text("New Unit Photos")').all();
  console.log(`Found ${cards.length} photo cards`);

  // Let's also check Documents tab
  const docsTab = page.getByRole('button', { name: 'Documents' });
  if (await docsTab.isVisible()) {
    console.log('Clicking Documents tab...');
    await docsTab.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'job-detail-documents-tab.png' });
    console.log('Saved job-detail-documents-tab.png');
  }

  await browser.close();
})();
