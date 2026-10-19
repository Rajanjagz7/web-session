const { chromium } = require('playwright');

async function debugHeatPumpSubmit() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // 1. Reference
  await page.locator('input[name="ownReference"]').fill(`HWHP-${Date.now()}`);

  // 2. Activity Type: Hot Water Heat Pump
  const actSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Activity Type' }).first();
  await actSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: 'Hot Water Heat Pump' }).first().click();
  await page.waitForTimeout(400);

  // 3. Lead Gen
  const leadSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Method of Lead Generation' }).first();
  await leadSelect.click();
  await page.locator('[class*="-option"]').first().click();
  await page.waitForTimeout(400);

  // 4. Building Type: Residential
  const bldgSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Building Type' }).first();
  await bldgSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: 'Residential' }).first().click();
  await page.waitForTimeout(400);

  // 5. Installer Company
  const compSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Installer (Company)' }).first();
  await compSelect.click();
  const compInput = page.locator('#react-select-8-input');
  await compInput.fill('Rajan');
  await page.waitForTimeout(400);
  await page.locator('[class*="-option"]').filter({ hasText: 'Rajan Testing Company' }).first().click();
  await page.waitForTimeout(500);

  // 6. Installer Person
  const personSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Installer Name' }).first();
  if (await personSelect.isVisible()) {
    await personSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 7. Customer fields
  await page.locator('input[name="customerName"]').fill('Jack Wilson');
  await page.locator('input[name="phone"]').fill('+61423456789');
  await page.locator('input[name="email"]').fill('rajan.nsw.job2@yopmail.com');

  // 8. Address Switcher
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);
  await page.locator('input[name="customerAddress"]').fill('88 George St, The Rocks NSW');
  await page.locator('input[name="postcode"]').fill('2000');

  // 9. Hot Water Heat Pump - New System
  const newSysSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select New System' }).first();
  if (await newSysSelect.isVisible()) {
    await newSysSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 10. Check all placeholders visible now
  console.log('Placeholders visible before selecting equipment/brand/model:');
  console.log(await page.locator('.select__placeholder, [class*="-placeholder"]').allInnerTexts());

  // Let's see if Select Original Equipment is visible
  const eq = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Original Equipment' }).first();
  console.log('Select Original Equipment visible:', await eq.isVisible());
  if (await eq.isVisible()) {
    await eq.click();
    await page.waitForTimeout(400);
    const opts = await page.locator('[class*="-option"]').allInnerTexts();
    console.log('Original Equipment options for HWHP:', opts);
    if (opts.length > 0) {
      await page.locator('[class*="-option"]').first().click();
      await page.waitForTimeout(400);
    }
  }

  // Brand
  const br = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Brand' }).first();
  console.log('Select Brand visible:', await br.isVisible());
  if (await br.isVisible()) {
    await br.click();
    await page.waitForTimeout(400);
    const bOpts = await page.locator('[class*="-option"]').allInnerTexts();
    console.log('Brand options for HWHP:', bOpts.slice(0, 10));
    if (bOpts.length > 0) {
      await page.locator('[class*="-option"]').first().click();
      await page.waitForTimeout(400);
    }
  }

  // Model
  const mo = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Model' }).first();
  console.log('Select Model visible:', await mo.isVisible());
  if (await mo.isVisible()) {
    await mo.click();
    await page.waitForTimeout(400);
    const mOpts = await page.locator('[class*="-option"]').allInnerTexts();
    console.log('Model options for HWHP:', mOpts.slice(0, 10));
    if (mOpts.length > 0) {
      await page.locator('[class*="-option"]').first().click();
      await page.waitForTimeout(400);
    }
  }

  // Listen to response
  page.on('response', res => {
    if (res.url().includes('/api/v1/jobs')) {
      console.log(`[API RESPONSE HWHP] ${res.status()} ${res.url()}`);
    }
  });

  // Submit
  console.log('Submitting HWHP job...');
  await page.locator('#submitButton').click();
  await page.waitForTimeout(3000);

  // Check errors if any
  const errs = await page.locator('.text-red-500, .form-item-explain, [class*="errorMessage"]').allInnerTexts();
  console.log('Errors if any:', errs);

  await browser.close();
}

debugHeatPumpSubmit().catch(console.error);
