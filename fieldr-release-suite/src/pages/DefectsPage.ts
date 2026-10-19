import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

/** BUG-03: title and description edits must survive closing the menu. */
export class DefectsPage extends BasePage {
  async openJobDefects(jobId: string): Promise<void> {
    await this.open(`${env.routes.jobs}/${encodeURIComponent(jobId)}/defects`); // TODO(confirm): route
  }
  get addDefect(): Locator {
    return this.page.getByRole('button', { name: /add defect/i });
  }
  get menu(): Locator {
    return this.dialog(/defect/i); // TODO(confirm): menu may be a drawer/dialog
  }
  get title(): Locator {
    return this.menu.getByLabel(/title/i);
  }
  get description(): Locator {
    return this.menu.getByLabel(/description/i);
  }
  get close(): Locator {
    return this.menu.getByRole('button', { name: /close/i });
  }
  defectRow(title: string): Locator {
    return this.page.getByRole('row', { name: title });
  }
}
