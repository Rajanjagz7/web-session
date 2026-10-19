const { chromium } = require('playwright');

async function testLogin(email, password) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1000);
  
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForTimeout(3000);

  console.log('After login URL:', page.url());
  console.log('Page text snippet:', (await page.locator('body').innerText()).substring(0, 300));
  await browser.close();
}

testLogin(process.argv[2] || 'johns@softwareco.com', process.argv[3] || 'admin@123').catch(console.error);
