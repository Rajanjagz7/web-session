import { Page, expect } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';
import { Logger } from '@utils/Logger';
import { config } from '@config/index';

export class LoginModule {
  private logger = new Logger('LoginModule');

  constructor(
    private page: Page,
    private loginPage: LoginPage,
  ) {}

  async doLogin(
    username: string = config.credentials.username,
    password: string = config.credentials.password,
  ): Promise<void> {
    this.logger.info(`Logging in as: ${username}`);
    await this.loginPage.navigate('/');
    await this.loginPage.fillUsername(username);
    await this.loginPage.fillPassword(password);
    await this.loginPage.clickSubmit();
    this.logger.info('Login submitted');
  }

  async verifyLoggedIn(): Promise<void> {
    await expect(this.page).toHaveURL(/inventory\.html/);
  }

  async verifyLoginFailed(expectedError: string): Promise<void> {
    await expect(this.loginPage.errorMessage()).toBeVisible();
    const errorText = await this.loginPage.getErrorText();
    expect(errorText).toContain(expectedError);
    this.logger.warn(`Login failed as expected: ${expectedError}`);
  }

  async verifyErrorCleared(): Promise<void> {
    await expect(this.loginPage.errorMessage()).toBeHidden();
  }
}
