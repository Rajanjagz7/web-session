import { type Locator } from '@playwright/test';
import { env } from '../lib/env';
import { BasePage } from './BasePage';

export class SchedulePage extends BasePage {
  async openSchedule(): Promise<void> {
    await this.open(env.routes.schedule);
  }

  /** SCH-01 */
  get addShiftButton(): Locator {
    return this.page.getByRole('button', { name: 'Add Shift' });
  }
  get addUserButton(): Locator {
    return this.page.getByRole('button', { name: 'Add User' });
  }

  get shiftDialog(): Locator {
    return this.dialog(/shift/i); // TODO(confirm)
  }
  get shiftStart(): Locator {
    return this.shiftDialog.getByLabel(/start/i); // TODO(confirm)
  }
  get shiftEnd(): Locator {
    return this.shiftDialog.getByLabel(/end/i); // TODO(confirm)
  }
  get shiftTeam(): Locator {
    return this.shiftDialog.getByRole('listbox', { name: /team|assignees/i }); // TODO(confirm)
  }

  /** SCH-02 / SCH-03 */
  get userDialog(): Locator {
    return this.dialog(/user/i); // TODO(confirm)
  }
  userField(label: string | RegExp): Locator {
    return this.userDialog.getByLabel(label);
  }
  get saveUser(): Locator {
    return this.userDialog.getByRole('button', { name: /save|add user/i }); // TODO(confirm)
  }
}
