// Concurrency test: created at roughly the same time as a job created from
// mobile, to check for job-number collisions or other race conditions in
// job creation.
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

const job = {
  customerName: 'Concurrency Test Web',
  email: 'concurrency.test.web@yopmail.com',
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '20 Bridge Street Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Customer initiated contact',
  ownReference: `REF-${RUN_ID}-CONCWEB`,
  installationDate: '29-09-2026',
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

    console.log(`[${new Date().toISOString()}] Creating job for ${job.customerName}`);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, job);
    console.log(`[${new Date().toISOString()}] Submitting...`);
    const { created } = await submitAndReport(page, dialog, job.customerName);
    console.log(`[${new Date().toISOString()}] ${created ? 'Job created.' : 'Job blocked.'}`);
  } finally {
    await browser.close();
  }
})();
