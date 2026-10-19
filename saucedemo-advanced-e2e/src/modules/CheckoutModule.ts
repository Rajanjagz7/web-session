import { Page, expect } from '@playwright/test';
import { CheckoutPage } from '@pages/CheckoutPage';
import { Logger } from '@utils/Logger';

export interface ShippingInfo {
  firstName: string;
  lastName: string;
  postalCode: string;
}

export class CheckoutModule {
  private logger = new Logger('CheckoutModule');

  constructor(
    private page: Page,
    private checkoutPage: CheckoutPage,
  ) {}

  async fillShippingInfo(info: ShippingInfo): Promise<void> {
    this.logger.info('Filling shipping information', info);
    await this.checkoutPage.fillFirstName(info.firstName);
    await this.checkoutPage.fillLastName(info.lastName);
    await this.checkoutPage.fillPostalCode(info.postalCode);
  }

  async continueToOverview(): Promise<void> {
    await this.checkoutPage.clickContinue();
  }

  async verifyOnOverviewStep(): Promise<void> {
    await expect(this.page).toHaveURL(/checkout-step-two\.html/);
  }

  async verifyValidationError(expectedMessage: string): Promise<void> {
    await expect(this.checkoutPage.errorMessage()).toBeVisible();
    const text = await this.checkoutPage.getErrorText();
    expect(text).toContain(expectedMessage);
  }

  async verifyTotalsConsistent(): Promise<void> {
    const parse = (text: string) => parseFloat(text.replace(/[^0-9.]/g, ''));
    const subtotal = parse(await this.checkoutPage.getSubtotalText());
    const tax = parse(await this.checkoutPage.getTaxText());
    const total = parse(await this.checkoutPage.getTotalText());
    expect(total).toBeCloseTo(subtotal + tax, 2);
    this.logger.info(`Totals verified: ${subtotal} + ${tax} = ${total}`);
  }

  async completeOrder(): Promise<string> {
    await this.checkoutPage.clickFinish();
    await expect(this.page).toHaveURL(/checkout-complete\.html/);
    const confirmation = await this.checkoutPage.getCompleteHeaderText();
    this.logger.info(`Order completed: ${confirmation}`);
    return confirmation;
  }

  async cancel(): Promise<void> {
    await this.checkoutPage.clickCancel();
  }
}
