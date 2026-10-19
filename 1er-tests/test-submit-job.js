const { chromium } = require('playwright');

async function testSubmitJob() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Own Reference
  const ownRef = page.locator('input[name="ownReference"], input[placeholder*="reference" i]').first();
  if (await ownRef.isVisible()) {
    await ownRef.fill('DRY-RUN-001');
  }

  // 1. Activity Type
  const input5 = page.locator('#react-select-5-input');
  await input5.focus();
  await page.locator('[class*="-control"]').first().click();
  await page.locator('[class*="-option"]').filter({ hasText: 'Heating & Cooling' }).first().click();
  await page.waitForTimeout(400);

  // 2. Lead Generation
  const leadControl = page.locator('[class*="-control"]').filter({ hasText: 'Select Method of Lead Generation' }).first();
  if (await leadControl.isVisible()) {
    await leadControl.click();
    await page.locator('[class*="-option"]').filter({ hasText: 'Customer initiated contact' }).first().click();
  }
  await page.waitForTimeout(400);

  // 3. Building Type
  const bldgControl = page.locator('[class*="-control"]').filter({ hasText: 'Select Building Type' }).first();
  if (await bldgControl.isVisible()) {
    await bldgControl.click();
    await page.locator('[class*="-option"]').filter({ hasText: 'Residential Building' }).first().click();
  }
  await page.waitForTimeout(400);

  // 4. Installer Company
  const compControl = page.locator('[class*="-control"]').filter({ hasText: 'Select Installer (Company)' }).first();
  if (await compControl.isVisible()) {
    await compControl.click();
    const compInput = page.locator('#react-select-8-input');
    await compInput.fill('Rajan Testing Company');
    await page.waitForTimeout(500);
    await page.locator('[class*="-option"]').filter({ hasText: 'Rajan Testing Company' }).first().click();
  }
  await page.waitForTimeout(400);

  // Let's dump all inputs in the form
  console.log('Inputs after selects:');
  const allInputs = await page.locator('form input, .dialog input, [role="dialog"] input').all();
  for (const inp of allInputs) {
    console.log(await inp.evaluate(el => ({
      name: el.name,
      placeholder: el.placeholder,
      type: el.type,
      id: el.id
    })));
  }

  // Customer Name
  const nameInput = page.locator('input[name="customerName"], input[placeholder*="name" i]').first();
  console.log('Customer name input visible:', await nameInput.isVisible());

  // Customer Phone
  const phoneInput = page.locator('input[type="tel"]').first();
  console.log('Phone input visible:', await phoneInput.isVisible());

  // Customer Email
  const emailInput = page.locator('input[name="customerEmail"], input[placeholder*="email" i], input[type="email"]').first();
  console.log('Email input visible:', await emailInput.isVisible());

  // Address
  const addrInput = page.locator('input[name="address"], input[placeholder*="address" i]').first();
  console.log('Address input visible:', await addrInput.isVisible());

  // Postcode
  const postcodeInput = page.locator('input[name="postcode"], input[placeholder*="postcode" i]').first();
  console.log('Postcode input visible:', await postcodeInput.isVisible());

  // Submit button
  const submitBtn = page.getByRole('button', { name: /send engagement letter/i });
  console.log('Submit button visible:', await submitBtn.isVisible());

  await browser.close();
}

testSubmitJob().catch(console.error);
