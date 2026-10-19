const { chromium } = require('playwright');

async function checkJobsList() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');
  await page.waitForTimeout(3000);

  // Read table rows
  const rows = await page.locator('table tbody tr').all();
  console.log(`Found ${rows.length} rows in Jobs table:`);
  for (let i = 0; i < Math.min(rows.length, 5); i++) {
    const text = (await rows[i].innerText()).replace(/\n+/g, ' | ');
    console.log(`Row ${i + 1}: ${text}`);
  }

  await browser.close();
}

checkJobsList().catch(console.error);
