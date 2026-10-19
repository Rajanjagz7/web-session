import { expect, type Locator, type Page } from '@playwright/test';

/** The customer picker used on New Job and New Quote (PIC-01..04, JOB-04). */
export class PickerComponent {
  constructor(private readonly page: Page, private readonly label: string | RegExp = /customer/i) {} // TODO(confirm): picker label

  get combobox(): Locator {
    return this.page.getByRole('combobox', { name: this.label });
  }
  get searchInput(): Locator {
    return this.page.getByRole('combobox', { name: this.label }); // TODO(confirm): search box may be a separate textbox in the popup
  }
  get options(): Locator {
    return this.page.getByRole('option');
  }
  /** PIC-01 loading state. TODO(confirm): role of the loading indicator (status/progressbar). */
  get loading(): Locator {
    return this.page.getByRole('status');
  }
  get clearButton(): Locator {
    return this.page.getByRole('button', { name: /clear/i }); // TODO(confirm)
  }

  async open(): Promise<void> {
    await this.combobox.click();
    await expect(this.options.first()).toBeVisible();
  }

  async search(term: string): Promise<void> {
    await this.searchInput.fill(term);
  }

  async clear(): Promise<void> {
    await this.searchInput.fill('');
  }

  option(text: string | RegExp): Locator {
    return this.page.getByRole('option', { name: text });
  }
}
