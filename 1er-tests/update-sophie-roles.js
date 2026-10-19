const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const userId = '6aaa4574bdeb55ed054cd80a';
  const installerId = '6a83ef63347d989cc5de4a3c';

  // Let's test updating Sophie's company roles
  const res = await page.evaluate(async ({ uid, iid }) => {
    // Check if PUT /api/v1/users/:id works
    const r = await fetch(`/api/v1/users/${uid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        companies: [
          {
            installerId: iid,
            roles: ['Electrician', 'Refrigeration Mechanic'],
            accessType: 'Admin',
            isActive: true,
            signOffResponsibilities: ['Installation sign-off', 'Electrical sign-off']
          }
        ]
      })
    });
    return { status: r.status, text: await r.text() };
  }, { uid: userId, iid: installerId });

  console.log('Update result:', res);

  // Now check by-role again
  const checkRefrig = await page.evaluate(async (iid) => {
    const r = await fetch(`/api/v1/installers/${iid}/members/by-role?role=${encodeURIComponent('Refrigeration Mechanic')}`);
    return await r.json();
  }, installerId);
  console.log('Refrigeration Mechanic members now:', JSON.stringify(checkRefrig));

  await browser.close();
})();
