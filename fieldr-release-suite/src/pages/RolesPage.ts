import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

export class RolesPage extends BasePage {
  async openRoles(): Promise<void> {
    await this.open(env.routes.roles);
  }

  /** ROL-01 */
  get createMenuButton(): Locator {
    return this.page.getByRole('button', { name: 'Create' }); // TODO(confirm)
  }
  get newRoleMenuItem(): Locator {
    return this.page.getByRole('menuitem', { name: 'New Role' });
  }
  async openCommandPalette(): Promise<void> {
    await this.page.keyboard.press('ControlOrMeta+K'); // TODO(confirm): shortcut
  }
  get paletteInput(): Locator {
    return this.page.getByRole('combobox', { name: /command|search/i }); // TODO(confirm)
  }
  get paletteNewRoleOption(): Locator {
    return this.page.getByRole('option', { name: 'New Role' });
  }

  /** ROL-02 / ROL-03 : job Team step */
  get assignByRolePlus(): Locator {
    return this.page.getByRole('button', { name: /add role|new role|\+/i }); // TODO(confirm): the "+" button's accessible name
  }
  get assignByRoleSelect(): Locator {
    return this.page.getByRole('combobox', { name: /assign by role/i });
  }
  get newRoleDialog(): Locator {
    return this.dialog(/role/i);
  }
  get roleNameInput(): Locator {
    return this.newRoleDialog.getByLabel(/name/i);
  }
  get copyAccessFrom(): Locator {
    return this.newRoleDialog.getByLabel(/same access as|copy/i); // TODO(confirm)
  }
  get assignedPeople(): Locator {
    return this.page.getByRole('list', { name: /assigned|team/i }); // TODO(confirm)
  }

  /** USR-03 */
  get roleNameCells(): Locator {
    return this.page.getByRole('row').getByRole('link'); // TODO: fragile (role names rendered as links?) confirm
  }
  get roleNameSort(): Locator {
    return this.columnHeader(/role|name/i);
  }
}
