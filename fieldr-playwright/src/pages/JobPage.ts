import { Page, expect } from '@playwright/test';

export interface JobDetails {
  title: string;
  customerName?: string;
  startDate?: string; // YYYY-MM-DD
  endDate?: string;   // YYYY-MM-DD
  address?: string;
  radius?: string;
  description?: string;
}

export class JobPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async gotoList() {
    await this.page.goto('/app/job/list');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async gotoNew() {
    await this.page.goto('/app/job/new');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async clickAddJob() {
    const addJobBtn = this.page.locator('button').filter({ hasText: /add job/i });
    if (await addJobBtn.isVisible()) {
      await addJobBtn.click();
    } else {
      await this.gotoNew();
    }
  }

  async fillStep1JobDetails(details: JobDetails) {
    // 1. Fill Job Title
    const titleInput = this.page.locator('input[name="title"]');
    await titleInput.waitFor({ state: 'visible', timeout: 10000 });
    await titleInput.fill(details.title);

    // 2. Select Customer from react-select dropdown
    const customerSelect = this.page.locator('#react-select-5-input, [id^="react-select-"][id$="-input"]').first();
    if (await customerSelect.isVisible()) {
      await customerSelect.focus();
      if (details.customerName) {
        await customerSelect.fill(details.customerName);
        await this.page.waitForTimeout(500);
      }
      await this.page.keyboard.press('ArrowDown');
      await this.page.keyboard.press('Enter');
    }

    // 3. Fill Dates if provided
    const dateInputs = this.page.locator('input[name="date"]');
    const dateCount = await dateInputs.count();
    if (dateCount > 0 && details.startDate) {
      await dateInputs.nth(0).fill(details.startDate);
    }
    if (dateCount > 1 && details.endDate) {
      await dateInputs.nth(1).fill(details.endDate);
    }

    // 4. Fill Address
    if (details.address) {
      const addressInput = this.page.locator('input[placeholder*="address" i]');
      if (await addressInput.isVisible()) {
        await addressInput.fill(details.address);
        await this.page.waitForTimeout(600);
        // If an address suggestion dropdown appears, press Enter or Down
        await this.page.keyboard.press('ArrowDown');
        await this.page.keyboard.press('Enter');
      }
    }

    // 5. Fill Radius
    if (details.radius) {
      const radiusInput = this.page.locator('input[name="siteRadius"]');
      if (await radiusInput.isVisible()) {
        await radiusInput.fill(details.radius);
      }
    }

    // 6. Fill Description
    if (details.description) {
      const descInput = this.page.locator('textarea[name="description"]');
      if (await descInput.isVisible()) {
        await descInput.fill(details.description);
      }
    }
  }

  async clickNext() {
    const nextBtn = this.page.locator('button').filter({ hasText: /^next$/i });
    await nextBtn.waitFor({ state: 'visible' });
    await nextBtn.click();
    await this.page.waitForTimeout(800);
  }

  async finishAndCreateJob() {
    // Step 1 -> Step 2
    await this.clickNext();

    // Step 2 (Team) -> Step 3
    await this.clickNext();

    // Step 3 (Checklists) -> Step 4
    await this.clickNext();

    // Step 4 (Reports) -> Step 5
    await this.clickNext();

    // Step 5: Review & Save -> Click 'Create Job'
    const createBtn = this.page.locator('button').filter({ hasText: /create job/i });
    await createBtn.waitFor({ state: 'visible', timeout: 10000 });
    await createBtn.click();

    // Wait for redirect to job list or confirmation
    await this.page.waitForURL(/.*\/app\/job\/.*/, { timeout: 20000 });
  }

  async verifyJobCreated(jobTitle: string) {
    await this.gotoList();
    const jobRow = this.page.locator(`text=${jobTitle}`).first();
    await expect(jobRow).toBeVisible({ timeout: 15000 });
  }
}
