// A fresh batch of 15 edge/boundary scenarios across different fields
// (not just email this time) - postcode, ABN, phone, dates, name/reference
// content, multi-product brand variety, regional addresses, duplicates.
// Exploratory: reports created vs blocked for each, doesn't assert an
// expected outcome (same style as submitAndReport elsewhere in this suite).
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n) => `${RUN_ID}${n}`;

const baseValid = (i, overrides = {}) => ({
  customerName: `Batch2 Edge ${i}`,
  email: `batch2.edge.${uniq(i)}@yopmail.com`,
  phone: `4${uniq(i).padStart(8, '0').slice(-8)}`,
  abnAcn: uniq(i).padStart(11, '0').slice(-11),
  addressSearch: '10 Pitt Street Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Customer initiated contact',
  ownReference: `REF-${RUN_ID}-B2-${i}`,
  installationDate: '01-10-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
  ...overrides,
});

const cases = [
  { label: 'Postcode too short (1 digit)', fields: baseValid(1, { postcode: '2' }) },
  { label: 'Postcode with letters', fields: baseValid(2, { postcode: 'AB12' }) },
  { label: 'Postcode too long (6 digits)', fields: baseValid(3, { postcode: '200012' }) },
  { label: 'ABN/ACN with letters mixed in', fields: baseValid(4, { abnAcn: '1234ABCD901' }) },
  { label: 'Phone with leading zero (10 digits)', fields: baseValid(5, { phone: '0412345678' }) },
  { label: 'Installation date far future (31-12-2099)', fields: baseValid(6, { installationDate: '31-12-2099' }) },
  { label: "Customer name is only emoji", fields: baseValid(7, { customerName: '🏠🔥❄️🛠️' }) },
  { label: 'Own reference extremely long (300 chars)', fields: baseValid(8, { ownReference: 'REF-' + 'Z'.repeat(300) }) },
  { label: '5-product job (max brand variety)', fields: baseValid(9, { productCount: 5 }) },
  { label: 'SQL-injection style Own reference', fields: baseValid(10, { ownReference: "REF'); DROP TABLE Jobs;--" }) },
  { label: 'Regional NSW address (Dubbo)', fields: baseValid(11, { addressSearch: '1 Talbragar Street Dubbo', postcode: '2830' }) },
  { label: 'Regional NSW address (Newcastle)', fields: baseValid(12, { addressSearch: '1 Hunter Street Newcastle', postcode: '2300' }) },
  { label: 'Duplicate ABN reused from case 1', fields: baseValid(13, { abnAcn: uniq(1).padStart(11, '0').slice(-11) }) },
  { label: 'Small Business + Doorknocking lead method', fields: baseValid(14, { buildingType: 'Small Business Site', leadMethod: 'Doorknocking (pre-1 August 2024)' }) },
  { label: 'Whitespace-only Own reference', fields: baseValid(15, { ownReference: '     ' }) },
];

(async () => {
  const browser = await chromium.launch({ headless: !HEADED, slowMo: HEADED ? 40 : 0 });
  const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const results = [];

  try {
    console.log(`Logging in to ${BASE_URL} ...`);
    await login(page);
    console.log('Logged in.\n');

    for (let i = 0; i < cases.length; i++) {
      const c = cases[i];
      console.log(`\n=== Case ${i + 1}/${cases.length}: ${c.label} ===`);
      try {
        const dialog = await openAddJobDrawer(page);
        await fillJobForm(dialog, c.fields);

        // Capture which brand(s)/model(s) got picked for this job, so we
        // can confirm variety across the batch.
        const brandTexts = await dialog.locator('.border-dashed.border-gray-300').evaluateAll((containers) =>
          containers.map((c) => {
            const text = c.innerText || '';
            return text.slice(0, 200).replace(/\s+/g, ' ').trim();
          })
        );
        console.log(`Product block(s): ${JSON.stringify(brandTexts)}`);

        const { created } = await submitAndReport(page, dialog, c.label);
        results.push({ label: c.label, created });

        const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
        if (stillOpen) {
          await page.keyboard.press('Escape').catch(() => {});
          await page.waitForTimeout(500);
        }
      } catch (err) {
        console.log(`  ERROR: ${err.message}`);
        results.push({ label: c.label, created: false, error: err.message });
        await page.keyboard.press('Escape').catch(() => {});
        await page.waitForTimeout(500);
      }
    }
  } finally {
    console.log('\n\n=== Summary ===');
    results.forEach((r) => console.log(`${r.created ? 'CREATED' : 'BLOCKED'.padEnd(7)} - ${r.label}${r.error ? ` (ERROR: ${r.error})` : ''}`));
    await browser.close();
  }
})();
