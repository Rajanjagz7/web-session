import { expect, fixme, live, test } from '../fixtures/test';
import { InvitesPage } from '../pages/InvitesPage';
import { expectNoLabelViolations } from '../utils/a11y';

/** Release notes: Improvements > Customer Invites (INV-01..07) and Bug Fixes > Invites (BUG-09a/09b). */
test.describe('@invites Customer invites', () => {
  live('INV-01', 'the customer invite details step asks company name, address (required) and notes, with no staff fields', async ({ page, api, uniq }) => {
    const { link } = await api.createInvite('customer', `${uniq('rn')}@example.invalid`);
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

  live('INV-02', 'opening a customer invite while signed in as staff does not ask you to sign out', async ({ page, api, uniq }) => {
    const { link } = await api.createInvite('customer', `${uniq('rn')}@example.invalid`);
    test.skip(link === undefined, 'reason: the create-invite response has no link field; set KEY.invite.link in src/config/payloads.ts');
    await page.goto(link ?? '');
    await expect(page.getByRole('button', { name: /sign out|log out/i })).toHaveCount(0);
    await expect(page.getByText(/sign out/i)).toHaveCount(0);
    await expect(new InvitesPage(page).companyName).toBeVisible();
  });

  fixme('INV-03');

  live('INV-04', '"Your sign-in email" now reads "Your registration email"', async ({ page, api, uniq }) => {
    const { link } = await api.createInvite('customer', `${uniq('rn')}@example.invalid`);
    test.skip(link === undefined, 'reason: the create-invite response has no link field; set KEY.invite.link in src/config/payloads.ts');
    await page.goto(link ?? '');
    const invites = new InvitesPage(page);
    await expect(invites.registrationEmailLabel).toBeVisible();
    await expect(invites.oldSignInEmailLabel).toHaveCount(0);
  });

  live('INV-05', 'the "waiting" count does not shrink while you search', async ({ page, api, uniq }) => {
    const emails = [1, 2, 3].map(() => `${uniq('rn')}@example.invalid`);
    for (const email of emails) await api.createInvite('customer', email);
    const invites = new InvitesPage(page);
    await invites.openInvites();
    const readCount = async (): Promise<number> => Number(((await invites.waitingCount.innerText()).match(/\d+/) ?? ['NaN'])[0]);
    const before = await readCount();
    expect(before).toBeGreaterThanOrEqual(3);
    await invites.searchBox.fill(emails[0] ?? '');
    await expect(invites.rows.filter({ hasText: emails[0] ?? '' })).toHaveCount(1);
    expect(await readCount()).toBe(before);
  });

  live('INV-06', 'the invite dialog and its buttons have accessible names (automated part)', async ({ page }) => {
    const invites = new InvitesPage(page);
    await invites.openInvites();
    await invites.inviteButton.click();
    await expect(invites.inviteDialog).toBeVisible();
    await expect(invites.inviteDialog).toHaveAccessibleName(/./);
    for (const button of await invites.inviteDialog.getByRole('button').all()) await expect(button).toHaveAccessibleName(/./);
    await expectNoLabelViolations(page, invites.inviteDialog);
    // MANUAL: screen-reader announcement order, focus return on close and live-region behaviour need a real screen reader.
  });

  live('INV-07', 'inviting a customer\'s email as staff explains why instead of saying "already a member"', async ({ page, api, uniq }) => {
    const email = `${uniq('rn')}@example.invalid`;
    await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email });
    const invites = new InvitesPage(page);
    await invites.openInvites();
    await invites.inviteButton.click(); // TODO(confirm): choose the "staff" invite type in the dialog
    await invites.emailInput.fill(email);
    await invites.sendInviteButton.click();
    await expect(invites.alert).toBeVisible();
    await expect(invites.alert).not.toContainText(/already a member/i);
    await expect(invites.alert).toContainText(/customer/i); // TODO(confirm): exact wording
  });

  fixme('BUG-09a');

  live('BUG-09b', 'a missing email on an invite gives a clear error', async ({ page }) => {
    const invites = new InvitesPage(page);
    await invites.openInvites();
    await invites.inviteButton.click();
    await invites.sendInviteButton.click();
    await expect(invites.alert.or(invites.inviteDialog.getByText(/email/i)).first()).toContainText(/email/i);
    await expect(page.getByRole('progressbar')).toHaveCount(0); // not left "hanging"
  });
});
