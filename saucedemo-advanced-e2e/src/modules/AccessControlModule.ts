import { Page, expect } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';
import { Logger } from '@utils/Logger';

export class AccessControlModule {
  private logger = new Logger('AccessControlModule');

  constructor(
    private page: Page,
    private loginPage: LoginPage,
  ) {}

  async verifyBlockedWhenUnauthenticated(path: string): Promise<void> {
    this.logger.info(`Verifying unauthenticated access is blocked for ${path}`);
    await this.loginPage.navigate(path);
    await expect(this.loginPage.errorMessage()).toContainText(
      `You can only access '${path}' when you are logged in.`,
    );
  }
}
