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
  await page.waitForTimeout(3000);

  // Search or find M8N000380
  const searchInput = page.locator('input[placeholder*="Search"]').first();
  await searchInput.fill('M8N000380');
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'jobs-table-380.png', fullPage: true });

  // Click on the row or job number link to open modal
  const jobRow = page.locator('tr').filter({ hasText: 'M8N000380' }).first();
  console.log('Job row text:', await jobRow.innerText());

  // Click job number
  await jobRow.locator('td').nth(1).click();
  await page.waitForTimeout(3000);

  await page.screenshot({ path: 'job-380-modal-opened.png', fullPage: true });

  // Check buttons inside dialog/modal
  const modalButtons = await page.locator('[role="dialog"] button, .modal button').evaluateAll(btns => btns.map(b => ({
    text: b.innerText.trim(),
    visible: b.offsetWidth > 0,
    disabled: b.disabled,
    classes: b.className
  })));
  console.log('Modal buttons:', modalButtons);

  // Check modal text
  const modalText = await page.locator('[role="dialog"], .modal').first().innerText();
  console.log('Modal text content:');
  console.log(modalText);

  await browser.close();
})();
