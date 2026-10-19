/**
 * Release notes: Improvements > Job Orders, Users, Date & Time, Phone Numbers, PDFs, Insights, Platform Admin; New Features > Admin Log In As.
 * IDs in this file: DT-01, INS-01, INS-02, LA-01, ORD-01, ORD-02, ORD-03, PA-01, PA-02, PA-03, PA-04, PA-05, PDF-01, PDF-02, PDF-03, PH-01, USR-01, USR-02
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { expect, needs, test } from '../fixtures/data.fixture';
import { env, fill, personaApi } from '../lib/env';
import { CustomersPage } from '../pages/CustomersPage';
import { LoginAsPage } from '../pages/LoginAsPage';
import { DateTimePicker, InsightsPage, JobOrderPage, UserFormPage } from '../pages/MiscPage';
import { SchedulePage } from '../pages/SchedulePage';
import { downloadPdf, blankPages } from '../lib/pdf';

// Standard Australian ABN layout XX XXX XXX XXX. TODO: the release notes say properly formatted without a pattern; confirm.
const ABN_SPACED = /\b\d{2} \d{3} \d{3} \d{3}\b/;
const ABN_UNSPACED = /\b\d{11}\b/;

test.describe('@misc Date & Time', () => {
  test('[DT-01] @misc @super-admin the picker offers 15-minute slots and scrolls to the current time when it opens', async ({ page }) => {
    await page.clock.install({ time: new Date('2026-10-07T14:07:00') }); // fixed "now" so the scroll target is deterministic
    const schedule = new SchedulePage(page);
    await schedule.openSchedule();
    await schedule.addShiftButton.click();
    const picker = new DateTimePicker(page, /start/i);
    await picker.open();
    const labels = await picker.slotLabels();
    expect(labels.length, 'slots for a full day at 15-minute spacing').toBe(96); // 24 x 4
    const toMinutes = (label: string): number => {
      const m = /(\d{1,2}):(\d{2})\s*(am|pm)?/i.exec(label);
      if (!m) throw new Error(`Unrecognised slot label: ${label}`);
      let h = Number(m[1]) % 12;
      if ((m[3] ?? '').toLowerCase() === 'pm') h += 12;
      return h * 60 + Number(m[2]);
    };
    const minutes = labels.map(toMinutes);
    for (let i = 1; i < minutes.length; i++) expect((minutes[i] ?? 0) - (minutes[i - 1] ?? 0), `step before slot ${i}`).toBe(15);
    // Scroll: with the clock at 2:07 pm the 2:00 pm (or 2:15 pm) slot must be in view. TODO(confirm): 12-hour label format and rounding rule.
    await expect(picker.slots.filter({ hasText: /^\s*2:(00|15)\s*pm\s*$/i }).first()).toBeInViewport();
  });
});

test.describe('@insights Insights', () => {
  test('[INS-01] @insights @super-admin reports show the status, customer and worker filters', async ({ page }) => {
    const insights = new InsightsPage(page);
    await insights.openInsights();
    await insights.reportLink(/./).first().click(); // TODO: iterate over each report; the report names are unconfirmed
    await expect(insights.statusFilter).toBeVisible();
    await expect(insights.customerFilter).toBeVisible();
    await expect(insights.workerFilter).toBeVisible();
  });

  test('[INS-02] @insights @super-admin percentages on cards use the same rounding as the table', async ({ page }) => {
    const insights = new InsightsPage(page);
    await insights.openInsights();
    const decimals = (s: string): number[] => [...s.matchAll(/(\d+)(?:\.(\d+))?%/g)].map((m) => (m[2] ?? '').length);
    const cardPct = decimals(await insights.cards.allInnerTexts().then((t) => t.join(' ')));
    const tablePct = decimals(await insights.tableCells.allInnerTexts().then((t) => t.join(' ')));
    expect(cardPct.length + tablePct.length, 'percentages found').toBeGreaterThan(0);
    // Proxy check: cards and table use the same number of decimal places. TODO: replace with an exact per-metric comparison
    // (card figure === table figure for the same metric) once cards and rows share a test-id per metric.
    expect(new Set([...cardPct, ...tablePct]).size, 'one rounding style across cards and table').toBe(1);
  });
});

test.describe('@admin Admin Log In As', () => {
  test('[LA-01] @admin @super-admin a super admin logged in as a company admin can log in as one of that company\'s customers', async ({ page }) => {
    const admin = new LoginAsPage(page);
    await admin.openAccounts();
    await admin.logInAsButton(/./).first().click(); // step 1: log in as the company admin (TODO: pick a named seeded company)
    await expect(admin.loggedInAsBanner).toBeVisible();
    const customers = new CustomersPage(page);
    await customers.open(env.routes.customers);
    await customers.row(/./).first().getByRole('button', { name: /log in as/i }).click(); // step 2: log in as a customer
    await expect(admin.loggedInAsBanner).toBeVisible();
    // TODO: assert the portal opens for that customer (PORTAL_URL) and the banner names the customer.
  });

  test('[LA-01] @admin @no-permission the Log In As option is not offered to a user who is not a super admin',     async ({ page }) => {
      const customers = new CustomersPage(page);
      await customers.openList();
      await expect(page.getByRole('button', { name: /log in as/i })).toHaveCount(0);
  });
});

test.describe('@misc Job Orders', () => {
  test('[ORD-01] @misc @super-admin "Phone" is now "Mobile Number" and "Site Contact" is now "Site Contact Name"', async ({ page }) => {
    const order = new JobOrderPage(page);
    await order.openNewOrder();
    await expect(order.mobileNumber).toBeVisible();
    await expect(order.siteContactName).toBeVisible();
    await expect(order.oldPhoneLabel).toHaveCount(0);
    await expect(order.oldSiteContactLabel).toHaveCount(0);
  });

  test('[ORD-02] @misc @super-admin The error message for an invalid number is clearer', async () => {
    test.fixme(true, 'reason: the new message wording is not in the release notes; set EXPECTED text then remove fixme');
  });

  test('[ORD-03] @misc @super-admin Add Line adds a line and scrolls the page to it', async ({ page }) => {
    const order = new JobOrderPage(page);
    await order.openNewOrder();
    const before = await order.lineRows.count();
    await order.addLine.click();
    await expect(order.lineRows).toHaveCount(before + 1);
    await expect(order.lineRows.last()).toBeInViewport();
  });
});

test.describe('@admin Platform Admin', () => {
  test('[PA-01] @admin @super-admin the overview loads once (one request per data source)', async ({ page }) => {
    const calls: string[] = [];
    page.on('request', (r) => {
      if (r.url().includes(env.api.adminOverview)) calls.push(r.url());
    });
    const admin = new LoginAsPage(page);
    await admin.openOverview();
    await expect(admin.main).toBeVisible();
    await page.waitForResponse((r) => r.url().includes(env.api.adminOverview)); // the first overview response
    await expect.poll(() => calls.length, { timeout: 3_000 }).toBe(1);
    // TODO: stable alternative: wait for a "loaded" test-id, then assert the request count; polling cannot prove a late second call never comes.
    expect(calls.length, `overview calls: ${calls.join(', ')}`).toBeLessThanOrEqual(1);
  });

  test('[PA-02] @admin @manual @super-admin MANUAL Year-to-date figures are correct around midnight', async () => {
    test.fixme(true, 'reason: MANUAL - needs a wall-clock boundary: mock the clock (page.clock) at 23:59:50 on 31 Dec / 30 Jun, or run a scheduled job near the boundary');
  });

  test('[PA-03] @admin @super-admin the accounts list shows sorting, accounts with zero revenue and the 200-row limit notice', async ({ page }) => {
    const admin = new LoginAsPage(page);
    await admin.openAccounts();
    await expect(admin.sortButton(/revenue/i)).toBeVisible();
    await expect(admin.accountRows.filter({ hasText: /\$?0(\.00)?\b/ }).first()).toBeVisible(); // TODO: fragile; seed a zero-revenue account and match by name
    const rows = await admin.accountRows.count();
    if (rows >= 200) {
      await expect(admin.rowLimitNotice).toBeVisible();
      if (env.expected.accountsRowLimitText !== '') await expect(admin.rowLimitNotice).toContainText(env.expected.accountsRowLimitText);
    } else {
      test.info().annotations.push({ type: 'todo', description: `only ${rows} rows: the limit notice needs an environment with 200+ accounts` });
    }
  });

  test('[PA-04] @admin @super-admin Monthly revenue counts yearly plans, trials and one-off charges correctly', async () => {
    test.fixme(true, 'reason: needs seeded revenue fixtures (yearly plan, trial, one-off) and the expected totals');
  });

  test('[PA-05] @admin @super-admin role settings only offer super-admin modules to the Super Admin role', async ({ page }) => {
    const admin = new LoginAsPage(page);
    await admin.openRoleSettings();
    const superModules = await admin.roleModuleOptions('Super Admin').count(); // TODO(confirm): role names
    const adminModules = await admin.roleModuleOptions('Admin').count();
    expect(superModules, 'Super Admin has more modules').toBeGreaterThan(adminModules);
    // TODO: assert by module name (the notes do not list the super-admin-only modules).
  });
});

test.describe('@pdf PDFs', () => {
  test('[PDF-01] @pdf @super-admin the order PDF shows the ABN formatted and has clearer labels', async ({ request }) => {
    needs(env.fixtures.orderId, 'FIXTURE_ORDER_ID');
    const pdf = await downloadPdf(request, personaApi(fill(env.api.orderPdf, env.fixtures.orderId)));
    expect(pdf.text, 'a formatted ABN').toMatch(ABN_SPACED);
    expect(pdf.text, 'no unformatted 11-digit ABN').not.toMatch(ABN_UNSPACED);
    if (env.expected.abnDisplayFormat !== '') expect(pdf.text).toContain(env.expected.abnDisplayFormat); // TODO: fill EXPECTED_ABN_DISPLAY_FORMAT
    // TODO: assert the new label wording once the notes say what "clearer labels" are (compare with Mobile Number / Site Contact Name in ORD-01).
  });

  test('[PDF-02] @pdf @super-admin the company ABN is formatted on reports too', async ({ request }) => {
    needs(env.fixtures.reportId, 'FIXTURE_REPORT_ID');
    const pdf = await downloadPdf(request, personaApi(fill(env.api.reportPdf, env.fixtures.reportId)));
    expect(pdf.text).toMatch(ABN_SPACED);
    expect(pdf.text).not.toMatch(ABN_UNSPACED);
  });

  test('[PDF-03] @pdf @super-admin timesheet PDFs have no blank pages', async ({ request }) => {
    const pdf = await downloadPdf(request, personaApi(env.api.timesheetPdf));
    expect(pdf.pages.length, 'at least one page').toBeGreaterThan(0);
    expect(blankPages(pdf), 'blank page numbers').toEqual([]);
    // TODO: seed a timesheet range that previously produced blank pages (the notes do not say which) for a sharper regression.
  });
});

test.describe('@misc Phone Numbers', () => {
  test('[PH-01] @misc @super-admin a phone number is formatted identically across forms', async ({ page }) => {
    const raw = '0412345678';
    const shown: string[] = [];
    // Form 1: job order
    const order = new JobOrderPage(page);
    await order.openNewOrder();
    await order.mobileNumber.fill(raw);
    await order.mobileNumber.blur();
    shown.push(await order.mobileNumber.inputValue());
    // Form 2: My Profile
    const profile = new UserFormPage(page);
    await profile.openProfile();
    await profile.mobile.fill(raw);
    await profile.mobile.blur();
    shown.push(await profile.mobile.inputValue());
    // Form 3: customer form. TODO: sign-up and customer-contract forms need their own page objects and routes.
    await page.goto(new URL(env.routes.customers, env.baseUrl).toString());
    await page.getByRole('button', { name: /new customer|add customer/i }).click(); // TODO(confirm)
    const customerMobile = page.getByLabel(/mobile|phone/i);
    await customerMobile.fill(raw);
    await customerMobile.blur();
    shown.push(await customerMobile.inputValue());
    expect(new Set(shown).size, `values shown: ${JSON.stringify(shown)}`).toBe(1);
    if (env.expected.phoneDisplayFormat !== '') expect(shown[0]).toBe(env.expected.phoneDisplayFormat); // TODO: fill EXPECTED_PHONE_DISPLAY_FORMAT
  });
});

test.describe('@misc Users', () => {
  test('[USR-01] @misc @super-admin Industry is optional on Add User, Edit User and My Profile', async ({ page }) => {
    const form = new UserFormPage(page);
    await form.openProfile();
    await expect(form.industry).not.toHaveAttribute('aria-required', 'true');
    await form.openUsers();
    await form.addUserButton.click();
    await expect(form.industry).not.toHaveAttribute('aria-required', 'true');
    // TODO: submit Add User with every required field except Industry and assert it saves (needs the list of required fields).
    // TODO: repeat on the Edit User screen (needs a seeded user and the edit route).
  });

  test('[USR-02] @misc @super-admin Picking a Google address fills Suburb, State and Postcode automatically', async () => {
    test.fixme(true, 'reason: needs Google Places responses stubbed with page.route or a live key; stub shape unconfirmed');
  });
});
