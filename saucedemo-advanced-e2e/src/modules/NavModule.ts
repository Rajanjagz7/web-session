import { Page, expect } from '@playwright/test';
import { NavPage } from '@pages/NavPage';
import { Logger } from '@utils/Logger';

export class NavModule {
  private logger = new Logger('NavModule');

  constructor(
    private page: Page,
    private navPage: NavPage,
  ) {}

  async logout(): Promise<void> {
    this.logger.info('Logging out');
    await this.navPage.clickMenuButton();
    await this.navPage.clickLogout();
    await expect(this.page).toHaveURL('https://www.saucedemo.com/');
  }
}
