/**
 * Release notes: New Features > Customer Portal; Customers > company name first (portal quote page).
 * IDs in this file: CP-01, CP-02, CP-03, CP-04, CU-03c
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { expect, needs, test } from '../fixtures/data.fixture';
import { env, fill, personaApi } from '../lib/env';
import { PortalPage } from '../pages/PortalPage';

test.describe('@portal Customer Portal', () => {
  test('[CP-01] @portal @portal-customer the quote list has a Job column; the job number shows on hover', async ({ page }) => {
    const portal = new PortalPage(page);
    await portal.openQuotes();
    await expect(portal.jobColumn).toBeVisible();
    // TODO: hover a cell whose quote belongs to a job and assert the job-number tooltip text (needs a seeded converted quote).
    const firstJobCell = portal.jobCell(/./);
    await firstJobCell.hover();
    await expect(page.getByRole('tooltip')).toBeVisible(); // TODO(confirm): tooltip role
  });

  test('[CP-02] @portal @portal-customer quotes that became jobs say "Converted to Job" in the badge and the status filter', async ({ page }) => {
    const portal = new PortalPage(page);
    await portal.openQuotes();
    await portal.statusFilter.click();
    await expect(portal.statusFilterOption(env.expected.convertedBadge)).toBeVisible();
    // TODO: assert a seeded converted quote row shows the badge; and that no converted quote still says "Accepted".
  });

  test('[CP-03] @portal @portal-customer If portal access is removed while logged in, customer sees "You no longer have access to the customer portal"', async () => {
    test.fixme(true, 'reason: needs a dedicated portal login whose access can be revoked mid-session (the shared portal-customer persona must not be broken) and the revoke endpoint');
  });

  test('[CP-04] @portal @portal-customer a customer can download the worklog report for their own job', async ({ request, data, uniq }) => {
    needs(env.fixtures.portalCustomerId, 'PORTAL_CUSTOMER_ID');
    const jobId = await data.seedJob(env.fixtures.portalCustomerId, uniq('rn-job'));
    const res = await request.get(personaApi(fill(env.api.jobWorklogReport, jobId), env.portalUrl));
    expect(res.ok(), `worklog report status ${res.status()}`).toBeTruthy();
    expect((await res.body()).length).toBeGreaterThan(0);
    // TODO: assert the content type once the report format (PDF / CSV) is confirmed.
  });
});

test.describe('@customers Customers', () => {
  test('[CU-03c] @customers @portal @portal-customer the portal quote page shows the company name before the contact', async ({ page }) => {
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
});
