const { chromium } = require('playwright');

async function testLogin(identifier) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://nswdev.rebatem8.com.au/sign-in', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  console.log(`Testing login with: ${identifier}`);
  const input = page.locator('input[name="emailMobile"]');
  await input.fill(identifier);
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForTimeout(3000);

  console.log('URL:', page.url());
  console.log('Page text:');
  console.log(await page.locator('body').innerText());
  await browser.close();
}

testLogin(process.argv[2] || 'johns@softwareco.com').catch(console.error);
