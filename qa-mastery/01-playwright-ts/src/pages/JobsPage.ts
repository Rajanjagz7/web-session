import { Page, expect, Locator } from '@playwright/test';

export class JobsPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
    await this.page.waitForTimeout(1500);
  }

  async getTableRowByJobId(jobId: string): Promise<Locator> {
    const row = this.page.locator('tr').filter({ hasText: jobId }).first();
    await expect(row).toBeVisible({ timeout: 10000 });
    return row;
  }

  async expectJobDetailsInTable(jobId: string, expectedCompany: string, expectedCustomer: string) {
    const row = await this.getTableRowByJobId(jobId);
    await expect(row).toContainText(expectedCompany);
    await expect(row).toContainText(expectedCustomer);
    await expect(row).toContainText('Engagement Sent');
  }

  async search(query: string) {
    const searchBox = this.page.locator('input[placeholder*="Search" i]').first();
    await searchBox.fill(query);
    await searchBox.press('Enter');
    await this.page.waitForTimeout(1500);
  }

  async clearSearch() {
    const searchBox = this.page.locator('input[placeholder*="Search" i]').first();
    await searchBox.fill('');
    await searchBox.press('Enter');
    await this.page.waitForTimeout(1000);
  }

  async clickJob(jobId: string) {
    const row = await this.getTableRowByJobId(jobId);
    const link = row.locator('a').filter({ hasText: jobId }).first();
    if (await link.isVisible()) {
      await link.click();
    } else {
      await row.click();
    }
    await this.page.waitForURL(/.*\/jobs\/.*/, { timeout: 10000 });
  }
}
