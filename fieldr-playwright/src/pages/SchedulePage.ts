import { Page, expect } from '@playwright/test';

export interface ShiftDetails {
  date?: string;
  startTime?: string;
  endTime?: string;
  shiftName?: string;
  jobName?: string;
}

export class SchedulePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/app/schedule');
    await this.page.waitForLoadState('domcontentloaded');
    // Wait for the schedule grid to load
    await this.page.waitForSelector('.rbc-calendar, div[class*="schedule"], table', { timeout: 20000 });
  }

  async openAddShiftDrawer() {
    // Look for Add Shift button or click an open cell in the schedule grid
    const addShiftBtn = this.page.locator('button[aria-label="Add shift"], button:has-text("Add shift"), button:has-text("Add Shift")').first();
    if (await addShiftBtn.isVisible({ timeout: 4000 }).catch(() => false)) {
      await addShiftBtn.click();
    } else {
      // Click on a cell in the schedule matrix
      const gridCell = this.page.locator('div[class*="cell"], div[class*="slot"], td').filter({ hasNotText: /job|user/i }).first();
      await gridCell.click({ force: true });
    }
    // Wait for drawer to open
    await this.page.waitForSelector('text=Add Shift', { timeout: 10000 });
  }

  async clearShiftDate() {
    const clearBtn = this.page.locator('span.close-btn, button[aria-label="Clear"]').first();
    if (await clearBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await clearBtn.click();
    }
  }

  async setShiftDate(dateStr: string) {
    // dateStr format: MM/DD/YYYY or YYYY-MM-DD
    const dateInput = this.page.locator("input[placeholder*='date' i], input").first();
    await dateInput.click();
    await dateInput.fill(dateStr);
    await this.page.keyboard.press('Enter');
  }

  async setStartTime(timeStr: string) {
    const startSelect = this.page.locator('#react-select-2-input, [id^="react-select-"][id$="-input"]').first();
    await startSelect.focus();
    await startSelect.fill(timeStr);
    await this.page.waitForTimeout(300);
    await this.page.keyboard.press('Enter');
  }

  async setEndTime(timeStr: string) {
    const endSelect = this.page.locator('#react-select-3-input, [id^="react-select-"][id$="-input"]').nth(1);
    await endSelect.focus();
    await endSelect.fill(timeStr);
    await this.page.waitForTimeout(300);
    await this.page.keyboard.press('Enter');
  }

  async setShiftName(name: string) {
    const nameInput = this.page.locator('input[placeholder="Enter Shift Name"]');
    await nameInput.waitFor({ state: 'visible', timeout: 5000 });
    await nameInput.fill(name);
  }

  async clearShiftName() {
    const nameInput = this.page.locator('input[placeholder="Enter Shift Name"]');
    await nameInput.waitFor({ state: 'visible', timeout: 5000 });
    await nameInput.fill('');
  }

  async assignJob(jobName?: string) {
    const jobSelect = this.page.locator('#react-select-4-input, [id^="react-select-"][id$="-input"]').last();
    if (await jobSelect.isVisible().catch(() => false)) {
      await jobSelect.focus();
      if (jobName) {
        await jobSelect.fill(jobName);
        await this.page.waitForTimeout(400);
      }
      await this.page.keyboard.press('ArrowDown');
      await this.page.keyboard.press('Enter');
    }
  }

  async clickPublish() {
    const publishBtn = this.page.locator('button').filter({ hasText: /^publish$/i });
    await publishBtn.waitFor({ state: 'visible' });
    await publishBtn.click();
  }

  async fillShiftDetails(details: ShiftDetails) {
    if (details.date) {
      await this.setShiftDate(details.date);
    }
    if (details.startTime) {
      await this.setStartTime(details.startTime);
    }
    if (details.endTime) {
      await this.setEndTime(details.endTime);
    }
    if (details.shiftName !== undefined) {
      await this.setShiftName(details.shiftName);
    }
    if (details.jobName) {
      await this.assignJob(details.jobName);
    }
  }

  async expectValidationError(messageRegex: RegExp) {
    const errorLocator = this.page.locator(`text=${messageRegex.source}`).first();
    await expect(errorLocator).toBeVisible({ timeout: 8000 });
  }

  async verifyShiftVisibleOnGrid(shiftName: string) {
    const shiftCard = this.page.locator(`text=${shiftName}`).first();
    await expect(shiftCard).toBeVisible({ timeout: 15000 });
  }
}
