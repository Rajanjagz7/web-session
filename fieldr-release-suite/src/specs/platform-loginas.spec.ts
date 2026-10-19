import { env } from '../config/env';
import { expect, fixme, live, manual, test } from '../fixtures/test';
import { CustomersPage } from '../pages/CustomersPage';
import { PlatformAdminPage } from '../pages/PlatformAdminPage';

/** Release notes: Platform Admin (PLT-01..05), Admin "Log In As" (LIA-01) and BUG-15. Runs on ADMIN_URL / BASE_URL as the super-admin. */
test.describe('@platform Platform admin console', () => {
  live('PLT-01', 'the overview loads once (one request per data source)', async ({ page }) => {
    const calls: string[] = [];
    page.on('request', (r) => {
      if (r.url().includes(env.api.adminOverview)) calls.push(r.url());
    });
    const admin = new PlatformAdminPage(page);
    await admin.openOverview();
    await expect(admin.main).toBeVisible();
    await page.waitForLoadState('networkidle'); // single bounded wait for the page to settle; replace with a "loaded" test-id when available
    expect(calls.length, `overview calls: ${calls.join(', ')}`).toBeLessThanOrEqual(1);
  });

  manual('PLT-02');

  live('PLT-03', 'the accounts list shows sorting, accounts with zero revenue and the 200-row limit notice', async ({ page }) => {
    const admin = new PlatformAdminPage(page);
    await admin.openAccounts();
    await expect(admin.sortButton(/revenue/i)).toBeVisible();
    await expect(admin.accountRows.filter({ hasText: /\$?0(\.00)?\b/ }).first()).toBeVisible(); // TODO: fragile; seed a zero-revenue account and match by name
    const rows = await admin.accountRows.count();
    if (rows >= 200) {
      await expect(admin.rowLimitNotice).toBeVisible();
      if (env.expected.accountsRowLimitText !== '') await expect(admin.rowLimitNotice).toContainText(env.expected.accountsRowLimitText);
    } else {
      test.info().annotations.push({ type: 'todo', description: `only ${rows} rows: the limit notice needs an environment with 200+ accounts` });
    }
  });

  fixme('PLT-04');

  live('PLT-05', 'role settings only offer super-admin modules to the Super Admin role', async ({ page }) => {
    const admin = new PlatformAdminPage(page);
    await admin.openRoleSettings();
    const superModules = await admin.roleModuleOptions('Super Admin').count(); // TODO(confirm): role names
    const adminModules = await admin.roleModuleOptions('Admin').count();
    expect(superModules, 'Super Admin has more modules').toBeGreaterThan(adminModules);
    // TODO: assert by module name (the notes do not list the super-admin-only modules).
  });
});

test.describe('@loginas Log In As', () => {
  live('LIA-01', 'a super admin logged in as a company admin can log in as one of that company\'s customers', async ({ page }) => {
    const admin = new PlatformAdminPage(page);
    await admin.openAccounts();
    await admin.logInAsButton(/./).first().click(); // step 1: log in as the company admin (TODO: pick a named seeded company)
    await expect(admin.loggedInAsBanner).toBeVisible();
    const customers = new CustomersPage(page);
    await customers.open(env.routes.customers);
    await customers.row(/./).first().getByRole('button', { name: /log in as/i }).click(); // step 2: log in as a customer
    await expect(admin.loggedInAsBanner).toBeVisible();
    // TODO: assert the portal opens for that customer (PORTAL_URL) and the banner names the customer.
  });

  // Negative: someone who is not a super admin must not get the option.
  live(
    'LIA-01',
    'the Log In As option is not offered to a user who is not a super admin',
    async ({ page }) => {
      const customers = new CustomersPage(page);
      await customers.openList();
      await expect(page.getByRole('button', { name: /log in as/i })).toHaveCount(0);
    },
    'no-permission',
  );

  live('BUG-15', 'the Log In As button is hidden while you are already logged in as someone else', async ({ page }) => {
    const admin = new PlatformAdminPage(page);
    await admin.openAccounts();
    await admin.logInAsButton(/./).first().click();
    await expect(admin.loggedInAsBanner).toBeVisible();
    const customers = new CustomersPage(page);
    await customers.openList();
    await expect(page.getByRole('button', { name: /log in as/i })).toHaveCount(0);
  });
});
