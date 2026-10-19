// Follow-up diagnostic: create a job, then poll GET /api/v1/jobs/{id} over
// ~60s to see whether engagement.email/factSheetEmail/sms ever move off
// "pending" (attempts: 0) - tells us if this is async latency or a stuck
// queue/worker on the backend.
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

const job = {
  customerName: 'Email Poll Diagnostic',
  email: 'email.poll.diagnostic@yopmail.com',
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '1 George Street Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Customer initiated contact',
  ownReference: `REF-${RUN_ID}-EMAILPOLL`,
  installationDate: '25-09-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
};

(async () => {
  const browser = await chromium.launch({ headless: !HEADED, slowMo: HEADED ? 60 : 0 });
  const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  let jobId = null;
  page.on('response', async (res) => {
    if (res.request().method() === 'POST' && res.url().endsWith('/api/v1/jobs')) {
      try {
        const json = await res.json();
        jobId = json?.data?.job?.id || null;
      } catch {}
    }
  });

  try {
    console.log(`Logging in to ${BASE_URL} ...`);
    await login(page);
    console.log('Logged in.\n');

    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, job);
    await dialog.getByRole('button', { name: /send engagement letter/i }).click();
    await page.waitForTimeout(3000);

    if (!jobId) {
      console.log('Could not capture job id from create response - aborting poll.');
      return;
    }
    console.log(`Job created: ${jobId}. Polling engagement status every 10s for 60s...\n`);

    for (let i = 0; i < 6; i++) {
      await page.waitForTimeout(10000);
      const result = await page.evaluate(async (id) => {
        const res = await fetch(`/api/v1/jobs/${id}`, { credentials: 'include' });
        const json = await res.json().catch(() => null);
        return { status: res.status, engagement: json?.data?.job?.engagement || json?.data?.engagement || null, raw: json };
      }, jobId);
      console.log(`[t+${(i + 1) * 10}s] status=${result.status} engagement=${JSON.stringify(result.engagement)}`);
      if (!result.engagement) {
        console.log(`  (full response) ${JSON.stringify(result.raw).slice(0, 500)}`);
      }
    }
  } finally {
    await browser.close();
  }
})();
