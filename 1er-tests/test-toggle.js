const { chromium } = require('playwright');

async function testAddress() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Click .switcher-toggle
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(500);

  console.log('After clicking .switcher-toggle:');
  const allInputs = await page.locator('input:visible, textarea:visible').all();
  for (const inp of allInputs) {
    console.log(await inp.evaluate(el => ({ name: el.name, placeholder: el.placeholder, type: el.type, id: el.id })));
  }

  await browser.close();
}

testAddress().catch(console.error);
