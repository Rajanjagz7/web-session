const { chromium } = require('playwright');

async function testTargetedSelect() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('/api/v1/jobs') && res.request().method() === 'POST') {
      console.log(`[API RESPONSE SUCCESS] ${res.status()} ${res.url()}`);
    }
  });
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Helper for label-based react-select
  async function selectByLabel(labelText, optionText, searchText = '') {
    const item = page.locator('.form-item').filter({ hasText: labelText }).first();
    await item.locator('.select__control').click();
    await page.waitForTimeout(300);
    if (searchText) {
      const inp = item.locator('input.select__input');
      await inp.fill(searchText);
      await page.waitForTimeout(400);
    }
    const opt = page.locator('[class*="-option"]').filter({ hasText: optionText }).first();
    await opt.waitFor({ state: 'visible', timeout: 5000 });
    await opt.click();
    await page.waitForTimeout(400);
    console.log(`Selected "${optionText}" for [${labelText}]`);
  }

  // 1. Reference
  await page.locator('input[name="ownReference"]').fill(`HWHP-RES-${Date.now()}`);

  // 2. Activity Type
  await selectByLabel('Activity Type', 'Hot Water Heat Pump');

  // 3. Lead Gen
  await selectByLabel('Method of Lead Generation', 'Online advertisement');

  // 4. Building Type
  await selectByLabel('Building Type', 'Residential Building');

  // 5. Installer Company
  await selectByLabel('Installer (Company)', 'Rajan Testing Company', 'Rajan');

  // 6. Installer Person
  await selectByLabel('Name of Installer Attended', 'Rajan Jagwani');

  // 7. Customer
  await page.locator('input[name="customerName"]').fill('Jack Wilson');
  await page.locator('input[name="phone"]').fill('+61423456789');
  await page.locator('input[name="email"]').fill('rajan.nsw.job2@yopmail.com');

  // 8. Address
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);
  await page.locator('input[name="customerAddress"]').fill('88 George St, The Rocks NSW');
  await page.locator('input[name="postcode"]').fill('2000');

  // 9. Equipment
  await selectByLabel('Original Equipment', 'Electric Hot Water Unit');

  // 10. Brand
  await selectByLabel('Brand', 'AGM Energy');

  // 11. Model
  await selectByLabel('Model', 'AGMHP270W');

  // 12. Submit
  console.log('Submitting HWHP Job 2...');
  await page.locator('#submitButton').click();
  await page.waitForTimeout(5000);

  // Check top rows
  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  const rows = await page.locator('table tbody tr').all();
  console.log(`\n=== Jobs Table (Top 3) ===`);
  for (let i = 0; i < Math.min(rows.length, 3); i++) {
    const text = (await rows[i].innerText()).replace(/\n+/g, ' | ');
    console.log(`Row ${i + 1}: ${text}`);
  }

  await browser.close();
}

testTargetedSelect().catch(console.error);
