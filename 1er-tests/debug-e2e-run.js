const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('/api/v1/jobs') && res.request().method() === 'POST') {
      console.log(`[API RESPONSE SUCCESS] ${res.status()} ${res.url()}`);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Helper
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
    await opt.waitFor({ state: 'visible', timeout: 8000 });
    await opt.click();
    await page.waitForTimeout(300);
    console.log(`Selected "${optionText}" for [${labelText}]`);
  }

  // Reference
  await page.locator('input[name="ownReference"]').fill(`DEBUG-E2E-${Date.now()}`);

  // Activity Type
  await selectByLabel('Activity Type', 'Heating & Cooling');

  // Lead Gen
  await selectByLabel('Method of Lead Generation', 'Customer initiated contact');

  // Building Type
  await selectByLabel('Building Type', 'Residential');

  // Installer
  await selectByLabel('Installer', 'Rajan Testing Company', 'Rajan');

  // Installer Person
  const personItem = page.locator('.form-item').filter({ hasText: 'Attended' }).first();
  if (await personItem.isVisible({ timeout: 2000 }).catch(() => false)) {
    await personItem.locator('.select__control').click();
    await page.waitForTimeout(300);
    const firstOpt = page.locator('[class*="-option"]').first();
    await firstOpt.click();
    console.log('Selected Installer Person');
  }

  // Customer Name
  await page.locator('input[name="customerName"]').fill('Olivia Nguyen');

  // Phone: 9 digits for AU
  const phoneInp = page.locator('input[name="phone"]');
  await phoneInp.fill('412345678');
  console.log('Filled phone: 412345678');

  // Customer Email
  await page.locator('input[name="email"]').fill(`rajan.test.${Date.now()}@yopmail.com`);

  // Address
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);
  await page.locator('input[name="customerAddress"]').fill('12 Macquarie St, Sydney NSW');
  await page.locator('input[name="postcode"]').fill('2000');

  // Equipment to Be Quoted
  console.log('Selecting Original Equipment...');
  const eqItem = page.locator('.form-item').filter({ hasText: 'Original Equipment' }).first();
  await eqItem.locator('.select__control').click();
  await page.waitForTimeout(400);
  await page.locator('[class*="-option"]').first().click();
  await page.waitForTimeout(500);

  // Brand
  console.log('Selecting Brand...');
  const brandItem = page.locator('.form-item').filter({ hasText: 'Brand' }).first();
  await brandItem.locator('.select__control').click();
  await page.waitForTimeout(400);
  await page.locator('[class*="-option"]').first().click();
  await page.waitForTimeout(500);

  // Model
  console.log('Selecting Model...');
  const modelItem = page.locator('.form-item').filter({ hasText: 'Model' }).first();
  await modelItem.locator('.select__control').click();
  await page.waitForTimeout(400);
  await page.locator('[class*="-option"]').first().click();
  await page.waitForTimeout(500);

  console.log('Clicking #submitButton...');
  const [response] = await Promise.all([
    page.waitForResponse(res => res.url().includes('/api/v1/jobs') && res.request().method() === 'POST', { timeout: 15000 }),
    page.locator('#submitButton').click()
  ]);

  console.log('Got response status:', response.status());
  const body = await response.json();
  console.log('Job ID created:', body?.data?.jobId || body?.jobId || body);

  await browser.close();
})();
