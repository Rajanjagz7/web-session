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

  // Click Photos tab
  await page.getByRole('button', { name: 'Photos' }).click();
  await page.waitForTimeout(2000);

  // Scroll down and screenshot
  await page.evaluate(() => window.scrollBy(0, 600));
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'photos-tab-scrolled-1.png' });

  await page.evaluate(() => window.scrollBy(0, 600));
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'photos-tab-scrolled-2.png' });

  // Check all accordion headers or collapse elements
  const accordions = await page.locator('.collapse, [class*="accordion"], [class*="collapse"]').all();
  console.log(`Found ${accordions.length} accordions`);
  for (let i = 0; i < accordions.length; i++) {
    const text = (await accordions[i].innerText().catch(() => '')).trim().split('\n')[0];
    console.log(`Accordion ${i}: "${text}"`);
  }

  // Click on "Existing Unit Photos" card at top
  const existingCard = page.locator('div').filter({ hasText: /^Existing Unit Photos/ }).first();
  if (await existingCard.isVisible()) {
    console.log('Clicking Existing Unit Photos card...');
    await existingCard.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'after-click-existing-card.png' });
  }

  await browser.close();
})();
