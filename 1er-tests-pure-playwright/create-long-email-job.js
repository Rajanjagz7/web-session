// One-off: create a job with a long, special-character-containing yopmail
// address, so it can be checked in the yopmail inbox. Uses characters that
// are actually valid in an email local-part (. + _ -) so the form's own
// validation accepts it rather than rejecting it.
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

const LONG_EMAIL = 'qa.longtest+special_chars-boundary.value.email.address.check.2026@yopmail.com';

const job = {
  customerName: 'Long Email Boundary Test',
  email: LONG_EMAIL,
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '1 Martin Place Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Email campaign',
  ownReference: `REF-${RUN_ID}-LONGEMAIL`,
  installationDate: '22-09-2026',
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

    console.log(`Email under test (${LONG_EMAIL.length} chars): ${LONG_EMAIL}`);
    console.log(`Creating job for ${job.customerName}`);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, job);

    const emailField = dialog.getByPlaceholder('customer@email.com');
    const emailValue = await emailField.inputValue();
    console.log(`Email field holds (${emailValue.length} chars): "${emailValue}"`);

    const { created } = await submitAndReport(page, dialog, job.customerName);
    console.log(created ? '\nDone: job created.' : '\nDone: job was blocked - see dialog text above.');
    process.exitCode = created ? 0 : 1;
  } finally {
    await browser.close();
  }
})();
