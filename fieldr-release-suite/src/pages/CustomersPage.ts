import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

export class CustomersPage extends BasePage {
  async openList(): Promise<void> {
    await this.open(env.routes.customers);
  }
  async openDetails(customerId: string): Promise<void> {
    await this.open(`${env.routes.customers}/${encodeURIComponent(customerId)}`); // TODO(confirm): route shape
  }

  get searchBox(): Locator {
    return this.page.getByRole('searchbox'); // TODO(confirm): may be a textbox named Search
  }
  get rows(): Locator {
    return this.page.getByRole('row');
  }
  row(text: string | RegExp): Locator {
    return this.page.getByRole('row', { name: text });
  }

  /** CUS-01 / CUS-02 / JOB-04 */
  get createJobButton(): Locator {
    return this.page.getByRole('button', { name: 'Create Job' });
  }

  /** CUS-03e : portal access screen */
  get portalAccessSection(): Locator {
    return this.page.getByRole('region', { name: /portal access/i }); // TODO(confirm)
  }

  /** SEC-05 / SEC-06 */
  get companyNameInput(): Locator {
    return this.page.getByLabel(/company name/i);
  }
  get saveButton(): Locator {
    return this.page.getByRole('button', { name: /save/i });
  }
}
