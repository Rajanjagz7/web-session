// Creates 15 NSW jobs on the RebateM8 NSW dev site using raw Puppeteer
// (no Playwright) - a Puppeteer port of ../1er-tests-pure-playwright's
// "Valid job creation" suite. Runs headed by default, per project
// convention, so the flow can be watched live.
const puppeteer = require('puppeteer');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');
const jobs = require('./jobs-data');

const HEADED = process.env.HEADED !== '0';
const LIMIT = process.env.LIMIT ? parseInt(process.env.LIMIT, 10) : jobs.length;

const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n) => `${RUN_ID}${n}`;
const abn = (n) => uniq(n).padStart(11, '0').slice(-11);
const phone = (n) => `4${uniq(n).padStart(8, '0').slice(-8)}`;

(async () => {
  const browser = await puppeteer.launch({
    headless: !HEADED,
    defaultViewport: null,
    args: ['--start-maximized'],
    slowMo: HEADED ? 40 : 0,
  });

  const page = await browser.newPage();
  const results = [];

  try {
    console.log(`Logging in to ${BASE_URL} ...`);
    await login(page);
    console.log('Logged in.\n');

    const toRun = jobs.slice(0, LIMIT);
    console.log(`Creating ${toRun.length} jobs...\n`);

    for (let i = 0; i < toRun.length; i++) {
      const data = toRun[i];
      const label = `Job ${i + 1}/${toRun.length}: ${data.customerName}`;
      console.log(label);
      try {
        let dialog;
        try {
          dialog = await openAddJobDrawer(page);
        } catch (err) {
          await page.screenshot({ path: 'debug-add-job-drawer.png', fullPage: true }).catch(() => {});
          throw err;
        }
        await fillJobForm(dialog, page, {
          customerName: data.customerName,
          email: `${data.customerName.toLowerCase().replace(/\s+/g, '.')}.${uniq(i)}@yopmail.com`,
          phone: phone(i),
          abnAcn: abn(i),
          addressSearch: data.addressSearch,
          postcode: data.postcode,
          activityType: data.activityType,
          buildingType: data.buildingType,
          newSystem: data.newSystem,
          leadMethod: data.leadMethod,
          ownReference: `REF-${RUN_ID}-${i}`,
          installationDate: data.installationDate,
          installer: INSTALLER_COMPANY,
          fillEquipment: true,
        });
        const { created } = await submitAndReport(page, dialog, label);
        results.push({ label, created, error: null });
      } catch (err) {
        console.log(`  [${label}] ERROR: ${err.message}`);
        results.push({ label, created: false, error: err.message });
      }
    }
  } finally {
    const created = results.filter((r) => r.created).length;
    const blocked = results.filter((r) => !r.created && !r.error).length;
    const errored = results.filter((r) => r.error).length;
    console.log(`\n${created} created, ${blocked} blocked, ${errored} errored (of ${results.length})`);
    if (errored) {
      console.log('\nErrored jobs:');
      results.filter((r) => r.error).forEach((r) => console.log(`  - ${r.label}: ${r.error}`));
    }
    await browser.close();
    process.exit(errored > 0 ? 1 : 0);
  }
})();
