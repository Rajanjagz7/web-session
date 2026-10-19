import { expect, type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

/** Locators below were confirmed from the accessibility tree recorded in fieldr-qa (2026-09-19); re-check after UI changes. */
export class LoginPage extends BasePage {
  get heading(): Locator {
    return this.page.getByRole('heading', { name: 'Welcome to Fieldr' });
  }
  get mobileTab(): Locator {
    return this.page.getByRole('button', { name: 'Mobile Number' });
  }
  get identifierInput(): Locator {
    return this.page.locator('form').getByRole('textbox').first(); // TODO: fragile (form scope); the input has no accessible name
  }
  get sendOtp(): Locator {
    return this.page.getByRole('button', { name: 'Send OTP' });
  }
  otpDigit(index: number): Locator {
    return this.page.getByRole('textbox', { name: `Digit ${index}` });
  }
  get verify(): Locator {
    return this.page.getByRole('button', { name: 'Verify & Login' });
  }
  /** BUG-16: the logo. TODO(confirm): accessible name of the logo image. */
  get logo(): Locator {
    return this.page.getByRole('img', { name: /fieldr/i });
  }
  /** BUG-07: error text that must not appear on portal login. */
  get deviceIdError(): Locator {
    return this.page.getByText('Device id is required');
  }

  async openLogin(base: string = env.baseUrl): Promise<void> {
    await this.open(env.routes.login, base);
    await expect(this.heading).toBeVisible();
  }

  async signInWithMobileAndOtp(mobile: string, otp: string): Promise<void> {
    await this.mobileTab.click();
    await this.identifierInput.click();
    await this.identifierInput.pressSequentially(mobile.replace(/^\+?61/, ''), { delay: 40 }); // the field pre-fills +61; fill() overwrites it
    await this.sendOtp.click();
    await expect(this.otpDigit(1)).toBeVisible();
    for (let i = 0; i < otp.length; i++) await this.otpDigit(i + 1).fill(otp.charAt(i));
    await this.verify.click();
  }

  async expectSignedIn(): Promise<void> {
    await expect(this.page).not.toHaveURL(new RegExp(`${env.routes.login}$`));
  }
}
