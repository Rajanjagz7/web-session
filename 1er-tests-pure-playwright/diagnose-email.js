// Diagnostic: create a job and capture every network request/response and
// console message around the "Send engagement letter & fact sheet" submit,
// to see whether the email-triggering API call fires and what it returns.
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

const job = {
  customerName: 'Email Diagnostic Test',
  email: 'email.diagnostic.test@yopmail.com',
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '1 George Street Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Customer initiated contact',
  ownReference: `REF-${RUN_ID}-EMAILDIAG`,
  installationDate: '24-09-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
};

(async () => {
  const browser = await chromium.launch({ headless: !HEADED, slowMo: HEADED ? 60 : 0 });
  const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  let relevantLog = [];
  const isNoise = (url) => /pmx-support|widget\.js|\.css($|\?)|\/assets\/.*\.(js|png|svg|woff)|\/auth\/me/i.test(url);
  page.on('request', (req) => {
    const url = req.url();
    if (!isNoise(url) && req.method() !== 'GET') {
      relevantLog.push({ type: 'request', method: req.method(), url, postData: req.postData()?.slice(0, 800) });
    }
  });
  page.on('response', async (res) => {
    const url = res.url();
    if (isNoise(url)) return;
    if (res.request().method() !== 'GET') {
      let body = null;
      try { body = (await res.text()).slice(0, 3000); } catch {}
      relevantLog.push({ type: 'response', status: res.status(), url, body });
    }
  });
  page.on('console', (msg) => {
    if (msg.type() === 'error' || msg.type() === 'warning') {
      relevantLog.push({ type: `console:${msg.type()}`, text: msg.text() });
    }
  });
  page.on('requestfailed', (req) => {
    if (isNoise(req.url())) return;
    relevantLog.push({ type: 'requestfailed', url: req.url(), failure: req.failure()?.errorText });
  });

  try {
    console.log(`Logging in to ${BASE_URL} ...`);
    await login(page);
    console.log('Logged in.\n');

    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, job);

    console.log('--- Submitting and capturing network/console activity for 6s ---\n');
    relevantLog = []; // reset - only care about activity from the submit click onward
    await dialog.getByRole('button', { name: /send engagement letter/i }).click();
    await page.waitForTimeout(6000);

    console.log(`Captured ${relevantLog.length} relevant events:\n`);
    for (const entry of relevantLog) {
      console.log(JSON.stringify(entry, null, 2));
    }

    const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
    console.log(`\nDrawer still open (blocked): ${stillOpen}`);
  } finally {
    await browser.close();
  }
})();
