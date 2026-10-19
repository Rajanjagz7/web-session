// One-off: create a new job with fresh valid data.
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

const job = {
  customerName: 'Ryan Coleman',
  email: 'ryan.coleman.next@yopmail.com',
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '30 Clarence Street Sydney',
  postcode: '2000',
  activityType: 'Hot Water Heat Pump',
  buildingType: 'Small Business Site',
  leadMethod: 'Pamphlet',
  ownReference: `REF-${RUN_ID}-NEXT`,
  installationDate: '30-09-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
};

(async () => {
  const browser = await chromium.launch({ headless: !HEADED, slowMo: HEADED ? 40 : 0 });
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
  } finally {
    await browser.close();
  }
})();
