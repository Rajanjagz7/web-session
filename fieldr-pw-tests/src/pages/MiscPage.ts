import { type Locator, type Page } from '@playwright/test';
import { env } from '../lib/env';
import { BasePage } from './BasePage';

/** Misc improvements: job orders (ORD-*), user forms (USR-*), insights (INS-*), date-time picker (DT-01). */
export class JobOrderPage extends BasePage {
  async openNewOrder(): Promise<void> {
    await this.open(`${env.routes.jobs}/orders/new`); // TODO(confirm): job order route
  }

  /** ORD-01 */
  get mobileNumber(): Locator {
    return this.page.getByLabel('Mobile Number');
  }
  get oldPhoneLabel(): Locator {
    return this.page.getByLabel('Phone', { exact: true });
  }
  get siteContactName(): Locator {
    return this.page.getByLabel('Site Contact Name');
  }
  get oldSiteContactLabel(): Locator {
    return this.page.getByLabel('Site Contact', { exact: true });
  }

  /** ORD-03 */
  get addLine(): Locator {
    return this.page.getByRole('button', { name: 'Add Line' });
  }
  get lineRows(): Locator {
    return this.page.getByRole('row', { name: /line/i }); // TODO(confirm)
  }
  get submit(): Locator {
    return this.page.getByRole('button', { name: /save|submit|create/i });
  }
}


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


export class InsightsPage extends BasePage {
  async openInsights(): Promise<void> {
    await this.open(env.routes.insights);
  }
  /** INS-01 */
  get statusFilter(): Locator {
    return this.page.getByRole('combobox', { name: /status/i });
  }
  get customerFilter(): Locator {
    return this.page.getByRole('combobox', { name: /customer/i });
  }
  get workerFilter(): Locator {
    return this.page.getByRole('combobox', { name: /worker/i });
  }
  reportLink(name: string | RegExp): Locator {
    return this.page.getByRole('link', { name }); // TODO(confirm)
  }
  /** INS-02: a percentage on a card and the same figure in the table. */
  get cards(): Locator {
    return this.page.getByRole('group'); // TODO(confirm): card landmark
  }
  get tableCells(): Locator {
    return this.page.getByRole('cell');
  }
}


/** DTM-01. TODO(confirm): the picker exposes its slots as role="option" inside a listbox. */
export class DateTimePicker {
  constructor(private readonly page: Page, private readonly label: string | RegExp) {}

  get input(): Locator {
    return this.page.getByLabel(this.label);
  }
  get slots(): Locator {
    return this.page.getByRole('listbox').getByRole('option');
  }
  async open(): Promise<void> {
    await this.input.click();
  }
  /** Slot labels, e.g. ["12:00 am", "12:15 am", ...]. Parsing is done in the spec. */
  async slotLabels(): Promise<string[]> {
    return this.slots.allInnerTexts();
  }
}
