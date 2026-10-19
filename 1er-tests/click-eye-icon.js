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
  console.log('Clicking eye icon...');
  await eyeIcon.click();
  await page.waitForTimeout(3000);

  console.log('URL after clicking eye icon:', page.url());
  await page.screenshot({ path: 'after-click-eye-view.png' });

  // Let's dump all headings, tabs, dialogs or buttons on the screen now
  const headings = await page.locator('h1, h2, h3, h4, h5, [role="heading"]').allInnerTexts();
  console.log('Headings:', headings);

  const tabs = await page.locator('[role="tab"], .tab, button[class*="tab"]').allInnerTexts();
  console.log('Tabs:', tabs);

  const buttons = await page.locator('button').allInnerTexts();
  console.log('Buttons:', buttons.filter(b => b.trim().length > 0));

  await browser.close();
})();
