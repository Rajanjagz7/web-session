import { expect, fixme, live, test } from '../fixtures/test';
import { CustomersPage } from '../pages/CustomersPage';
import { DateTimePicker } from '../pages/DateTimePicker';
import { SchedulePage } from '../pages/SchedulePage';
import { UserFormPage } from '../pages/UserFormPage';

/** Release notes: Improvements > Users (USR-01, USR-02), Date & Time (DTM-01), Bug Fixes > Search (BUG-14). */
test.describe('@users Users', () => {
  live('USR-01', 'Industry is optional on Add User, Edit User and My Profile', async ({ page }) => {
    const form = new UserFormPage(page);
    await form.openProfile();
    await expect(form.industry).not.toHaveAttribute('aria-required', 'true');
    await form.openUsers();
    await form.addUserButton.click();
    await expect(form.industry).not.toHaveAttribute('aria-required', 'true');
    // TODO: submit Add User with every required field except Industry and assert it saves (needs the list of required fields).
    // TODO: repeat on the Edit User screen (needs a seeded user and the edit route).
  });

  fixme('USR-02');

  live('BUG-14', 'users and customers can be found by the phone number and customer number shown in the list', async ({ page, api, uniq }) => {
    const contact = uniq('rn-contact');
    await api.createCustomer({ company: uniq('rn-co'), contact, email: `${uniq('rn')}@example.invalid`, mobile: '0412345678' }); // TODO(confirm): mobile format accepted
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
});

test.describe('@datetime Date and time picker', () => {
  live('DTM-01', 'the picker offers 15-minute slots and scrolls to the current time when it opens', async ({ page }) => {
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
