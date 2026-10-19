const { chromium } = require('playwright');
const fs = require('fs');

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
  const actionCell = row.locator('td').nth(1);
  const cellHtml = await actionCell.innerHTML();
  console.log('Action cell HTML:', cellHtml);

  // Let's click the second icon (the document/file icon) first, or the first icon (the eye)
  const svgs = actionCell.locator('svg');
  const count = await svgs.count();
  console.log(`Action cell has ${count} svgs`);

  // Click the document icon (index 1)
  console.log('Clicking document icon (index 1)...');
  await svgs.nth(1).click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'after-click-doc-icon.png' });
  console.log('Saved after-click-doc-icon.png. URL:', page.url());

  // Check if a modal or drawer appeared
  const modalOrDrawer = await page.locator('[role="dialog"], .modal, .drawer, [class*="modal"], [class*="drawer"]').all();
  console.log(`Found ${modalOrDrawer.length} modal/drawer elements`);
  for (const m of modalOrDrawer) {
    const text = (await m.innerText().catch(() => '')).trim();
    console.log('Modal/drawer text sample:', text.substring(0, 150));
  }

  // Also click the eye icon (index 0) if nothing opened
  if (modalOrDrawer.length === 0 && page.url().endsWith('/jobs')) {
    console.log('Clicking eye icon (index 0)...');
    await svgs.nth(0).click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'after-click-eye-icon.png' });
    console.log('Saved after-click-eye-icon.png. URL:', page.url());
  }

  await browser.close();
})();
