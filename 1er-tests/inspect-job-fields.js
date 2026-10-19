const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobDetails = await page.evaluate(async () => {
    const res = await fetch('/api/v1/jobs/6ab2438c7c29b5bf7379e390');
    return await res.json();
  });

  console.log('Job details keys:', Object.keys(jobDetails.data.job));
  console.log('Status:', jobDetails.data.job.status);
  console.log('energyBill:', jobDetails.data.job.energyBill);
  console.log('files:', jobDetails.data.job.files);
  console.log('photos:', jobDetails.data.job.photos);
  console.log('siteAssessment:', jobDetails.data.job.siteAssessment);

  await browser.close();
})();
