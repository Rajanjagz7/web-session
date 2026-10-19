import { type Locator } from '@playwright/test';
import { env } from '../lib/env';
import { BasePage } from './BasePage';

/** Customer portal (PORTAL_URL). */
export class PortalPage extends BasePage {
  async openQuotes(): Promise<void> {
    await this.open(env.routes.portalQuotes, env.portalUrl);
  }
  async openJobs(): Promise<void> {
    await this.open(env.routes.portalJobs, env.portalUrl);
  }

  /** POR-01 */
  get jobColumn(): Locator {
    return this.columnHeader('Job');
  }
  jobCell(quoteName: string | RegExp): Locator {
    return this.page.getByRole('row', { name: quoteName }).getByRole('cell').nth(0); // TODO: fragile (column index); ask dev for a test-id
  }

  /** POR-02 */
  statusBadge(quoteName: string | RegExp): Locator {
    return this.page.getByRole('row', { name: quoteName }).getByTestId('status-badge'); // TODO(confirm): badge test-id
  }
  get statusFilter(): Locator {
    return this.page.getByRole('combobox', { name: /status/i });
  }
  statusFilterOption(name: string | RegExp): Locator {
    return this.page.getByRole('option', { name });
  }

  /** POR-03 */
  get accessRemoved(): Locator {
    return this.page.getByRole('main').filter({ hasText: env.expected.portalAccessRemoved }); // TODO: confirm the message is inside main
  }

  /** POR-04 */
  get worklogReportLink(): Locator {
    return this.page.getByRole('link', { name: /worklog report/i }); // TODO(confirm): link vs button
  }

  /** BUG-07 */
  get deviceIdError(): Locator {
    return this.page.getByRole('main').filter({ hasText: 'Device id is required' });
  }
}
