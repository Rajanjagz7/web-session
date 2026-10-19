import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

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
