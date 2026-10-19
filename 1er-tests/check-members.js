const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const installerId = '6a83ef63347d989cc5de4a3c';
  const roles = ['Plumber', 'Electrician', 'Refrigeration Mechanic'];

  for (const r of roles) {
    const res = await page.evaluate(async ({ id, role }) => {
      const resp = await fetch(`/api/v1/installers/${id}/members/by-role?role=${encodeURIComponent(role)}`);
      return await resp.json();
    }, { id: installerId, role: r });
    console.log(`Role ${r}:`, JSON.stringify(res));
  }

  // Also check all installer users
  const allUsers = await page.evaluate(async () => {
    const resp = await fetch('/api/v1/users?roleType=installer_user&limit=100');
    return await resp.json();
  });
  console.log('All installer users count:', allUsers.data?.total || allUsers.data?.users?.length);
  if (allUsers.data?.users) {
    console.log('Users sample:', allUsers.data.users.map(u => ({ name: `${u.firstName} ${u.lastName}`, roles: u.roles, company: u.installer?.companyName })));
  }

  await browser.close();
})();
