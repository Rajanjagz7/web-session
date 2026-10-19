// A few more email boundary/edge cases, isolating the email field while
// keeping every other field valid/boilerplate. Reports created vs blocked
// for each (exploratory - doesn't assert an expected outcome, documents
// real behaviour, same style as submitAndReport elsewhere in this suite).
const { chromium } = require('playwright');
const { BASE_URL, INSTALLER_COMPANY } = require('./config');
const { login, openAddJobDrawer, fillJobForm, submitAndReport } = require('./helpers');

const HEADED = process.env.HEADED !== '0';
const RUN_ID = Date.now().toString().slice(-8);

function localPart(len, filler = 'x') {
  const base = 'edge.case.';
  return base.length >= len ? base.slice(0, len) : base + filler.repeat(len - base.length);
}

const cases = [
  { label: '64-char local-part (RFC 5321 max)', email: `${localPart(64)}@yopmail.com` },
  { label: '65-char local-part (1 over RFC max)', email: `${localPart(65)}@yopmail.com` },
  { label: 'Consecutive dots in local-part', email: 'edge..case..dots@yopmail.com' },
  { label: 'Leading dot in local-part', email: '.edgecase@yopmail.com' },
  { label: 'Trailing dot in local-part', email: 'edgecase.@yopmail.com' },
  { label: 'Uppercase email', email: 'EDGE.CASE.UPPER@YOPMAIL.COM' },
  { label: 'Unicode/emoji in local-part', email: 'tëst🎉edge@yopmail.com' },
  { label: 'No TLD on domain', email: 'edgecase@yopmail' },
  { label: 'Leading/trailing whitespace', email: '  edgecase.whitespace@yopmail.com  ' },
  { label: 'Minimal valid email', email: 'a@b.co' },
];

(async () => {
  const browser = await chromium.launch({ headless: !HEADED, slowMo: HEADED ? 40 : 0 });
  const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  try {
    console.log(`Logging in to ${BASE_URL} ...`);
    await login(page);
    console.log('Logged in.\n');

    for (let i = 0; i < cases.length; i++) {
      const c = cases[i];
      console.log(`\n=== Case ${i + 1}/${cases.length}: ${c.label} ===`);
      console.log(`Email (${c.email.length} chars, raw): "${c.email}"`);

      const dialog = await openAddJobDrawer(page);
      await fillJobForm(dialog, {
        customerName: `Edge Email ${i + 1}`,
        email: c.email,
        phone: `4${(RUN_ID + i).padStart(8, '0').slice(-8)}`,
        abnAcn: (RUN_ID + i).padStart(11, '0').slice(-11),
        addressSearch: '10 Pitt Street Sydney',
        postcode: '2000',
        activityType: 'Heating & Cooling',
        buildingType: 'Residential Building',
        leadMethod: 'Social media',
        ownReference: `REF-${RUN_ID}-EDGE${i}`,
        installationDate: '28-09-2026',
        installer: INSTALLER_COMPANY,
        fillEquipment: true,
      });

      const emailField = dialog.getByPlaceholder('customer@email.com');
      const heldValue = await emailField.inputValue();
      console.log(`Field holds (${heldValue.length} chars): "${heldValue}"`);

      await submitAndReport(page, dialog, c.label);

      // Close the drawer if it's still open (blocked), so the next case
      // starts clean.
      const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
      if (stillOpen) {
        await page.keyboard.press('Escape').catch(() => {});
        await page.waitForTimeout(500);
      }
    }
  } finally {
    await browser.close();
  }
})();
