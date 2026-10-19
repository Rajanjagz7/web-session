const { chromium } = require('playwright');

async function checkFormErrors() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Fill everything as before
  await page.locator('input[name="ownReference"]').fill('REF-AUTO-001');

  // Activity Type
  const input5 = page.locator('#react-select-5-input');
  await input5.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);

  // Lead Gen
  const input6 = page.locator('#react-select-6-input');
  await input6.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);

  // Building Type
  const input7 = page.locator('#react-select-7-input');
  await input7.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);

  // Installer
  const input8 = page.locator('#react-select-8-input');
  await input8.focus();
  await input8.fill('Rajan');
  await page.waitForTimeout(500);
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);

  // Customer Name
  await page.locator('input[name="customerName"]').fill('Olivia Nguyen');

  // Customer Phone
  const phone = page.locator('input[name="phone"]');
  await phone.fill('+61412345678');

  // Customer Email
  await page.locator('input[name="email"]').fill('rajan.nsw.job1@yopmail.com');

  // Toggle manual address
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);

  // Address
  await page.locator('input[name="customerAddress"]').fill('12 Macquarie St, Sydney NSW');

  // Postcode
  await page.locator('input[name="postcode"]').fill('2000');

  // Let's click submit
  await page.locator('#submitButton').click();
  await page.waitForTimeout(1500);

  // Inspect any text elements that appeared
  const errorElements = await page.locator('.text-red-500, .form-item-explain, .error, [class*="text-red"]').all();
  console.log(`Found ${errorElements.length} red/error elements:`);
  for (const el of errorElements) {
    const txt = await el.innerText();
    const parent = await el.locator('xpath=..').innerText().catch(() => '');
    console.log(`Error element: "${txt}" | Parent: "${parent.replace(/\n+/g, ' ')}"`);
  }

  await page.screenshot({ path: 'form-validation-screenshot.png', fullPage: true });
  console.log('Saved form-validation-screenshot.png');

  await browser.close();
}

checkFormErrors().catch(console.error);
