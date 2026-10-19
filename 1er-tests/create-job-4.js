const { chromium } = require('playwright');

async function createJob4() {
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
    await opt.waitFor({ state: 'visible', timeout: 6000 });
    await opt.click();
    await page.waitForTimeout(400);
    console.log(`Selected "${optionText}" for [${labelText}]`);
  }

  // Reference
  await page.locator('input[name="ownReference"]').fill(`RJN-HWHP-SMB-${Date.now().toString().slice(-4)}`);

  // Activity Type
  await selectByLabel('Activity Type', 'Hot Water Heat Pump');

  // Lead Gen
  await selectByLabel('Method of Lead Generation', 'Email campaign');

  // Building Type
  await selectByLabel('Building Type', 'Small Business');

  // Installer Company
  await selectByLabel('Installer', 'Rajan Testing Company', 'Rajan');

  // Installer Person
  await selectByLabel('Attended', 'Rajan Jagwani');

  // Business fields
  await page.locator('input[name="businessName"]').fill('Coastal Enterprises NSW Pty Ltd');
  await page.locator('input[name="authFirstName"]').fill('Noah');
  await page.locator('input[name="authLastName"]').fill('Collins');
  await page.locator('input[name="authSignPosition"]').fill('General Manager');
  await page.locator('input[name="authPhoneNumber"]').fill('+61458901234');
  await page.locator('input[name="authEmail"]').fill('rajan.nsw.job4@yopmail.com');
  await page.locator('input[name="abnAcn"]').fill('33102417032');

  // Address
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);
  await page.locator('input[name="customerAddress"]').fill('15 Crown St, Wollongong NSW');
  await page.locator('input[name="postcode"]').fill('2500');

  // Check if New System is visible
  const newSys = page.locator('.form-item').filter({ hasText: 'New System' }).first();
  if (await newSys.isVisible()) {
    await selectByLabel('New System', 'Heat pump');
  }

  // Original Equipment
  await selectByLabel('Original Equipment', 'Electric Hot Water Unit');

  // Brand
  const brandItem = page.locator('.form-item').filter({ hasText: 'Brand' }).first();
  await brandItem.locator('.select__control').click();
  await page.waitForTimeout(400);
  const firstBrand = page.locator('[class*="-option"]').first();
  await firstBrand.waitFor({ state: 'visible', timeout: 6000 });
  const brandName = await firstBrand.innerText();
  await firstBrand.click();
  console.log(`Selected Brand: ${brandName}`);
  await page.waitForTimeout(400);

  // Model
  const modelItem = page.locator('.form-item').filter({ hasText: 'Model' }).first();
  await modelItem.locator('.select__control').click();
  await page.waitForTimeout(400);
  const firstModel = page.locator('[class*="-option"]').first();
  await firstModel.waitFor({ state: 'visible', timeout: 6000 });
  const modelName = await firstModel.innerText();
  await firstModel.click();
  console.log(`Selected Model: ${modelName}`);
  await page.waitForTimeout(400);

  // Submit
  console.log('Submitting Job 4...');
  await page.locator('#submitButton').click();
  await page.waitForTimeout(5000);

  await page.screenshot({ path: 'screenshots/job_4.png' });
  console.log('Saved screenshots/job_4.png');

  // Verify in table
  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  const rows = await page.locator('table tbody tr').all();
  console.log(`\n=== Current Jobs Table (Top 5) ===`);
  for (let i = 0; i < Math.min(rows.length, 5); i++) {
    const text = (await rows[i].innerText()).replace(/\n+/g, ' | ');
    console.log(`Row ${i + 1}: ${text}`);
  }

  await browser.close();
}

createJob4().catch(console.error);
