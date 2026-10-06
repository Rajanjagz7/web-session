import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

/** Selectors come from the accessibility tree observed on 2026-09-19. */
export class LoginPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  heading = () => this.page.getByRole('heading', { name: 'Welcome to Fieldr' });
  eyebrow = () => this.page.getByText(/secure login/i).first();
  helper = () => this.page.getByText("Log in with your mobile number or email. We'll send you a one-time passcode (OTP).");
  mobileTab = () => this.page.getByRole('button', { name: 'Mobile Number' });
  emailTab = () => this.page.getByRole('button', { name: 'Email Address' });
  form = () => this.page.locator('form');
  identifierInput = () => this.form().getByRole('textbox').first();
  countryButton = () => this.page.getByRole('button', { name: /Australia/ });
  sendOtpBtn = () => this.page.getByRole('button', { name: 'Send OTP' });
  termsLink = () => this.page.getByRole('link', { name: 'Terms & Conditions' });
  privacyLink = () => this.page.getByRole('link', { name: 'Privacy Policy' });

  otpHeading = () => this.page.getByRole('heading', { name: 'Check Your Messages' });
  otpSentTo = () => this.page.getByText('We sent a 6-digit OTP to');
  otpDigit = (index: number) => this.page.getByRole('textbox', { name: `Digit ${index}` });
  verifyBtn = () => this.page.getByRole('button', { name: 'Verify & Login' });
  resendBtn = () => this.page.getByRole('button', { name: 'Resend OTP', exact: true });
  resendTimer = () => this.page.getByText(/Resend OTP in \d+s/);
  changeIdentifierBtn = () => this.page.getByRole('button', { name: 'Use a different number or email' });

  async open(): Promise<void> {
    await this.navigate('/login');
  }

  async clickMobileTab(): Promise<void> {
    await this.mobileTab().click();
  }

  async clickEmailTab(): Promise<void> {
    await this.emailTab().click();
  }

  async fillIdentifier(value: string): Promise<void> {
    await this.identifierInput().fill(value);
  }

  async clickSendOtp(): Promise<void> {
    await this.sendOtpBtn().click();
  }

  async fillOtpDigit(index: number, value: string): Promise<void> {
    await this.otpDigit(index).fill(value);
  }

  async typeIntoOtpDigit(index: number, value: string): Promise<void> {
    await this.otpDigit(index).pressSequentially(value);
  }

  async clickVerify(): Promise<void> {
    await this.verifyBtn().click();
  }

  async clickResend(): Promise<void> {
    await this.resendBtn().click();
  }

  async clickChangeIdentifier(): Promise<void> {
    await this.changeIdentifierBtn().click();
  }

  async pressTab(): Promise<void> {
    await this.page.keyboard.press('Tab');
  }
}
