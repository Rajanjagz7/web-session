const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobId = '6ab2438c7c29b5bf7379e390'; // M8N000380
  const jobRes = await page.evaluate(async (id) => {
    const r = await fetch(`/api/v1/jobs/${id}`);
    return await r.json();
  }, jobId);

  console.log('siteAssessorDeclaration:', JSON.stringify(jobRes.data.job.siteAssessorDeclaration, null, 2));
  console.log('team:', JSON.stringify(jobRes.data.job.team, null, 2));

  await browser.close();
})();
