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

  console.log('Full Job Details Keys:', Object.keys(jobRes.data.job));
  console.log('Engagement object:', JSON.stringify(jobRes.data.job.engagement, null, 2));
  console.log('SiteAssessment object:', JSON.stringify(jobRes.data.job.siteAssessment, null, 2));
  console.log('Nomination object:', JSON.stringify(jobRes.data.job.nomination, null, 2));
  console.log('Public links / tokens in job:', {
    token: jobRes.data.job.token,
    publicToken: jobRes.data.job.publicToken,
    siteAssessorToken: jobRes.data.job.siteAssessorToken,
    declarationToken: jobRes.data.job.declarationToken,
    nominationToken: jobRes.data.job.nominationToken,
    signatureToken: jobRes.data.job.signatureToken
  });

  // Let's also check documents
  const docsRes = await page.evaluate(async (id) => {
    const r = await fetch(`/api/v1/jobs/${id}/documents`);
    return await r.json();
  }, jobId);
  console.log('Documents for job:', JSON.stringify(docsRes, null, 2));

  await browser.close();
})();
