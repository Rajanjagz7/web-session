const { chromium } = require('playwright');

async function testAddressField() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Check the switcher "Add Manual Address"
  const switcher = page.locator('label.switcher input[type="checkbox"]');
  console.log('Switcher found:', await switcher.count());
  await switcher.click();
  await page.waitForTimeout(500);

  // See what inputs appear
  const addressInputs = await page.locator('input[name*="address" i], input[placeholder*="address" i], textarea[name*="address" i]').all();
  console.log('Address inputs after toggling manual address:');
  for (const inp of addressInputs) {
    console.log(await inp.evaluate(el => ({ name: el.name, placeholder: el.placeholder, type: el.type, visible: el.offsetParent !== null })));
  }

  await browser.close();
}

testAddressField().catch(console.error);
