import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

export class QuotesPage extends BasePage {
  // ---- list (QUO-04)
  get createdByHeader(): Locator {
    return this.columnHeader(/created by/i); // TODO(confirm): exact header text
  }
  get rows(): Locator {
    return this.page.getByRole('row');
  }
  get newQuoteButton(): Locator {
    return this.page.getByRole('button', { name: /new quote/i }); // TODO(confirm)
  }

  async openList(): Promise<void> {
    await this.open(env.routes.quotes);
  }

  async openQuote(title: string): Promise<void> {
    await this.page.getByRole('link', { name: title }).click(); // TODO(confirm): quote rows are links
  }

  // ---- formula columns (QUO-01..03)
  get addColumnButton(): Locator {
    return this.page.getByRole('button', { name: /add (formula )?column/i }); // TODO(confirm)
  }
  get columnNameInput(): Locator {
    return this.page.getByLabel(/column name/i); // TODO(confirm)
  }
  get formulaInput(): Locator {
    return this.page.getByLabel(/formula/i); // TODO(confirm)
  }
  formulaToken(name: 'Cost Price' | 'Margin %' | 'Markup %'): Locator {
    return this.page.getByRole('option', { name }); // TODO(confirm): token picker role (option/menuitem/button)
  }
  showToCustomerToggle(columnName: string): Locator {
    return this.page.getByRole('row', { name: columnName }).getByRole('checkbox', { name: /show to customer/i }); // TODO(confirm): checkbox vs switch
  }
  cell(columnName: string, rowName: string): Locator {
    return this.page.getByRole('row', { name: rowName }).getByRole('cell', { name: columnName }); // TODO: fragile (cell has no name); prefer data-testid
  }

  async addFormulaColumn(name: string, tokens: ReadonlyArray<'Cost Price' | 'Margin %' | 'Markup %'>): Promise<void> {
    await this.addColumnButton.click();
    await this.columnNameInput.fill(name);
    for (const t of tokens) await this.formulaToken(t).click();
    await this.page.getByRole('button', { name: /save|add/i }).click(); // TODO(confirm)
  }

  // ---- a fresh quote must not carry over the previous one (BUG-02)
  get sectionNameInputs(): Locator {
    return this.page.getByRole('textbox', { name: /section name/i }); // TODO(confirm)
  }
  get lineRows(): Locator {
    return this.page.getByRole('row', { name: /line|item/i }); // TODO(confirm)
  }
}
