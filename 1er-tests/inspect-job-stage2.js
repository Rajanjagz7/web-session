const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

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
  await page.waitForTimeout(2500);

  await page.screenshot({ path: 'm8n000380-stage2.png' });
  console.log('Saved m8n000380-stage2.png');

  // Also check the second icon (the document/paper icon) in the row to see if it's now enabled!
  // Close the drawer first
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1000);

  const actionCell = row.locator('td').nth(1);
  const svgs = actionCell.locator('svg');
  console.log('Action cell svgs count:', await svgs.count());
  await svgs.nth(1).click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'm8n000380-doc-icon-click.png' });
  console.log('Saved m8n000380-doc-icon-click.png. URL:', page.url());

  await browser.close();
})();
