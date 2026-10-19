import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

/** Platform admin console (ADMIN_URL) plus the "Log In As" controls (LIA-01, BUG-15). */
export class PlatformAdminPage extends BasePage {
  async openOverview(): Promise<void> {
    await this.open(env.routes.adminOverview, env.adminUrl);
  }
  async openAccounts(): Promise<void> {
    await this.open(env.routes.adminAccounts, env.adminUrl);
  }
  async openRoleSettings(): Promise<void> {
    await this.open(env.routes.adminRoles, env.adminUrl);
  }

  /** PLT-03 */
  get accountRows(): Locator {
    return this.page.getByRole('row');
  }
  sortButton(column: string | RegExp): Locator {
    return this.page.getByRole('columnheader', { name: column }).getByRole('button'); // TODO(confirm)
  }
  get rowLimitNotice(): Locator {
    return this.page.getByRole('status', { name: /200|limit/i }); // TODO(confirm): role of the notice
  }

  /** PLT-05 */
  roleModuleOptions(roleName: string): Locator {
    return this.page.getByRole('region', { name: roleName }).getByRole('checkbox'); // TODO(confirm)
  }

  /** LIA-01 / BUG-15 */
  logInAsButton(name: string | RegExp): Locator {
    return this.page.getByRole('button', { name: /log in as/i }).filter({ hasText: name }); // TODO(confirm)
  }
  get loggedInAsBanner(): Locator {
    return this.page.getByRole('banner').getByText(/logged in as/i); // TODO(confirm)
  }
}
