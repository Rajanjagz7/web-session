import { Page, expect, Locator } from '@playwright/test';

export interface QuoteLineItem {
  sectionName: string;
  itemName?: string;
  description?: string;
  unit?: string;
  quantity?: string;
  rate?: string;
}

export class QuotePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async gotoList() {
    await this.page.goto('/app/quote/list');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async gotoNew() {
    await this.page.goto('/app/quote/new');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async clickAddQuote() {
    const addBtn = this.page.locator('button').filter({ hasText: /add quote/i });
    if (await addBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addBtn.click();
    } else {
      await this.gotoNew();
    }
  }

  async selectCustomer(customerName?: string) {
    const customerInput = this.page.locator('#react-select-4-input, [id^="react-select-"][id$="-input"]').first();
    await customerInput.waitFor({ state: 'visible', timeout: 10000 });
    await customerInput.focus();
    if (customerName) {
      await customerInput.fill(customerName);
      await this.page.waitForTimeout(400);
    }
    await this.page.keyboard.press('ArrowDown');
    await this.page.keyboard.press('Enter');
  }

  async clickNext() {
    const nextBtn = this.page.locator('button').filter({ hasText: /^next$/i });
    await nextBtn.scrollIntoViewIfNeeded();
    await nextBtn.click();
    await this.page.waitForTimeout(600);
  }

  async clickSave() {
    const saveBtn = this.page.locator('button').filter({ hasText: /^save$/i });
    await saveBtn.scrollIntoViewIfNeeded();
    await saveBtn.click();
  }

  async fillSectionDetails(item: QuoteLineItem) {
    // Fill Section Name
    if (item.sectionName !== undefined) {
      const sectionInput = this.page.locator("input[placeholder='Section Name']");
      await sectionInput.waitFor({ state: 'visible', timeout: 10000 });
      await sectionInput.fill(item.sectionName);
    }

    // Select Item if provided
    if (item.itemName) {
      const itemDropdown = this.page.locator("[id^='react-select-'][id$='-input']").nth(1);
      if (await itemDropdown.isVisible().catch(() => false)) {
        await itemDropdown.focus();
        await itemDropdown.fill(item.itemName);
        await this.page.waitForTimeout(400);
        await this.page.keyboard.press('ArrowDown');
        await this.page.keyboard.press('Enter');
      }
    }

    // Fill Item Description
    if (item.description !== undefined) {
      const descInput = this.page.locator("textarea[placeholder='Item Description']");
      if (await descInput.isVisible()) {
        await descInput.fill(item.description);
      }
    }

    // Fill Unit
    if (item.unit !== undefined) {
      const unitInput = this.page.locator("input[placeholder='Unit']");
      if (await unitInput.isVisible()) {
        await unitInput.fill(item.unit);
      }
    }

    // Fill Quantity
    if (item.quantity !== undefined) {
      const qtyInput = this.page.locator("input[placeholder='Quantity']");
      if (await qtyInput.isVisible()) {
        await qtyInput.fill(item.quantity);
      }
    }

    // Fill Rate
    if (item.rate !== undefined) {
      const rateInput = this.page.locator("input[placeholder='Rate']");
      if (await rateInput.isVisible()) {
        await rateInput.fill(item.rate);
      }
    }
  }

  // Validation helpers for negative testing
  async getValidationErrors(): Promise<string[]> {
    const errorLocators = this.page.locator('span.text-danger, .error-feedback, p.text-danger, .invalid-feedback, div[class*="error"], span[class*="error"]');
    return errorLocators.allInnerTexts();
  }

  async expectValidationError(messageRegex: RegExp) {
    const errorLocator = this.page.locator('text=' + messageRegex.source).first();
    await expect(errorLocator).toBeVisible({ timeout: 10000 });
  }

  async verifyQuoteCreated() {
    // Verify redirect or quote header shows Draft status and Quote number
    const draftBadge = this.page.locator('text=Draft, text=DRAFT').first();
    await expect(draftBadge).toBeVisible({ timeout: 20000 });
  }
}
