const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  let authToken = '';
  page.on('response', async res => {
    if (res.url().includes('/api/v1/auth/admin/login')) {
      const data = await res.json().catch(() => ({}));
      authToken = data.token || (data.data && data.data.token) || '';
      console.log('Got auth token length:', authToken.length);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  // Let's get the token from localStorage if not caught
  const storage = await page.evaluate(() => JSON.stringify(localStorage));
  console.log('LocalStorage keys:', Object.keys(JSON.parse(storage)));

  const token = await page.evaluate(() => {
    const raw = localStorage.getItem('token') || localStorage.getItem('auth') || localStorage.getItem('user');
    return {
      token: localStorage.getItem('token'),
      adminToken: localStorage.getItem('adminToken'),
      session: localStorage.getItem('session'),
      raw
    };
  });
  console.log('Tokens found:', token);

  // Let's inspect job M8N000380 via page.request or fetch in browser
  const jobInfo = await page.evaluate(async () => {
    const res = await fetch('/api/v1/jobs?search=M8N000380');
    return await res.json();
  });
  console.log('Job search result:', JSON.stringify(jobInfo, null, 2));

  const job = jobInfo.data && jobInfo.data.jobs && jobInfo.data.jobs[0];
  if (job) {
    const jobId = job._id || job.id;
    console.log('Target Job ID:', jobId);

    const jobDocs = await page.evaluate(async (id) => {
      const res = await fetch(`/api/v1/jobs/${id}/documents`);
      return await res.json();
    }, jobId);
    console.log('Job Documents:', JSON.stringify(jobDocs, null, 2));

    const jobDetails = await page.evaluate(async (id) => {
      const res = await fetch(`/api/v1/jobs/${id}`);
      return await res.json();
    }, jobId);
    console.log('Job Details Keys:', Object.keys(jobDetails.data || {}));
    if (jobDetails.data) {
      console.log('Job status:', jobDetails.data.status);
      console.log('Job activityType:', jobDetails.data.activityType);
      console.log('Job buildingType:', jobDetails.data.buildingType);
      console.log('Job files/documents/images in data:', {
        files: jobDetails.data.files,
        documents: jobDetails.data.documents,
        photos: jobDetails.data.photos,
        attachments: jobDetails.data.attachments,
        energyBill: jobDetails.data.energyBill
      });
    }
  }

  await browser.close();
})();
