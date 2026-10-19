const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');
  await page.waitForTimeout(2000);

  const searchInput = page.getByPlaceholder('Search Jobs...');
  await searchInput.fill('M8N000380');
  await page.waitForTimeout(1500);

  const row = page.locator('tr').filter({ hasText: 'M8N000380' }).first();
  const eyeIcon = row.locator('.cursor-pointer').first();
  await eyeIcon.click();
  await page.waitForTimeout(3000);

  await page.screenshot({ path: 'job-380-drawer-opened.png' });

  // Get all text and buttons inside drawer
  const drawer = page.locator('.drawer-content, [role="dialog"], .drawer').first();
  const drawerText = await drawer.innerText();
  console.log('Drawer text:');
  console.log(drawerText);

  // Check all buttons
  const buttons = await drawer.locator('button').evaluateAll(btns => btns.map(b => ({
    text: b.innerText.trim(),
    disabled: b.disabled,
    visible: b.offsetWidth > 0
  })));
  console.log('Drawer buttons:', buttons);

  await browser.close();
})();
