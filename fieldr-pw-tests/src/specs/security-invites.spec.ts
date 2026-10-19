/**
 * Release notes: Security & Data Quality; Improvements > Customer Invites.
 * IDs in this file: INV-01, INV-02, INV-03, INV-04, INV-05, INV-06, INV-07, SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { expect, needs, test } from '../fixtures/data.fixture';
import { env, fill, personaApi } from '../lib/env';
import { KEY } from '../lib/payloads';
import { CustomersPage, InvitesPage } from '../pages/CustomersPage';
import { expectNoLabelViolations } from '../lib/a11y';

const DENIED = [401, 403] as const;

test.describe('@invites Customer Invites', () => {
  test('[INV-01] @invites @super-admin the customer invite details step asks company name, address (required) and notes, with no staff fields', async ({ page, data, uniq }) => {
    const { link } = await data.seedInvite('customer', `${uniq('rn')}@example.invalid`);
    test.skip(link === undefined, 'reason: the create-invite response has no link field; set KEY.invite.link in src/config/payloads.ts');
    await page.goto(link ?? '');
    const invites = new InvitesPage(page);
    await expect(invites.companyName).toBeVisible();
    await expect(invites.address).toBeVisible();
    await expect(invites.notes).toBeVisible();
    await expect(invites.address).toHaveAttribute('aria-required', 'true');
    await expect(invites.dateOfBirth).toHaveCount(0);
    await expect(invites.licences).toHaveCount(0);
  });

  test('[INV-02] @invites @super-admin opening a customer invite while signed in as staff does not ask you to sign out', async ({ page, data, uniq }) => {
    const { link } = await data.seedInvite('customer', `${uniq('rn')}@example.invalid`);
    test.skip(link === undefined, 'reason: the create-invite response has no link field; set KEY.invite.link in src/config/payloads.ts');
    await page.goto(link ?? '');
    await expect(page.getByRole('button', { name: /sign out|log out/i })).toHaveCount(0);
    await expect(page.getByRole('main')).not.toContainText(/sign out/i); // TODO: also cover a dialog outside main if the prompt is a modal
    await expect(new InvitesPage(page).companyName).toBeVisible();
  });

  test('[INV-03] @invites @portal-customer A customer of another company can accept an invite using the mobile number already on their login', async () => {
    test.fixme(true, 'reason: needs a second company plus an invite link seeded for an existing portal login');
  });

  test('[INV-04] @invites @super-admin "Your sign-in email" now reads "Your registration email"', async ({ page, data, uniq }) => {
    const { link } = await data.seedInvite('customer', `${uniq('rn')}@example.invalid`);
    test.skip(link === undefined, 'reason: the create-invite response has no link field; set KEY.invite.link in src/config/payloads.ts');
    await page.goto(link ?? '');
    const invites = new InvitesPage(page);
    await expect(invites.registrationEmailLabel).toBeVisible();
    await expect(invites.oldSignInEmailLabel).toHaveCount(0);
  });

  test('[INV-05] @invites @super-admin the "waiting" count does not shrink while you search', async ({ page, data, uniq }) => {
    const emails = [1, 2, 3].map(() => `${uniq('rn')}@example.invalid`);
    for (const email of emails) await data.seedInvite('customer', email);
    const invites = new InvitesPage(page);
    await invites.openInvites();
    const readCount = async (): Promise<number> => Number(((await invites.waitingCount.innerText()).match(/\d+/) ?? ['NaN'])[0]);
    const before = await readCount();
    expect(before).toBeGreaterThanOrEqual(3);
    await invites.searchBox.fill(emails[0] ?? '');
    await expect(invites.rows.filter({ hasText: emails[0] ?? '' })).toHaveCount(1);
    expect(await readCount()).toBe(before);
  });

  test('[INV-06] @invites @super-admin the invite dialog and its buttons have accessible names (automated part)', async ({ page }) => {
    const invites = new InvitesPage(page);
    await invites.openInvites();
    await invites.inviteButton.click();
    await expect(invites.inviteDialog).toBeVisible();
    await expect(invites.inviteDialog).toHaveAccessibleName(/./);
    for (const button of await invites.inviteDialog.getByRole('button').all()) await expect(button).toHaveAccessibleName(/./);
    await expectNoLabelViolations(page, invites.inviteDialog);
    // MANUAL: screen-reader announcement order, focus return on close and live-region behaviour need a real screen reader.
  });

  test('[INV-07] @invites @super-admin inviting a customer\'s email as staff explains why instead of saying "already a member"', async ({ page, data, uniq }) => {
    const email = `${uniq('rn')}@example.invalid`;
    await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email });
    const invites = new InvitesPage(page);
    await invites.openInvites();
    await invites.inviteButton.click(); // TODO(confirm): choose the "staff" invite type in the dialog
    await invites.emailInput.fill(email);
    await invites.sendInviteButton.click();
    await expect(invites.alert).toBeVisible();
    await expect(invites.alert).not.toContainText(/already a member/i);
    await expect(invites.alert).toContainText(/customer/i); // TODO(confirm): exact wording
  });
});

test.describe('@security Security & Data Quality', () => {
  test('[SEC-01] @security @no-permission staff invites: send, view, resend and cancel are refused (UI hidden, API 403)', async ({ page, request, data, uniq }) => {
    const seeded = await data.seedInvite('staff', `${uniq('rn')}@example.invalid`);
    const invites = new InvitesPage(page);
    await invites.openInvites();
    await expect(invites.sendInviteButton).toHaveCount(0);
    const list = await request.get(personaApi(env.api.invites));
    expect(DENIED, 'view/list').toContain(list.status());
    const send = await request.post(personaApi(env.api.invites), { data: { [KEY.invite.kind]: 'staff', [KEY.invite.email]: `${uniq('rn')}@example.invalid` } });
    expect(DENIED, 'send').toContain(send.status());
    const resend = await request.post(personaApi(`${fill(env.api.invite, seeded.id)}/resend`)); // TODO: confirm resend route
    expect(DENIED, 'resend').toContain(resend.status());
    const cancel = await request.delete(personaApi(fill(env.api.invite, seeded.id))); // TODO: confirm cancel is DELETE
    expect(DENIED, 'cancel').toContain(cancel.status());
  });

  test('[SEC-02] @security @no-permission customer invites: send, view, resend and cancel are refused (UI hidden, API 403)', async ({ page, request, data, uniq }) => {
    const seeded = await data.seedInvite('customer', `${uniq('rn')}@example.invalid`);
    const invites = new InvitesPage(page);
    await invites.openInvites();
    await expect(invites.sendInviteButton).toHaveCount(0);
    const list = await request.get(personaApi(env.api.invites));
    expect(DENIED, 'view/list').toContain(list.status());
    const send = await request.post(personaApi(env.api.invites), { data: { [KEY.invite.kind]: 'customer', [KEY.invite.email]: `${uniq('rn')}@example.invalid` } });
    expect(DENIED, 'send').toContain(send.status());
    const resend = await request.post(personaApi(`${fill(env.api.invite, seeded.id)}/resend`)); // TODO: confirm resend route
    expect(DENIED, 'resend').toContain(resend.status());
    const cancel = await request.delete(personaApi(fill(env.api.invite, seeded.id))); // TODO: confirm cancel is DELETE
    expect(DENIED, 'cancel').toContain(cancel.status());
  });

  test('[SEC-03] @security @super-admin invalid email addresses are refused for invites, users and customers', async ({ data, uniq }) => {
    const bad = ['not-an-email', 'a@b', 'two@@example.invalid', ' spaced@example.invalid'];
    for (const email of bad) {
      const invite = await data.post(env.api.invites, { [KEY.invite.kind]: 'customer', [KEY.invite.email]: email });
      expect([400, 422], `invite with "${email}"`).toContain(invite.status());
      const user = await data.post(env.api.users, { [KEY.user.firstName]: uniq('rn'), [KEY.user.lastName]: 'x', [KEY.user.email]: email });
      expect([400, 422], `user with "${email}"`).toContain(user.status());
      const customer = await data.post(env.api.customers, { [KEY.customer.contactName]: uniq('rn'), [KEY.customer.email]: email });
      expect([400, 422], `customer with "${email}"`).toContain(customer.status());
    }
  });

  test('[SEC-04] @security @super-admin a deleted customer and a deleted user cannot be opened from an old link', async ({ page, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await expect(customers.main).toBeVisible(); // the link works while the customer exists
    expect((await data.deleteCustomer(customer.id)).ok()).toBeTruthy();
    await customers.openDetails(customer.id);
    await expect(page.getByRole('heading', { name: /not found|no longer|deleted/i })).toBeVisible(); // TODO(confirm): wording
    expect((await data.get(fill(env.api.customer, customer.id))).status()).toBe(404);
    // Users: same flow with data.createUser + a delete call; the user detail route is unconfirmed, so the UI half is TODO.
    const userId = await data.seedUser({ firstName: uniq('rn'), lastName: 'x', email: `${uniq('rn')}@example.invalid` });
    expect((await data.delete(fill(env.api.user, userId))).ok()).toBeTruthy();
    expect((await data.get(fill(env.api.user, userId))).status()).toBe(404);
  });

  test('[SEC-05] @security @super-admin a company name must contain at least one letter', async ({ data, uniq }) => {
    for (const company of ['12345', '---', '   ', '(+)']) {
      const res = await data.post(env.api.customers, { [KEY.customer.company]: company, [KEY.customer.contactName]: uniq('rn'), [KEY.customer.email]: `${uniq('rn')}@example.invalid` });
      expect([400, 422], `company "${company}"`).toContain(res.status());
    }
    const ok = await data.seedCustomer({ company: `${uniq('rn')} 2`, contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` }); // a name with a letter still saves
    expect(ok.id).not.toBe('');
  });

  test('[SEC-06] @security @portal-customer a customer contact cannot change the company name', async ({ request, data }) => {
    needs(env.fixtures.portalCustomerId, 'PORTAL_CUSTOMER_ID');
    const before = await data.get(fill(env.api.customer, env.fixtures.portalCustomerId));
    const company = (await before.json()) as Record<string, unknown>;
    const res = await request.put(personaApi(fill(env.api.customer, env.fixtures.portalCustomerId), env.portalUrl), { data: { [KEY.customer.company]: 'rn-renamed' } });
    expect(res.status(), 'rename by a customer contact').toBeGreaterThanOrEqual(400);
    const after = (await (await data.get(fill(env.api.customer, env.fixtures.portalCustomerId))).json()) as Record<string, unknown>;
    expect(JSON.stringify(after)).toBe(JSON.stringify(company)); // unchanged
  });

  test('[SEC-07] @security @portal-customer customers can only see time logs for their own jobs', async ({ request, data, uniq }) => {
    needs(env.fixtures.portalCustomerId, 'PORTAL_CUSTOMER_ID');
    const own = await data.seedJob(env.fixtures.portalCustomerId, uniq('rn-job'));
    const other = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const othersJob = await data.seedJob(other.id, uniq('rn-job'));
    const mine = await request.get(personaApi(fill(env.api.jobTimeLogs, own), env.portalUrl));
    expect(mine.ok(), 'own job time logs').toBeTruthy();
    const theirs = await request.get(personaApi(fill(env.api.jobTimeLogs, othersJob), env.portalUrl));
    expect([403, 404], 'another customer\'s job time logs').toContain(theirs.status());
  });
});
