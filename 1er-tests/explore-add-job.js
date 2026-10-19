const { chromium } = require('playwright');

async function explore() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');
  console.log('Logged in successfully!');

  // Click Add Job button
  const addJobBtn = page.getByRole('button', { name: 'Add Job' });
  await addJobBtn.waitFor({ state: 'visible' });
  await addJobBtn.click();
  await page.waitForTimeout(2000);

  console.log('--- Step 1: Add Job Modal Opened ---');
  const dialog = page.locator('[role="dialog"]');
  console.log('Dialog visible:', await dialog.isVisible());

  // Dump all labels, inputs, selects in dialog
  const formLabels = await dialog.locator('label').allInnerTexts();
  console.log('Labels found:', formLabels);

  // Let's inspect all react-select or custom select elements
  const selects = await dialog.locator('.select, [class*="control"], [id^="react-select"]').all();
  console.log('Found select-like elements:', selects.length);

  // Check installer dropdown options
  console.log('Looking for Company / Installer dropdown...');
  // Let's find inputs or dropdown triggers
  const textContent = await dialog.innerText();
  console.log('--- Modal Text Content ---');
  console.log(textContent);

  await browser.close();
}

explore().catch(console.error);
