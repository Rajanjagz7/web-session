const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('api') || res.url().includes('signature') || res.url().includes('s3')) {
      if (res.request().method() !== 'GET') {
        console.log(`[SIG RES] ${res.status()} ${res.request().method()} ${res.url()}`);
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

  // Look for canvas
  const canvas = page.locator('canvas').first();
  if (await canvas.isVisible()) {
    console.log('Found canvas, drawing signature...');
    const box = await canvas.boundingBox();
    if (box) {
      await page.mouse.move(box.x + 20, box.y + 20);
      await page.mouse.down();
      await page.mouse.move(box.x + 80, box.y + 50);
      await page.mouse.move(box.x + 140, box.y + 25);
      await page.mouse.move(box.x + 200, box.y + 60);
      await page.mouse.up();
      console.log('Signature drawn!');
      await page.waitForTimeout(1000);

      // Select installer if dropdown exists
      const installerSelect = page.locator('div').filter({ hasText: /^Select Primary Signature$/ }).last();
      if (await installerSelect.isVisible()) {
        await installerSelect.click();
        await page.waitForTimeout(500);
        await page.locator('[class*="-option"]').first().click().catch(() => {});
      }

      // Click Save Signature
      const saveSig = page.getByRole('button', { name: 'Save Signature' }).or(page.locator('button:has-text("Save Signature")'));
      if (await saveSig.isVisible()) {
        console.log('Clicking Save Signature...');
        await saveSig.click();
        await page.waitForTimeout(4000);
      }
    }
  } else {
    console.log('Canvas not visible');
  }

  await page.screenshot({ path: 'm8n000380-after-signature.png' });
  console.log('Saved m8n000380-after-signature.png');

  await browser.close();
})();
