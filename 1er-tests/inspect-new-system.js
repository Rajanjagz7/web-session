const { chromium } = require('playwright');

async function inspectNewSystem() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Activity Type: Hot Water Heat Pump
  const actSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Activity Type' }).first();
  await actSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: 'Hot Water Heat Pump' }).first().click();
  await page.waitForTimeout(400);

  // Lead Gen
  const leadSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Method of Lead Generation' }).first();
  await leadSelect.click();
  await page.locator('[class*="-option"]').first().click();
  await page.waitForTimeout(400);

  // Building Type: Residential
  const bldgSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Building Type' }).first();
  await bldgSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: 'Residential Building' }).first().click();
  await page.waitForTimeout(400);

  // Installer
  const compSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Installer (Company)' }).first();
  await compSelect.click();
  const compInput = page.locator('#react-select-8-input');
  await compInput.fill('Rajan');
  await page.waitForTimeout(400);
  await page.locator('[class*="-option"]').filter({ hasText: 'Rajan Testing Company' }).first().click();
  await page.waitForTimeout(500);

  // Click Select New System
  const sysSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select New System' }).first();
  await sysSelect.click();
  await page.waitForTimeout(400);
  const sysOptions = await page.locator('[class*="-option"]').allInnerTexts();
  console.log('New System Options:', sysOptions);

  if (sysOptions.length > 0) {
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(500);
  }

  // After selecting New System, what placeholders are visible?
  console.log('Placeholders after selecting New System:');
  console.log(await page.locator('.select__placeholder, [class*="-placeholder"]').allInnerTexts());

  await browser.close();
}

inspectNewSystem().catch(console.error);
