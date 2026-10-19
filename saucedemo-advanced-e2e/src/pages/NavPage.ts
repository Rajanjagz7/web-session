import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class NavPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  menuButton = () => this.page.getByRole('button', { name: 'Open Menu' });
  closeMenuButton = () => this.page.getByRole('button', { name: 'Close Menu' });
  logoutLink = () => this.page.getByTestId('logout-sidebar-link');
  resetLink = () => this.page.getByTestId('reset-sidebar-link');

  async clickMenuButton(): Promise<void> {
    await this.menuButton().click();
  }

  async clickLogout(): Promise<void> {
    await this.logoutLink().click();
  }

  async clickReset(): Promise<void> {
    await this.resetLink().click();
  }
}
