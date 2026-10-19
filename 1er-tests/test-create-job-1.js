const { chromium } = require('playwright');

async function testCreateJob() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  console.log('Opening Add Job modal...');
  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // 1. Own Reference
  const ref = `TEST-RJN-${Date.now()}`;
  console.log(`Setting ownReference: ${ref}`);
  await page.locator('input[name="ownReference"]').fill(ref);

  // 2. Activity Type: Heating & Cooling
  console.log('Selecting Activity Type...');
  const input5 = page.locator('#react-select-5-input');
  await input5.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(400);

  // 3. Method of Lead Gen: Customer initiated contact
  console.log('Selecting Method of Lead Gen...');
  const input6 = page.locator('#react-select-6-input');
  await input6.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(400);

  // 4. Building Type: Residential Building
  console.log('Selecting Building Type...');
  const input7 = page.locator('#react-select-7-input');
  await input7.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(400);

  // 5. Installer Company: Rajan Testing Company
  console.log('Selecting Installer (Rajan Testing Company)...');
  const input8 = page.locator('#react-select-8-input');
  await input8.focus();
  await input8.fill('Rajan Testing Company');
  await page.waitForTimeout(400);
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(400);

  // 6. Customer Name
  await page.locator('input[name="customerName"]').fill('Olivia Nguyen');

  // 7. Customer Phone (AU mobile)
  const phone = page.locator('input[name="phone"]');
  await phone.focus();
  await phone.fill('+61412345678');

  // 8. Customer Email (yopmail)
  await page.locator('input[name="email"]').fill('rajan.nsw.job1@yopmail.com');

  // 9. Manual Address switcher
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(400);

  // 10. Address & Postcode
  await page.locator('input[name="customerAddress"]').fill('12 Macquarie St, Sydney NSW');
  await page.locator('input[name="postcode"]').fill('2000');

  // Listen to network responses
  page.on('response', res => {
    if (res.url().includes('job') || res.status() >= 400) {
      console.log(`[API Response] ${res.status()} ${res.url()}`);
    }
  });

  // 11. Click Submit
  console.log('Clicking submit button...');
  const submitBtn = page.locator('#submitButton');
  await submitBtn.click();
  await page.waitForTimeout(4000);

  console.log('URL after submit:', page.url());
  const toasts = await page.locator('.notification, .toast, [role="alert"]').allInnerTexts();
  console.log('Toasts/Alerts:', toasts);

  // Take screenshot
  await page.screenshot({ path: 'after-create-job-1.png' });
  console.log('Screenshot saved to after-create-job-1.png');

  await browser.close();
}

testCreateJob().catch(console.error);
