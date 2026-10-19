const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 950 } });
  const page = await context.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobId = '6ab2438c7c29b5bf7379e390';
  await page.goto(`https://nswdev.rebatem8.com.au/jobs/${jobId}`);
  await page.waitForTimeout(4000);

  await page.screenshot({ path: 'job-380-nomination-signed.png', fullPage: true });

  // Get full job data from API
  const jobData = await page.evaluate(async (id) => {
    const r = await fetch(`/api/v1/jobs/${id}`);
    return await r.json();
  }, jobId);

  console.log('Current job status:', jobData.data?.job?.status);

  // Look for all buttons and text on the page
  const buttons = await page.locator('button').evaluateAll(btns => btns.map(b => ({
    text: b.innerText.trim(),
    visible: b.offsetWidth > 0,
    disabled: b.disabled
  })).filter(b => b.text.length > 0));
  console.log('Buttons on job detail page:', buttons);

  // Check what tabs exist
  const tabs = await page.locator('[role="tab"], .tab, [class*="tab"]').evaluateAll(ts => ts.map(t => t.innerText.trim()));
  console.log('Tabs:', tabs);

  // Check the photos tab
  const photosTab = page.locator('button, div, a').filter({ hasText: /^Photos/i }).first();
  if (await photosTab.isVisible()) {
    await photosTab.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'job-380-photos-tab.png', fullPage: true });
  }

  await browser.close();
})();
