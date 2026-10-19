import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class LoginPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  usernameInput = () => this.page.getByPlaceholder('Username');
  passwordInput = () => this.page.getByPlaceholder('Password');
  submitBtn = () => this.page.getByRole('button', { name: 'Login' });
  errorMessage = () => this.page.getByTestId('error');

  async fillUsername(username: string): Promise<void> {
    await this.usernameInput().fill(username);
  }

  async fillPassword(password: string): Promise<void> {
    await this.passwordInput().fill(password);
  }

  async clickSubmit(): Promise<void> {
    await this.submitBtn().click();
  }

  async getErrorText(): Promise<string> {
    return (await this.errorMessage().textContent()) ?? '';
  }
}
