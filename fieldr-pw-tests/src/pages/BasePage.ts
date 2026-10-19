import { expect, type Locator, type Page } from '@playwright/test';
import { env } from '../lib/env';

/** Shared helpers. Locators in page objects are role-based first, then getByTestId, then getByLabel. */
export abstract class BasePage {
  constructor(protected readonly page: Page) {}

  /** `base` is one of env.baseUrl / env.portalUrl / env.adminUrl. */
  async open(path: string, base: string = env.baseUrl): Promise<void> {
    await this.page.goto(new URL(path, base).toString());
  }

  get main(): Locator {
    return this.page.getByRole('main');
  }

  get alert(): Locator {
    return this.page.getByRole('alert');
  }

  /** Visible text inside the main landmark; use toContainText for stable assertions without CSS. */
  async expectMainContains(text: string | RegExp): Promise<void> {
    await expect(this.main).toContainText(text);
  }

  async expectMainNotContains(text: string | RegExp): Promise<void> {
    await expect(this.main).not.toContainText(text);
  }

  columnHeader(name: string | RegExp): Locator {
    return this.page.getByRole('columnheader', { name });
  }

  dialog(name?: string | RegExp): Locator {
    return name === undefined ? this.page.getByRole('dialog') : this.page.getByRole('dialog', { name });
  }
}
