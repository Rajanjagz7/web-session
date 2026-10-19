import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

/** Add User, Edit User and My Profile share these fields (USR-01, USR-02, BUG-14). */
export class UserFormPage extends BasePage {
  async openProfile(): Promise<void> {
    await this.open(env.routes.profile);
  }
  async openUsers(): Promise<void> {
    await this.open(env.routes.users);
  }
  get addUserButton(): Locator {
    return this.page.getByRole('button', { name: /add user/i });
  }
  get industry(): Locator {
    return this.page.getByLabel(/industry/i);
  }
  /** A field marked required exposes aria-required or a required asterisk in its label. */
  get industryLabel(): Locator {
    return this.page.getByText(/industry/i).first(); // TODO: fragile; prefer asserting aria-required on the input
  }
  get firstName(): Locator {
    return this.page.getByLabel(/first name/i);
  }
  get lastName(): Locator {
    return this.page.getByLabel(/last name/i);
  }
  get email(): Locator {
    return this.page.getByLabel(/email/i);
  }
  get mobile(): Locator {
    return this.page.getByLabel(/mobile|phone/i);
  }
  get addressSearch(): Locator {
    return this.page.getByRole('combobox', { name: /address/i }); // TODO(confirm): Google Places input
  }
  get suburb(): Locator {
    return this.page.getByLabel(/suburb/i);
  }
  get state(): Locator {
    return this.page.getByLabel(/state/i);
  }
  get postcode(): Locator {
    return this.page.getByLabel(/postcode/i);
  }
  get save(): Locator {
    return this.page.getByRole('button', { name: /save/i });
  }
  get searchBox(): Locator {
    return this.page.getByRole('searchbox'); // TODO(confirm)
  }
}
