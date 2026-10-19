/**
 * Release notes: Bug Fixes (one regression test per bug).
 * IDs in this file: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05a, BUG-05b, BUG-06, BUG-07, BUG-08, BUG-09a, BUG-09b, BUG-10a, BUG-10b, BUG-10c, BUG-10d, BUG-11, BUG-12, BUG-13
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { expect, needs, test } from '../fixtures/data.fixture';
import { env, personaCreds } from '../lib/env';
import { CustomersPage, InvitesPage } from '../pages/CustomersPage';
import { DefectsPage, JobBudgetPage } from '../pages/JobBudgetPage';
import { LoginAsPage } from '../pages/LoginAsPage';
import { LoginPage } from '../pages/LoginPage';
import { QuotesPage } from '../pages/QuotesPage';

test.describe('@regression Bug Fixes', () => {
  test('[BUG-01] @regression @super-admin Contracts: recipients who have signed no longer show "Opened: Not yet" or "Read: Not yet"', async () => {
    test.fixme(true, 'reason: needs a contract with a signed recipient (signing link flow) seeded through the API');
  });

  test('[BUG-02] @regression @super-admin a new quote does not keep the section name and rows from the previous new quote', async ({ page }) => {
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await quotes.newQuoteButton.click();
    await quotes.sectionNameInputs.first().fill('rn-previous-section'); // TODO(confirm): sections step locator
    await page.goBack(); // leave without saving
    await quotes.newQuoteButton.click();
    await expect(quotes.sectionNameInputs.first()).toHaveValue('');
    await expect(quotes.lineRows).toHaveCount(0);
  });

  test('[BUG-03] @regression @super-admin defect title and description changes are saved when the menu is closed', async ({ page, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await data.seedJob(customer.id, uniq('rn-job'));
    const defects = new DefectsPage(page);
    await defects.openJobDefects(jobId);
    await defects.addDefect.click();
    const title = uniq('rn-defect');
    await defects.title.fill(title);
    await defects.description.fill('rn-description-after-edit');
    await defects.close.click(); // closing the menu is what used to lose the edit
    await page.reload();
    await expect(defects.defectRow(title)).toBeVisible();
    await defects.defectRow(title).click();
    await expect(defects.description).toHaveValue('rn-description-after-edit');
  });

  test('[BUG-04] @regression @super-admin Defects: the defect view shows the drawing with its markup, not the plain image', async () => {
    test.fixme(true, 'reason: needs a defect with a drawing and markup seeded (file upload) and an image-diff baseline');
  });

  test('[BUG-05a] @regression @cost-viewer editing the job budget no longer wipes the prices copied from the quote', async ({ page, data, uniq }) => {
    const { jobId } = await data.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await budget.openBudgetTab();
    await expect(budget.sellPrice('Line A')).toHaveValue('100');
    await expect(budget.costPrice('Line A')).toHaveValue('60');
    await budget.quantity('Line A').fill('5');
    await budget.saveButton.click();
    await page.reload();
    await budget.openBudgetTab();
    await expect(budget.sellPrice('Line A')).toHaveValue('100');
    await expect(budget.costPrice('Line A')).toHaveValue('60');
  });

  test('[BUG-05b] @regression @cost-viewer Jobs: prices already wiped on existing jobs can be restored', async () => {
    test.fixme(true, 'reason: needs a legacy job with wiped prices and the documented restore action');
  });

  test('[BUG-06] @regression @super-admin Jobs: budget lines typed by hand on a quote match correctly in daily reports', async () => {
    test.fixme(true, 'reason: needs a daily report seed that references a hand-typed quote line');
  });

  test('[BUG-07] @regression @portal-customer portal login no longer fails with "Device id is required"', async ({ browser }) => {
    const creds = personaCreds['portal-customer'];
    needs(creds.mobile, 'PERSONA_PORTAL_CUSTOMER_MOBILE');
    const context = await browser.newContext(); // fresh device: no stored device id
    const page = await context.newPage();
    const login = new LoginPage(page);
    await login.openLogin(env.portalUrl);
    await login.signInWithMobileAndOtp(creds.mobile, creds.otp);
    await expect(login.deviceIdError).toHaveCount(0);
    await login.expectSignedIn();
    await context.close();
  });

  test('[BUG-08] @regression @portal-customer Plan checks now handle customer portal logins correctly', async () => {
    test.fixme(true, 'reason: needs a plan-limited company and the plan-check endpoint that portal logins hit');
  });

  test('[BUG-09a] @regression @super-admin Invites: a refused customer invite shows an error instead of hanging', async () => {
    test.fixme(true, 'reason: needs a precondition that makes the server refuse the invite (rule unknown)');
  });

  test('[BUG-09b] @regression @super-admin a missing email on an invite gives a clear error', async ({ page }) => {
    const invites = new InvitesPage(page);
    await invites.openInvites();
    await invites.inviteButton.click();
    await invites.sendInviteButton.click();
    await expect(invites.alert.or(invites.inviteDialog.getByRole('alert')).first()).toContainText(/email/i);
    await expect(page.getByRole('progressbar')).toHaveCount(0); // not left "hanging"
  });

  test('[BUG-10a] @regression @super-admin Insights: Average Job Duration respects the date range', async () => {
    test.fixme(true, 'reason: needs seeded jobs with known durations inside and outside a date range');
  });

  test('[BUG-10b] @regression @super-admin Insights: weekly revenue counts every day, not only Mondays', async () => {
    test.fixme(true, 'reason: needs seeded invoices on every weekday and the expected weekly total');
  });

  test('[BUG-10c] @regression @super-admin Insights: submission compliance respects the worker filter', async () => {
    test.fixme(true, 'reason: needs seeded submissions for two workers and the expected compliance figures');
  });

  test('[BUG-10d] @regression @super-admin Insights: older "Created" invoices are included in status totals', async () => {
    test.fixme(true, 'reason: needs an invoice in the legacy "Created" state and expected totals');
  });

  test('[BUG-11] @regression @super-admin users and customers can be found by the phone number and customer number shown in the list', async ({ page, data, uniq }) => {
    const contact = uniq('rn-contact');
    await data.seedCustomer({ company: uniq('rn-co'), contact, email: `${uniq('rn')}@example.invalid`, mobile: '0412345678' }); // TODO(confirm): mobile format accepted
    const customers = new CustomersPage(page);
    await customers.openList();
    await customers.searchBox.fill(contact);
    const cells = await customers.row(contact).getByRole('cell').allInnerTexts();
    const shownPhone = cells.map((c) => c.trim()).find((c) => /^[+\d][\d\s()+-]{7,}$/.test(c)); // TODO: fragile; add a test-id per column
    const shownNumber = cells.map((c) => c.trim()).find((c) => /^[A-Za-z]{0,4}-?\d{3,}$/.test(c) && c !== shownPhone); // TODO: fragile
    expect(shownPhone, 'a phone number is shown in the list').toBeDefined();
    for (const term of [shownPhone, shownNumber]) {
      if (term === undefined) continue; // TODO: customer number column not found; confirm its format
      await customers.searchBox.fill(term);
      await expect(customers.row(contact)).toBeVisible();
    }
    // TODO: repeat for Users (needs a seeded user with a mobile number).
  });

  test('[BUG-12] @regression @super-admin the Log In As button is hidden while you are already logged in as someone else', async ({ page }) => {
    const admin = new LoginAsPage(page);
    await admin.openAccounts();
    await admin.logInAsButton(/./).first().click();
    await expect(admin.loggedInAsBanner).toBeVisible();
    const customers = new CustomersPage(page);
    await customers.openList();
    await expect(page.getByRole('button', { name: /log in as/i })).toHaveCount(0);
  });

  test('[BUG-13] @regression @super-admin the login logo is not squashed against the top of the screen', async ({ browser }) => {
    const context = await browser.newContext(); // signed out
    const page = await context.newPage();
    const login = new LoginPage(page);
    await login.openLogin(env.baseUrl);
    await expect(login.logo).toBeVisible();
    const box = await login.logo.boundingBox();
    expect(box, 'logo has a box').not.toBeNull();
    expect(box?.y ?? 0, 'space above the logo (px)').toBeGreaterThanOrEqual(8); // TODO(confirm): the design spacing; 8 px is a minimum, not the spec
    expect(box?.height ?? 0, 'logo height (px)').toBeGreaterThan(16);
    // TODO: add a visual baseline (toHaveScreenshot) once the approved design is available.
    await context.close();
  });
});
