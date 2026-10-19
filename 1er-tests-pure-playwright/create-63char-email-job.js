// One-off: create a job with an email whose local-part (before @) is
// exactly 63 characters - one under RFC 5321's 64-octet local-part limit,
// a natural boundary-value test. Includes valid special characters and
// asserts the length in-code so we don't hand-count wrong.
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

function buildLocalPart(targetLen) {
  const base = 'qa.boundary+chars_test-63-len.value.email.local.part.check.';
  if (base.length > targetLen) return base.slice(0, targetLen);
  return base + 'x'.repeat(targetLen - base.length);
}

const LOCAL_PART = buildLocalPart(63);
if (LOCAL_PART.length !== 63) {
  throw new Error(`Local part is ${LOCAL_PART.length} chars, expected 63`);
}
const LONG_EMAIL = `${LOCAL_PART}@yopmail.com`;

const job = {
  customerName: '63 Char Email Boundary Test',
  email: LONG_EMAIL,
  phone: `4${RUN_ID.padStart(8, '0').slice(-8)}`,
  abnAcn: RUN_ID.padStart(11, '0').slice(-11),
  addressSearch: '5 Martin Place Sydney',
  postcode: '2000',
  activityType: 'Hot Water Heat Pump',
  buildingType: 'Residential Building',
  newSystem: 'Solar (electric boosted)',
  leadMethod: 'Online advertisement',
  ownReference: `REF-${RUN_ID}-63EMAIL`,
  installationDate: '23-09-2026',
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

    console.log(`Local-part length: ${LOCAL_PART.length} chars`);
    console.log(`Email under test: ${LONG_EMAIL}`);
    console.log(`Creating job for ${job.customerName}`);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, job);

    const emailField = dialog.getByPlaceholder('customer@email.com');
    const emailValue = await emailField.inputValue();
    const localPartHeld = emailValue.split('@')[0];
    console.log(`Email field holds: "${emailValue}" (local-part ${localPartHeld.length} chars)`);

    const { created } = await submitAndReport(page, dialog, job.customerName);
    console.log(created ? '\nDone: job created.' : '\nDone: job was blocked - see dialog text above.');
    process.exitCode = created ? 0 : 1;
  } finally {
    await browser.close();
  }
})();
