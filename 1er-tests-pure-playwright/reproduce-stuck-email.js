// Reproduction attempt: create a new job with the same parameters as the
// stuck job M8N000085 (Jack Sullivan - Hot Water Heat Pump / Residential /
// Heat pump / Artarmon / Online advertisement), then poll its engagement
// status over 90s to see if it also gets stuck at pending/0 attempts.
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

const job = {
  customerName: 'Repro Stuck Email Test',
  email: 'repro.stuck.email.test@yopmail.com',
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '50 Elizabeth Street Artarmon',
  postcode: '2064',
  activityType: 'Hot Water Heat Pump',
  buildingType: 'Residential Building',
  newSystem: 'Heat pump',
  leadMethod: 'Online advertisement',
  ownReference: `REF-${RUN_ID}-REPRO`,
  installationDate: '26-09-2026',
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
    console.log(`Job created: ${jobId}. Polling engagement status every 10s for 90s...\n`);

    for (let i = 0; i < 9; i++) {
      await page.waitForTimeout(10000);
      const result = await page.evaluate(async (id) => {
        const res = await fetch(`/api/v1/jobs/${id}`, { credentials: 'include' });
        const json = await res.json().catch(() => null);
        return { status: res.status, jobNumber: json?.data?.job?.jobNumber, engagement: json?.data?.job?.engagement || null };
      }, jobId);
      console.log(`[t+${(i + 1) * 10}s] jobNumber=${result.jobNumber} engagement=${JSON.stringify(result.engagement)}`);
    }
  } finally {
    await browser.close();
  }
})();
