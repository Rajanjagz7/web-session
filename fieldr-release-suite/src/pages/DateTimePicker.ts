import { type Locator, type Page } from '@playwright/test';

/** DTM-01. TODO(confirm): the picker exposes its slots as role="option" inside a listbox. */
export class DateTimePicker {
  constructor(private readonly page: Page, private readonly label: string | RegExp) {}

  get input(): Locator {
    return this.page.getByLabel(this.label);
  }
  get slots(): Locator {
    return this.page.getByRole('listbox').getByRole('option');
  }
  async open(): Promise<void> {
    await this.input.click();
  }
  /** Slot labels, e.g. ["12:00 am", "12:15 am", ...]. Parsing is done in the spec. */
  async slotLabels(): Promise<string[]> {
    return this.slots.allInnerTexts();
  }
}
