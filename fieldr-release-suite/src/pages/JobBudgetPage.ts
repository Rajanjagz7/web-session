import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

export class JobBudgetPage extends BasePage {
  async openJob(jobId: string): Promise<void> {
    await this.open(`${env.routes.jobs}/${encodeURIComponent(jobId)}`); // TODO(confirm): the job detail route shape
  }

  async openBudgetTab(): Promise<void> {
    await this.page.getByRole('tab', { name: /budget/i }).click(); // TODO(confirm)
  }

  line(name: string): Locator {
    return this.page.getByRole('row', { name }); // TODO(confirm): rows named by their item
  }
  sellPrice(lineName: string): Locator {
    return this.line(lineName).getByRole('spinbutton', { name: /sell price/i }); // TODO(confirm)
  }
  costPrice(lineName: string): Locator {
    return this.line(lineName).getByRole('spinbutton', { name: /cost price/i }); // TODO(confirm)
  }
  quantity(lineName: string): Locator {
    return this.line(lineName).getByRole('spinbutton', { name: /qty|quantity/i }); // TODO(confirm)
  }
  lineTotal(lineName: string): Locator {
    return this.line(lineName).getByTestId('line-total'); // TODO(confirm): test-id does not exist yet; ask dev to add it
  }
  get catalogueItemPicker(): Locator {
    return this.page.getByRole('combobox', { name: /catalogue item|item/i }); // TODO(confirm)
  }
  get jobBudgetTotal(): Locator {
    return this.page.getByTestId('job-budget-total'); // TODO(confirm)
  }
  get costBudgetTotal(): Locator {
    return this.page.getByTestId('cost-budget-total'); // TODO(confirm)
  }
  /** BUD-04 */
  get remainingBudgetTile(): Locator {
    return this.page.getByRole('group', { name: /job budget/i }); // TODO(confirm): tile landmark
  }
  /** JOB-03 */
  get linesOverPlannedQtyTile(): Locator {
    return this.page.getByRole('group', { name: 'Lines Over Planned Qty' });
  }
  get saveButton(): Locator {
    return this.page.getByRole('button', { name: /save/i });
  }
}
