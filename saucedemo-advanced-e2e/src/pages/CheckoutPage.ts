import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class CheckoutPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Step one: information
  firstNameInput = () => this.page.getByTestId('firstName');
  lastNameInput = () => this.page.getByTestId('lastName');
  postalCodeInput = () => this.page.getByTestId('postalCode');
  continueBtn = () => this.page.getByTestId('continue');
  cancelBtn = () => this.page.getByTestId('cancel');
  errorMessage = () => this.page.getByTestId('error');

  // Step two: overview
  subtotalLabel = () => this.page.getByTestId('subtotal-label');
  taxLabel = () => this.page.getByTestId('tax-label');
  totalLabel = () => this.page.getByTestId('total-label');
  finishBtn = () => this.page.getByTestId('finish');

  // Complete
  completeHeader = () => this.page.getByTestId('complete-header');

  async fillFirstName(value: string): Promise<void> {
    await this.firstNameInput().fill(value);
  }

  async fillLastName(value: string): Promise<void> {
    await this.lastNameInput().fill(value);
  }

  async fillPostalCode(value: string): Promise<void> {
    await this.postalCodeInput().fill(value);
  }

  async clickContinue(): Promise<void> {
    await this.continueBtn().click();
  }

  async clickCancel(): Promise<void> {
    await this.cancelBtn().click();
  }

  async clickFinish(): Promise<void> {
    await this.finishBtn().click();
  }

  async getErrorText(): Promise<string> {
    return (await this.errorMessage().textContent()) ?? '';
  }

  async getSubtotalText(): Promise<string> {
    return (await this.subtotalLabel().textContent()) ?? '';
  }

  async getTaxText(): Promise<string> {
    return (await this.taxLabel().textContent()) ?? '';
  }

  async getTotalText(): Promise<string> {
    return (await this.totalLabel().textContent()) ?? '';
  }

  async getCompleteHeaderText(): Promise<string> {
    return (await this.completeHeader().textContent()) ?? '';
  }
}
