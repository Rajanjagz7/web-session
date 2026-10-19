const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobs = ['M8N000380', 'M8N000379', 'M8N000378', 'M8N000377'];
  const results = [];

  for (const j of jobs) {
    const data = await page.evaluate(async (jobNum) => {
      const res = await fetch(`/api/v1/jobs?search=${jobNum}`);
      const json = await res.json();
      const job = json.data?.jobs?.[0];
      return {
        jobNumber: job?.jobNumber,
        id: job?.id || job?._id,
        status: job?.status,
        customerName: job?.customer?.name,
        companyName: job?.installer?.companyName,
        activityType: job?.activityType
      };
    }, j);
    results.push(data);
  }

  console.log('Target jobs details:', JSON.stringify(results, null, 2));
  await browser.close();
})();
