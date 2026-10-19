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

  const drawer = page.locator('.drawer-content, [role="dialog"]').first();

  // Look for step 2 button or text
  const step2 = drawer.locator('text=Site Assessment & Nomination').first();
  console.log('Clicking Step 2...');
  await step2.click({ force: true });
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'm8n000380-step2-content.png' });
  console.log('Saved m8n000380-step2-content.png');

  // Let's also check all clickable tabs or headers in drawer
  const tabs = await drawer.locator('button, [role="tab"], .step, [class*="step"]').all();
  console.log(`Found ${tabs.length} step/tab elements`);
  for (const t of tabs) {
    console.log('Tab/step text:', (await t.innerText().catch(() => '')).trim());
  }

  // Also check if there's any file input in the drawer right now
  const fileInputs = await drawer.locator('input[type="file"]').all();
  console.log(`Drawer has ${fileInputs.length} file inputs`);

  await browser.close();
})();
