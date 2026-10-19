const { chromium } = require('playwright');

async function testCompleteCreation() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('/api/') && res.request().method() === 'POST') {
      console.log(`[API RESPONSE] ${res.status()} ${res.url()}`);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // 1. Own Reference
  const ownRef = `TEST-RJN-${Date.now()}`;
  await page.locator('input[name="ownReference"]').fill(ownRef);
  console.log(`1. Filled ownReference: ${ownRef}`);

  // 2. Activity Type
  const actSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Activity Type' }).first();
  await actSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: 'Heating & Cooling' }).first().click();
  await page.waitForTimeout(400);
  console.log('2. Selected Activity Type: Heating & Cooling');

  // 3. Lead Generation
  const leadSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Method of Lead Generation' }).first();
  await leadSelect.click();
  await page.locator('[class*="-option"]').first().click();
  await page.waitForTimeout(400);
  console.log('3. Selected Lead Gen');

  // 4. Building Type
  const bldgSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Building Type' }).first();
  await bldgSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: 'Residential Building' }).first().click();
  await page.waitForTimeout(400);
  console.log('4. Selected Building Type: Residential Building');

  // 5. Installer Company: Rajan Testing Company
  const compSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Installer (Company)' }).first();
  await compSelect.click();
  const compInput = page.locator('#react-select-8-input');
  await compInput.fill('Rajan');
  await page.waitForTimeout(500);
  await page.locator('[class*="-option"]').filter({ hasText: 'Rajan Testing Company' }).first().click();
  await page.waitForTimeout(500);
  console.log('5. Selected Company: Rajan Testing Company');

  // 6. Installer Person
  const personSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Installer Name' }).first();
  await personSelect.click();
  await page.waitForTimeout(400);
  const personOpts = await page.locator('[class*="-option"]').allInnerTexts();
  console.log('Installer Persons available:', personOpts);
  await page.locator('[class*="-option"]').first().click();
  await page.waitForTimeout(400);

  // 7. Customer Name
  await page.locator('input[name="customerName"]').fill('Olivia Nguyen');
  console.log('7. Filled Customer Name: Olivia Nguyen');

  // 8. Phone
  const phone = page.locator('input[name="phone"]');
  await phone.fill('+61412345678');
  console.log('8. Filled Customer Phone: +61412345678');

  // 9. Email
  await page.locator('input[name="email"]').fill('rajan.nsw.job1@yopmail.com');
  console.log('9. Filled Customer Email: rajan.nsw.job1@yopmail.com');

  // 10. Manual Address
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);
  await page.locator('input[name="customerAddress"]').fill('12 Macquarie St, Sydney NSW');
  await page.locator('input[name="postcode"]').fill('2000');
  console.log('10. Filled Address & Postcode: 12 Macquarie St, Sydney NSW 2000');

  // 11. Original Equipment
  const eqSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Original Equipment' }).first();
  if (await eqSelect.isVisible()) {
    await eqSelect.click();
    await page.waitForTimeout(400);
    const eqOpts = await page.locator('[class*="-option"]').allInnerTexts();
    console.log('Original Equipment options:', eqOpts);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 12. Brand
  const brandSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Brand' }).first();
  if (await brandSelect.isVisible()) {
    await brandSelect.click();
    await page.waitForTimeout(400);
    const brandOpts = await page.locator('[class*="-option"]').allInnerTexts();
    console.log('Brand options:', brandOpts);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 13. Model
  const modelSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Model' }).first();
  if (await modelSelect.isVisible()) {
    await modelSelect.click();
    await page.waitForTimeout(400);
    const modelOpts = await page.locator('[class*="-option"]').allInnerTexts();
    console.log('Model options:', modelOpts);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 14. Submit!
  console.log('Submitting form...');
  const submitBtn = page.locator('#submitButton');
  await submitBtn.click();
  await page.waitForTimeout(5000);

  console.log('URL after submit:', page.url());
  const toastText = await page.locator('.notification, .toast, [role="alert"]').allInnerTexts();
  console.log('Notification / Toast:', toastText);

  await page.screenshot({ path: 'job-creation-success.png' });
  console.log('Screenshot saved to job-creation-success.png');

  await browser.close();
}

testCompleteCreation().catch(console.error);
