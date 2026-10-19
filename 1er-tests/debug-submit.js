const { chromium } = require('playwright');

async function debugSubmit() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Listen to all console logs
  page.on('console', msg => console.log(`[BROWSER CONSOLE] ${msg.type()}: ${msg.text()}`));
  
  // Listen to all requests
  page.on('request', req => {
    if (req.method() !== 'GET') {
      console.log(`[BROWSER REQ] ${req.method()} ${req.url()}`);
      console.log('Post data:', req.postData());
    }
  });

  page.on('response', res => {
    if (res.request().method() !== 'GET') {
      console.log(`[BROWSER RES] ${res.status()} ${res.url()}`);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Own reference
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
  await phone.fill('');
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

  // Check hidden inputs
  console.log('--- Hidden input values ---');
  const hiddenInputs = await page.locator('input[type="hidden"]').all();
  for (const h of hiddenInputs) {
    console.log(await h.evaluate(el => ({ name: el.name, value: el.value })));
  }

  console.log('Clicking Submit button...');
  await page.locator('#submitButton').click();
  await page.waitForTimeout(4000);

  console.log('Finished debug test.');
  await browser.close();
}

debugSubmit().catch(console.error);
