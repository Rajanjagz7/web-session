import { env, fill, personaCreds, personaApi } from '../config/env';
import { expect, fixme, live, needs, test } from '../fixtures/test';
import { LoginPage } from '../pages/LoginPage';
import { PortalPage } from '../pages/PortalPage';

/** Release notes: New Features > Customer Portal (POR-01..04), CUS-03c, Bug Fixes > BUG-07. Runs on PORTAL_URL. */
test.describe('@portal Customer portal', () => {
  live('POR-01', 'the quote list has a Job column; the job number shows on hover', async ({ page }) => {
    const portal = new PortalPage(page);
    await portal.openQuotes();
    await expect(portal.jobColumn).toBeVisible();
    // TODO: hover a cell whose quote belongs to a job and assert the job-number tooltip text (needs a seeded converted quote).
    const firstJobCell = portal.jobCell(/./);
    await firstJobCell.hover();
    await expect(page.getByRole('tooltip')).toBeVisible(); // TODO(confirm): tooltip role
  });

  live('POR-02', 'quotes that became jobs say "Converted to Job" in the badge and the status filter', async ({ page }) => {
    const portal = new PortalPage(page);
    await portal.openQuotes();
    await portal.statusFilter.click();
    await expect(portal.statusFilterOption(env.expected.convertedBadge)).toBeVisible();
    // TODO: assert a seeded converted quote row shows the badge; and that no converted quote still says "Accepted".
  });

  fixme('POR-03');

  live('POR-04', 'a customer can download the worklog report for their own job', async ({ request, api, uniq }) => {
    needs(env.fixtures.portalCustomerId, 'PORTAL_CUSTOMER_ID');
    const jobId = await api.createJob(env.fixtures.portalCustomerId, uniq('rn-job'));
    const res = await request.get(personaApi(fill(env.api.jobWorklogReport, jobId), env.portalUrl));
    expect(res.ok(), `worklog report status ${res.status()}`).toBeTruthy();
    expect((await res.body()).length).toBeGreaterThan(0);
    // TODO: assert the content type once the report format (PDF / CSV) is confirmed.
  });

  live('CUS-03c', 'the portal quote page shows the company name before the contact', async ({ page }) => {
    needs(env.fixtures.portalCompanyName, 'PORTAL_COMPANY_NAME');
    needs(env.fixtures.portalContactName, 'PORTAL_CONTACT_NAME');
    const portal = new PortalPage(page);
    await portal.openQuotes();
    await page.getByRole('link', { name: /quote/i }).first().click(); // TODO(confirm): how a quote opens
    const text = await portal.main.innerText();
    const company = text.indexOf(env.fixtures.portalCompanyName);
    const contact = text.indexOf(env.fixtures.portalContactName);
    expect(company, 'company present').toBeGreaterThanOrEqual(0);
    expect(contact, 'contact present').toBeGreaterThanOrEqual(0);
    expect(company, 'company before contact').toBeLessThan(contact);
  });

  live('BUG-07', 'portal login no longer fails with "Device id is required"', async ({ browser }) => {
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
});
