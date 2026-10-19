import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

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
