// One-off: create a job using an @example.com address (IANA-reserved test
// domain - unlike yopmail.com, it won't actually accept/deliver mail, so
// this is useful for checking how the app's email step behaves against a
// domain that can't receive it).
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

const job = {
  customerName: 'Example Domain Test',
  email: 'example.domain.test@example.com',
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '10 Pitt Street Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Social media',
  ownReference: `REF-${RUN_ID}-EXAMPLEDOM`,
  installationDate: '27-09-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
};

(async () => {
  const browser = await chromium.launch({ headless: !HEADED, slowMo: HEADED ? 60 : 0 });
  const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  try {
    console.log(`Logging in to ${BASE_URL} ...`);
    await login(page);
    console.log('Logged in.\n');

    console.log(`Creating job for ${job.customerName} (${job.email})`);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, job);
    const { created } = await submitAndReport(page, dialog, job.customerName);
    console.log(created ? '\nDone: job created.' : '\nDone: job was blocked - see dialog text above.');
    process.exitCode = created ? 0 : 1;
  } finally {
    await browser.close();
  }
})();
