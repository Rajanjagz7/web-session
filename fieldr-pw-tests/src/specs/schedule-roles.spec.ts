/**
 * Release notes: New Features > Schedule and Roles; Improvements > Users (Roles & Permissions order).
 * IDs in this file: RO-01, RO-02, RO-03, SC-01, SC-02, SC-03, USR-03
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { expect, test } from '../fixtures/data.fixture';
import { env, personaApi } from '../lib/env';
import { RolesPage } from '../pages/RolesPage';
import { SchedulePage } from '../pages/SchedulePage';

// TODO: the notes say today 9am-5pm; the time format shown in the fields is unconfirmed.
const NINE_AM = /\b0?9(:00)?\s*(am)?\b/i;
const FIVE_PM = /\b(0?5|17)(:00)?\s*(pm)?\b/i;

test.describe('@roles Roles', () => {
  test('[RO-01] @roles @super-admin New Role is in the Create menu and the command palette for a user who can manage roles', async ({ page }) => {
    const roles = new RolesPage(page);
    await roles.openRoles();
    await roles.createMenuButton.click();
    await expect(roles.newRoleMenuItem).toBeVisible();
    await page.keyboard.press('Escape');
    await roles.openCommandPalette();
    await roles.paletteInput.fill('New Role');
    await expect(roles.paletteNewRoleOption).toBeVisible();
    // TODO: the "plan includes custom roles" half needs a company on a plan without custom roles; add a persona/company for it.
  });

  test('[RO-01] @roles @no-permission New Role is absent for a user who cannot manage roles, and the roles API refuses creation',     async ({ page, request, uniq }) => {
      const roles = new RolesPage(page);
      await page.goto(env.baseUrl);
      await roles.createMenuButton.click().catch(() => undefined); // the Create menu may itself be absent
      await expect(roles.newRoleMenuItem).toHaveCount(0);
      await page.keyboard.press('Escape');
      await roles.openCommandPalette();
      await expect(roles.paletteNewRoleOption).toHaveCount(0);
      const res = await request.post(personaApi(env.api.roles), { data: { name: uniq('rn-role') } }); // TODO(confirm): payload key
      expect(res.status(), 'role creation without permission').toBe(403);
  });

  test('[RO-02] @roles @super-admin the "+" next to Assign By Role creates a role with the same access as an existing role', async ({ page, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await data.seedJob(customer.id, uniq('rn-job'));
    const roles = new RolesPage(page);
    await roles.open(`${env.routes.jobs}/${encodeURIComponent(jobId)}`); // TODO(confirm): then navigate to the Team step
    await page.getByRole('tab', { name: /team/i }).click(); // TODO(confirm)
    await roles.assignByRolePlus.click();
    const name = uniq('rn-role');
    await roles.roleNameInput.fill(name);
    await roles.copyAccessFrom.selectOption({ index: 1 }); // TODO(confirm): control type
    await page.getByRole('button', { name: /create|save/i }).click();
    const res = await data.get(env.api.roles);
    expect(await res.text(), 'the new role exists').toContain(name);
    // TODO: compare the new role's permissions with the source role through the roles API once the response shape is confirmed.
  });

  test('[RO-03] @roles @super-admin the new role is selected straight away and adds nobody to the job', async ({ page, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await data.seedJob(customer.id, uniq('rn-job'));
    const roles = new RolesPage(page);
    await roles.open(`${env.routes.jobs}/${encodeURIComponent(jobId)}`);
    await page.getByRole('tab', { name: /team/i }).click(); // TODO(confirm)
    const peopleBefore = await roles.assignedPeople.getByRole('listitem').count();
    await roles.assignByRolePlus.click();
    const name = uniq('rn-role');
    await roles.roleNameInput.fill(name);
    await page.getByRole('button', { name: /create|save/i }).click();
    await expect(roles.assignByRoleSelect).toContainText(name);
    expect(await roles.assignedPeople.getByRole('listitem').count()).toBe(peopleBefore);
  });
});

test.describe('@schedule Schedule', () => {
  test('[SC-01] @schedule @super-admin Add Shift and Add User buttons exist and Add Shift opens on today 9am-5pm', async ({ page }) => {
    const schedule = new SchedulePage(page);
    await schedule.openSchedule();
    await expect(schedule.addUserButton).toBeVisible();
    await schedule.addShiftButton.click();
    await expect(schedule.shiftDialog).toBeVisible();
    await expect(schedule.shiftStart).toHaveValue(NINE_AM);
    await expect(schedule.shiftEnd).toHaveValue(FIVE_PM);
    // TODO: also assert the date field is today. The displayed date format is unconfirmed; compare against a clock-mocked date (page.clock).
  });

  test('[SC-02] @schedule @super-admin Add User opens a quick popup and the Schedule stays open behind it', async ({ page }) => {
    const schedule = new SchedulePage(page);
    await schedule.openSchedule();
    const before = page.url();
    await schedule.addUserButton.click();
    await expect(schedule.userDialog).toBeVisible();
    expect(page.url()).toBe(before);
  });

  test('[SC-03] @schedule @super-admin after saving the new person, Add Shift opens for today 9am-5pm with them in the team', async ({ page, uniq }) => {
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

test.describe('@roles Users', () => {
  test('[USR-03] @roles @misc @super-admin Roles & Permissions opens sorted A-Z by role name', async ({ page }) => {
    const roles = new RolesPage(page);
    await roles.openRoles();
    const names = (await roles.roleNameCells.allInnerTexts()).map((t) => t.trim()).filter((t) => t !== '');
    expect(names.length, 'at least two roles to compare').toBeGreaterThan(1);
    const sorted = [...names].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
    expect(names).toEqual(sorted);
    // TODO: click the Role header and assert Z-A, then A-Z again.
  });
});
