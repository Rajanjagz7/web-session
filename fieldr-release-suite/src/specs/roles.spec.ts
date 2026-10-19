import { env, personaApi } from '../config/env';
import { expect, live, test } from '../fixtures/test';
import { RolesPage } from '../pages/RolesPage';

/** Release notes: New Features > Roles (ROL-01..03) and Improvements > Users (USR-03). */
test.describe('@roles Roles', () => {
  live('ROL-01', 'New Role is in the Create menu and the command palette for a user who can manage roles', async ({ page }) => {
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

  // Negative: without role-management permission the entry points are absent and the API refuses.
  live(
    'ROL-01',
    'New Role is absent for a user who cannot manage roles, and the roles API refuses creation',
    async ({ page, request, uniq }) => {
      const roles = new RolesPage(page);
      await page.goto(env.baseUrl);
      await roles.createMenuButton.click().catch(() => undefined); // the Create menu may itself be absent
      await expect(roles.newRoleMenuItem).toHaveCount(0);
      await page.keyboard.press('Escape');
      await roles.openCommandPalette();
      await expect(roles.paletteNewRoleOption).toHaveCount(0);
      const res = await request.post(personaApi(env.api.roles), { data: { name: uniq('rn-role') } }); // TODO(confirm): payload key
      expect(res.status(), 'role creation without permission').toBe(403);
    },
    'no-permission',
  );

  live('ROL-02', 'the "+" next to Assign By Role creates a role with the same access as an existing role', async ({ page, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await api.createJob(customer.id, uniq('rn-job'));
    const roles = new RolesPage(page);
    await roles.open(`${env.routes.jobs}/${encodeURIComponent(jobId)}`); // TODO(confirm): then navigate to the Team step
    await page.getByRole('tab', { name: /team/i }).click(); // TODO(confirm)
    await roles.assignByRolePlus.click();
    const name = uniq('rn-role');
    await roles.roleNameInput.fill(name);
    await roles.copyAccessFrom.selectOption({ index: 1 }); // TODO(confirm): control type
    await page.getByRole('button', { name: /create|save/i }).click();
    const res = await api.get(env.api.roles);
    expect(await res.text(), 'the new role exists').toContain(name);
    // TODO: compare the new role's permissions with the source role through the roles API once the response shape is confirmed.
  });

  live('ROL-03', 'the new role is selected straight away and adds nobody to the job', async ({ page, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await api.createJob(customer.id, uniq('rn-job'));
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

  live('USR-03', 'Roles & Permissions opens sorted A-Z by role name', async ({ page }) => {
    const roles = new RolesPage(page);
    await roles.openRoles();
    const names = (await roles.roleNameCells.allInnerTexts()).map((t) => t.trim()).filter((t) => t !== '');
    expect(names.length, 'at least two roles to compare').toBeGreaterThan(1);
    const sorted = [...names].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
    expect(names).toEqual(sorted);
    // TODO: click the Role header and assert Z-A, then A-Z again.
  });
});
