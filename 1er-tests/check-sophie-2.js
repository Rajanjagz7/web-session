const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const users = await page.evaluate(async () => {
    const res = await fetch('/api/v1/users?roleType=user&search=Sophie');
    return await res.json();
  });
  console.log('Sophie user info:', JSON.stringify(users, null, 2));

  await browser.close();
})();
