const { chromium } = require('playwright');

async function controlForLabel(page, labelText) {
  const label = page.getByText(labelText, { exact: false }).first();
  const wrapper = label.locator('xpath=ancestor::*[.//*[contains(@class,"select__control")]][1]');
  return wrapper.locator('.select__control').first();
}

async function fillDateByPlaceholder(page, placeholder, value) {
  const field = page.getByPlaceholder(placeholder, { exact: true }).first();
  const current = await field.inputValue().catch(() => '');
  if (current) {
    console.log(`  (skip) "${placeholder}" already has value "${current}"`);
    return;
  }
  await field.click();
  await page.keyboard.type(value);
  console.log(`  Filled "${placeholder}" -> ${value}`);
  await page.waitForTimeout(300);
}

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 200 });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  console.log('=== STEP 1: Log in and open Installer Users ===');
  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.getByPlaceholder(/email/i).fill('admin@rebatem8nsw.com.au');
  await page.getByPlaceholder(/password/i).fill('admin@123');
  await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
  await page.waitForTimeout(2000);

  await page.goto('https://nswdev.rebatem8.com.au/installeruser');
  await page.waitForTimeout(2000);
  await page.getByPlaceholder(/search/i).first().fill('jasonjohn@yopmail.com');
  await page.waitForTimeout(2000);

  console.log('=== STEP 2: Open Edit User for Jason John ===');
  const row = page.locator('table tbody tr').first();
  await row.locator('td').last().locator('svg, button, img').first().click();
  await page.waitForTimeout(2000);
  await page.getByText('Edit User', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });

  console.log('=== STEP 3: Add roles - Manager, Business Director, Electrician, Refrigeration Mechanic, Other (Plumber already selected) ===');
  const roleControl = await controlForLabel(page, 'Role');
  for (const roleName of ['Manager', 'Business Director', 'Electrician', 'Refrigeration Mechanic', 'Other']) {
    await roleControl.scrollIntoViewIfNeeded();
    await roleControl.click();
    await page.waitForTimeout(500);
    const option = page.getByRole('option', { name: roleName, exact: true });
    if (await option.count()) {
      await option.click();
      console.log(`  + Added role: ${roleName}`);
      await page.waitForTimeout(500);
    }
  }
  await page.waitForTimeout(1000);

  console.log('=== STEP 4: Fill the new Electrician licence sub-section ===');
  await page.getByPlaceholder('Enter NSW Electrical Licence Number', { exact: true }).fill('ELEC-' + Date.now().toString().slice(-8));
  await fillDateByPlaceholder(page, 'Select Electrician Qualification / Licence Completion Date', '01-06-2022');
  await fillDateByPlaceholder(page, 'Select Electrician Licence Expiry Date', '30-08-2027');

  console.log('=== STEP 5: Fill the new Refrigeration Mechanic licence sub-section ===');
  await page.getByPlaceholder('Enter NSW Air Conditioning and Refrigeration Licence Number', { exact: true }).fill('ARC-' + Date.now().toString().slice(-8));
  await fillDateByPlaceholder(page, 'Select Refrigeration Mechanic Qualification / Licence Completion Date', '01-06-2022');
  await fillDateByPlaceholder(page, 'Select Refrigeration Mechanic  Licence Expiry Date', '30-08-2027');

  await page.getByPlaceholder('Enter ARCtick Refrigerant Handling Licence Number', { exact: true }).fill('ARCTICK-' + Date.now().toString().slice(-6));
  const arcClassControl = await controlForLabel(page, 'ARCtick Refrigerant Handling Licence Number Class');
  await arcClassControl.scrollIntoViewIfNeeded();
  await arcClassControl.click();
  await page.waitForTimeout(400);
  await page.getByRole('option').first().click();
  console.log('  ARCtick number + class filled.');
  await page.waitForTimeout(400);
  await fillDateByPlaceholder(page, 'Select ARCtick Qualification / Licence Completion Date', '01-06-2022');
  await fillDateByPlaceholder(page, 'Select ARCtick Licence Expiry Date', '30-08-2027');

  console.log('=== STEP 6: Check Agreement Commencement Date / Responsibility for sign-off ===');
  await fillDateByPlaceholder(page, 'Select Commencement Date', '01-01-2024');

  console.log('=== STEP 7: Screenshot right before Save ===');
  await page.screenshot({ path: 'jasonjohn-before-save.png', fullPage: true });

  console.log('=== STEP 8: Click Save and capture the outcome ===');
  const fired = [];
  page.on('request', (req) => {
    if (['POST', 'PUT', 'PATCH'].includes(req.method())) fired.push(`${req.method()} ${req.url()}`);
  });

  await page.getByRole('button', { name: /^save$/i }).first().click();
  await page.waitForTimeout(3000);

  console.log('Requests fired on Save:', JSON.stringify(fired, null, 2));
  const stillOpen = await page.getByText('Edit User', { exact: true }).isVisible().catch(() => false);
  console.log('Edit User drawer still open after Save:', stillOpen);
  if (stillOpen) {
    const errorTexts = await page.locator('text=/required|invalid|must be/i').allTextContents().catch(() => []);
    console.log('Visible validation messages:', JSON.stringify(errorTexts));
    await page.screenshot({ path: 'jasonjohn-validation-errors.png', fullPage: true });
  } else {
    console.log('SUCCESS: drawer closed, Save appears to have succeeded.');
  }
  await page.screenshot({ path: 'jasonjohn-after-save.png', fullPage: true });

  console.log('\nLeaving browser open 15s to inspect.');
  await page.waitForTimeout(15000);
  await browser.close();
})();
