import { type Locator } from '@playwright/test';
import { env } from '../lib/env';
import { BasePage } from './BasePage';

/**
 * Subscription, plan cards and Purchase History (SUB-*, SUBS-*). The tests that use it are test.fixme until a billing
 * sandbox with the needed subscription states exists (see docs/traceability-matrix.md); the locators are ready to fill in.
 */
export class SubscriptionPage extends BasePage {
  async openSubscription(): Promise<void> {
    await this.open(env.routes.subscription); // TODO: real route
  }
  async openPurchaseHistory(): Promise<void> {
    await this.open(env.routes.purchaseHistory); // TODO: real route
  }

  get currentSubscription(): Locator {
    return this.page.getByRole('region', { name: /current subscription/i }); // TODO: confirm accessible name
  }
  get planCards(): Locator {
    return this.page.getByRole('list', { name: /plans/i }).getByRole('listitem'); // TODO: confirm
  }
  get cancelCard(): Locator {
    return this.page.getByRole('region', { name: /cancel/i }); // TODO: confirm
  }
  get resumeButton(): Locator {
    return this.page.getByRole('button', { name: /resume/i }); // SUB-01 TODO: confirm label
  }
  get paymentRows(): Locator {
    return this.page.getByRole('row'); // SUB-02 / SUBS-02
  }
  chargeInterval(row: string | RegExp): Locator {
    return this.paymentRows.filter({ hasText: row }).filter({ hasText: /monthly|yearly/i }); // SUB-02 TODO: confirm how the interval is rendered
  }
  get alerts(): Locator {
    return this.page.getByRole('alert'); // SUBS-03
  }
}
