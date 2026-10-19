import { expect, live, test } from '../fixtures/test';
import { SchedulePage } from '../pages/SchedulePage';

/** Release notes: New Features > Schedule (SCH-01..03). TODO: the notes say "today 9am-5pm"; the time format shown in the fields is unconfirmed. */
const NINE_AM = /\b0?9(:00)?\s*(am)?\b/i;
const FIVE_PM = /\b(0?5|17)(:00)?\s*(pm)?\b/i;

test.describe('@schedule Schedule', () => {
  live('SCH-01', 'Add Shift and Add User buttons exist and Add Shift opens on today 9am-5pm', async ({ page }) => {
    const schedule = new SchedulePage(page);
    await schedule.openSchedule();
    await expect(schedule.addUserButton).toBeVisible();
    await schedule.addShiftButton.click();
    await expect(schedule.shiftDialog).toBeVisible();
    await expect(schedule.shiftStart).toHaveValue(NINE_AM);
    await expect(schedule.shiftEnd).toHaveValue(FIVE_PM);
    // TODO: also assert the date field is today. The displayed date format is unconfirmed; compare against a clock-mocked date (page.clock).
  });

  live('SCH-02', 'Add User opens a quick popup and the Schedule stays open behind it', async ({ page }) => {
    const schedule = new SchedulePage(page);
    await schedule.openSchedule();
    const before = page.url();
    await schedule.addUserButton.click();
    await expect(schedule.userDialog).toBeVisible();
    expect(page.url()).toBe(before);
  });

  live('SCH-03', 'after saving the new person, Add Shift opens for today 9am-5pm with them in the team', async ({ page, uniq }) => {
    const schedule = new SchedulePage(page);
    await schedule.openSchedule();
    await schedule.addUserButton.click();
    const first = uniq('rn-first');
    await schedule.userField(/first name/i).fill(first);
    await schedule.userField(/last name/i).fill(uniq('rn-last'));
    await schedule.userField(/email/i).fill(`${uniq('rn')}@example.invalid`);
    // TODO: mobile / role fields that may be required by this popup are unconfirmed.
    await schedule.saveUser.click();
    await expect(schedule.shiftDialog).toBeVisible();
    await expect(schedule.shiftStart).toHaveValue(NINE_AM);
    await expect(schedule.shiftEnd).toHaveValue(FIVE_PM);
    await expect(schedule.shiftTeam).toContainText(first);
    // CLEANUP: the user created here is not tracked (no id is exposed). Names start with "rn-first"; delete them from Users.
  });
});
