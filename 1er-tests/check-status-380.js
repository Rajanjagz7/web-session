const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const res = await page.evaluate(async () => {
    const r = await fetch('/api/v1/jobs?search=M8N000380');
    return await r.json();
  });
  const job = res.data?.jobs?.[0];
  console.log('M8N000380 current status:', job?.status);
  console.log('Job details:', {
    id: job?.id,
    jobNumber: job?.jobNumber,
    status: job?.status,
    customer: job?.customer?.name
  });

  // Also fetch details of this job
  if (job?.id) {
    const details = await page.evaluate(async (id) => {
      const r = await fetch(`/api/v1/jobs/${id}`);
      return await r.json();
    }, job.id);
    console.log('Job status from GET /jobs/:id:', details.data?.job?.status);
  }

  await browser.close();
})();
