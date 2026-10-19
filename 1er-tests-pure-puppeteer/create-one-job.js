// One-off: create a single NSW job with a specific email, rest of the
// fields picked to exercise a fresh combination not already covered by
// jobs-data.js.
const puppeteer = require('puppeteer');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

const job = {
  customerName: 'Rajan Joshi',
  email: 'rajanj@softwareco.com',
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '48 Martin Place Sydney',
  postcode: '2000',
  activityType: 'Hot Water Heat Pump',
  buildingType: 'Residential Building',
  newSystem: 'Heat pump',
  leadMethod: 'Doorknocking (pre-1 August 2024)',
  ownReference: `REF-${RUN_ID}-RJ`,
  installationDate: '20-09-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
};

(async () => {
  const browser = await puppeteer.launch({
    headless: !HEADED,
    defaultViewport: null,
    args: ['--start-maximized'],
    slowMo: HEADED ? 40 : 0,
  });
  const page = await browser.newPage();

  try {
    console.log(`Logging in to ${BASE_URL} ...`);
    await login(page);
    console.log('Logged in.\n');

    console.log(`Creating job for ${job.customerName} (${job.email})`);
    const dialog = await openAddJobDrawer(page);
    try {
      await fillJobForm(dialog, page, job);
    } catch (err) {
      await page.screenshot({ path: 'debug-fill-form.png', fullPage: true }).catch(() => {});
      throw err;
    }
    const { created } = await submitAndReport(page, dialog, job.customerName);
    console.log(created ? '\nDone: job created.' : '\nDone: job was blocked - see dialog text above.');
    process.exitCode = created ? 0 : 1;
  } finally {
    await browser.close();
  }
})();
