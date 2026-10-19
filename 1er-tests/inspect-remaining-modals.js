const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  for (const id of ['M8N000379', 'M8N000378', 'M8N000377']) {
    console.log(`\n=== Opening ${id} ===`);
    const searchInput = page.getByPlaceholder('Search Jobs...');
    await searchInput.fill(id);
    await page.waitForTimeout(1500);

    const row = page.locator('tr').filter({ hasText: id }).first();
    const eyeIcon = row.locator('.cursor-pointer').first();
    await eyeIcon.click();
    await page.waitForTimeout(2000);

    await page.screenshot({ path: `job-view-${id}.png` });
    console.log(`Saved job-view-${id}.png`);

    const fileInputs = await page.locator('input[type="file"]').all();
    console.log(`${id} file inputs count: ${fileInputs.length}`);

    // Close modal
    await page.locator('div[class*="drawer"] button, div[class*="drawer"] span, body').locator('text=×, [aria-label="Close"], button:has-text("Back")').first().click().catch(() => page.keyboard.press('Escape'));
    await page.waitForTimeout(1000);
    // Extra escape just in case
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);
  }

  await browser.close();
})();
