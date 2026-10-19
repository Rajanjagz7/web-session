import { env, fill, personaApi } from '../config/env';
import { KEY } from '../config/payloads';
import { expect, live, needs, test, type Fx } from '../fixtures/test';
import { CustomersPage } from '../pages/CustomersPage';
import { InvitesPage } from '../pages/InvitesPage';

/** Release notes: Security & Data Quality (SEC-01..07). Permission tests run as personas; seeding uses the service token. */
const DENIED = [401, 403] as const;

test.describe('@security Security and data quality', () => {
  // SEC-01 / SEC-02: a user with no permissions gets a hidden control AND an API 403 for every invite action.
  live('SEC-01', 'staff invites: send, view, resend and cancel are refused (UI hidden, API 403)', async ({ page, request, api, uniq }) => {
    const seeded = await api.createInvite('staff', `${uniq('rn')}@example.invalid`);
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

  live('SEC-02', 'customer invites: send, view, resend and cancel are refused (UI hidden, API 403)', async ({ page, request, api, uniq }) => {
    const seeded = await api.createInvite('customer', `${uniq('rn')}@example.invalid`);
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

  live('SEC-03', 'invalid email addresses are refused for invites, users and customers', async ({ api, uniq }) => {
    const bad = ['not-an-email', 'a@b', 'two@@example.invalid', ' spaced@example.invalid'];
    for (const email of bad) {
      const invite = await api.post(env.api.invites, { [KEY.invite.kind]: 'customer', [KEY.invite.email]: email });
      expect([400, 422], `invite with "${email}"`).toContain(invite.status());
      const user = await api.post(env.api.users, { [KEY.user.firstName]: uniq('rn'), [KEY.user.lastName]: 'x', [KEY.user.email]: email });
      expect([400, 422], `user with "${email}"`).toContain(user.status());
      const customer = await api.post(env.api.customers, { [KEY.customer.contactName]: uniq('rn'), [KEY.customer.email]: email });
      expect([400, 422], `customer with "${email}"`).toContain(customer.status());
    }
  });

  live('SEC-04', 'a deleted customer and a deleted user cannot be opened from an old link', async ({ page, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await expect(customers.main).toBeVisible(); // the link works while the customer exists
    expect((await api.deleteCustomer(customer.id)).ok()).toBeTruthy();
    await customers.openDetails(customer.id);
    await expect(page.getByRole('heading', { name: /not found|no longer|deleted/i })).toBeVisible(); // TODO(confirm): wording
    expect((await api.get(fill(env.api.customer, customer.id))).status()).toBe(404);
    // Users: same flow with api.createUser + a delete call; the user detail route is unconfirmed, so the UI half is TODO.
    const userId = await api.createUser({ firstName: uniq('rn'), lastName: 'x', email: `${uniq('rn')}@example.invalid` });
    expect((await api.delete(fill(env.api.user, userId))).ok()).toBeTruthy();
    expect((await api.get(fill(env.api.user, userId))).status()).toBe(404);
  });

  live('SEC-05', 'a company name must contain at least one letter', async ({ api, uniq }) => {
    for (const company of ['12345', '---', '   ', '(+)']) {
      const res = await api.post(env.api.customers, { [KEY.customer.company]: company, [KEY.customer.contactName]: uniq('rn'), [KEY.customer.email]: `${uniq('rn')}@example.invalid` });
      expect([400, 422], `company "${company}"`).toContain(res.status());
    }
    const ok = await api.createCustomer({ company: `${uniq('rn')} 2`, contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` }); // a name with a letter still saves
    expect(ok.id).not.toBe('');
  });

  live('SEC-06', 'a customer contact cannot change the company name', async ({ request, api }) => {
    needs(env.fixtures.portalCustomerId, 'PORTAL_CUSTOMER_ID');
    const before = await api.get(fill(env.api.customer, env.fixtures.portalCustomerId));
    const company = (await before.json()) as Record<string, unknown>;
    const res = await request.put(personaApi(fill(env.api.customer, env.fixtures.portalCustomerId), env.portalUrl), { data: { [KEY.customer.company]: 'rn-renamed' } });
    expect(res.status(), 'rename by a customer contact').toBeGreaterThanOrEqual(400);
    const after = (await (await api.get(fill(env.api.customer, env.fixtures.portalCustomerId))).json()) as Record<string, unknown>;
    expect(JSON.stringify(after)).toBe(JSON.stringify(company)); // unchanged
  });

  live('SEC-07', 'customers can only see time logs for their own jobs', async ({ request, api, uniq }) => {
    needs(env.fixtures.portalCustomerId, 'PORTAL_CUSTOMER_ID');
    const own = await api.createJob(env.fixtures.portalCustomerId, uniq('rn-job'));
    const other = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const othersJob = await api.createJob(other.id, uniq('rn-job'));
    const mine = await request.get(personaApi(fill(env.api.jobTimeLogs, own), env.portalUrl));
    expect(mine.ok(), 'own job time logs').toBeTruthy();
    const theirs = await request.get(personaApi(fill(env.api.jobTimeLogs, othersJob), env.portalUrl));
    expect([403, 404], 'another customer\'s job time logs').toContain(theirs.status());
  });
});
