const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 400 });
  const page = await browser.newPage({ viewport: null, args: ['--start-maximized'] });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.getByPlaceholder(/email/i).fill('admin@rebatem8nsw.com.au');
  await page.getByPlaceholder(/password/i).fill('admin@123');
  await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
  await page.waitForTimeout(2000);

  const runId = Date.now().toString().slice(-8);
  const ownReference = 'REF-NOMAND-' + runId;

  console.log('\n=== STEP 1: Create a job via a direct API call, sending ONLY what the backend schema requires ===');
  console.log('Deliberately omitting: address, postcode, buildingType, methodOfLeadGeneration, installationDate, ABN, products - all shown with a red * on the Add Job form.');
  const resp = await page.evaluate(async ({ runId, ownReference }) => {
    const res = await fetch('/api/v1/jobs', {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        installerId: '6a83ef63347d989cc5de4a3c',
        activityType: 'heating_cooling',
        customerType: 'residential',
        customer: {
          name: 'Chrome Demo No Mandatory ' + runId,
          email: 'chrome.demo.nomandatory.' + runId + '@yopmail.com',
          phoneNumber: '4' + runId,
        },
        ownReference,
      }),
    });
    return { status: res.status, body: await res.json() };
  }, { runId, ownReference });
  console.log('Response status:', resp.status);
  console.log('Job created:', resp.body.data.job.jobNumber, '/', resp.body.data.job.id);
  const jobNumber = resp.body.data.job.jobNumber;

  console.log('\n=== STEP 2: Open the Jobs list and search for it ===');
  await page.goto('https://nswdev.rebatem8.com.au/jobs');
  await page.getByPlaceholder('Search Jobs...').fill(ownReference);
  await page.waitForTimeout(2500);
  const rowText = await page.locator('table tbody tr').first().allTextContents();
  console.log('Row in list:', JSON.stringify(rowText));
  console.log('>>> Watch the "Installation Date" and "Address" columns for this job in the browser.');
  await page.waitForTimeout(3000);

  console.log('\n=== STEP 3: Open the job detail to see the actual Engagement form ===');
  await page.locator('table tbody tr').first().locator('svg, img, button').first().click();
  await page.waitForTimeout(2500);
  console.log('>>> Watch: Site address, Postcode, ABN/ACN, Method of lead generation, Installation date, and Products are all empty placeholders.');
  console.log('>>> But Building type already shows "Residential Building" selected, despite never being sent.');
  await page.waitForTimeout(6000);

  console.log(`\nDone. This is job ${jobNumber}. Leaving the browser open for 30s so you can inspect it.`);
  await page.waitForTimeout(30000);
  await browser.close();
})();
