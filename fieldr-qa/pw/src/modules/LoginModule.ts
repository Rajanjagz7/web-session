import { Page, Response, expect } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';
import { DashboardPage } from '@pages/DashboardPage';
import { Logger } from '@utils/Logger';
import { config } from '@config/index';

export class LoginModule {
  private readonly logger = new Logger('LoginModule');

  constructor(
    private readonly page: Page,
    private readonly loginPage: LoginPage,
    private readonly dashboardPage: DashboardPage,
  ) {}

  async requestOtpForMobile(national: string): Promise<void> {
    this.logger.info(`Requesting OTP for mobile ending ${national.slice(-3)}`);
    await this.loginPage.open();
    await this.loginPage.clickMobileTab();
    await this.loginPage.fillIdentifier(national);
    await this.loginPage.clickSendOtp();
    await expect(this.loginPage.otpHeading()).toBeVisible({ timeout: config.timeouts.network });
  }

  async enterOtp(code: string): Promise<void> {
    for (let i = 0; i < code.length; i += 1) {
      await this.loginPage.fillOtpDigit(i + 1, code[i]);
    }
  }

  async loginWithMobile(national: string = config.mobile, otp: string = config.otp): Promise<void> {
    await this.requestOtpForMobile(national);
    await this.enterOtp(otp);
    await expect(this.loginPage.verifyBtn()).toBeEnabled();
    await this.loginPage.clickVerify();
    await this.expectOnDashboard();
  }

  async loginWithEmail(email: string, otp: string = config.otp): Promise<void> {
    this.logger.info('Requesting OTP by email');
    await this.loginPage.open();
    await this.loginPage.clickEmailTab();
    await this.loginPage.fillIdentifier(email);
    await this.loginPage.clickSendOtp();
    await expect(this.loginPage.otpHeading()).toBeVisible({ timeout: config.timeouts.network });
    await this.enterOtp(otp);
    await this.loginPage.clickVerify();
    await this.expectOnDashboard();
  }

  /** Click Send OTP and return the API response it triggered. */
  async sendOtpCapturing(): Promise<Response> {
    const [response] = await Promise.all([
      this.page.waitForResponse((r) => r.request().method() === 'POST', { timeout: config.timeouts.network }),
      this.loginPage.clickSendOtp(),
    ]);
    return response;
  }

  /** Click Verify & Login and return the API response it triggered. */
  async verifyCapturing(): Promise<Response> {
    const [response] = await Promise.all([
      this.page.waitForResponse((r) => r.request().method() === 'POST', { timeout: config.timeouts.network }),
      this.loginPage.clickVerify(),
    ]);
    return response;
  }

  /** Fill the identifier and click Send OTP only if the button is enabled. Returns whether it was clicked. */
  async trySendIdentifier(value: string): Promise<boolean> {
    await this.loginPage.fillIdentifier(value);
    const enabled = await this.loginPage.sendOtpBtn().isEnabled();
    if (enabled) await this.loginPage.clickSendOtp();
    return enabled;
  }

  async expectOnDashboard(): Promise<void> {
    await expect(this.page).toHaveURL(/\/app\/dashboard/, { timeout: config.timeouts.network });
    await expect(this.dashboardPage.heading()).toBeVisible({ timeout: config.timeouts.network });
  }

  async expectStillOnIdentifierStep(): Promise<void> {
    await expect(this.loginPage.otpHeading()).toBeHidden({ timeout: config.timeouts.ui });
    await expect(this.page).toHaveURL(/\/login/);
  }

  async logout(): Promise<void> {
    await this.dashboardPage.clickUserMenu();
    await this.dashboardPage.clickLogout();
    await expect(this.page).toHaveURL(/\/login/, { timeout: config.timeouts.network });
  }
}
