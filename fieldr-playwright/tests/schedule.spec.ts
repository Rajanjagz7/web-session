import { test, expect } from '@playwright/test';
import { LoginPage } from '../src/pages/LoginPage';
import { SchedulePage } from '../src/pages/SchedulePage';

test.describe('Schedule Job Module Tests', () => {
  let loginPage: LoginPage;
  let schedulePage: SchedulePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    schedulePage = new SchedulePage(page);

    const email = process.env.TEST_EMAIL || 'anayra@yopmail.com';
    const otp = process.env.TEST_OTP || '';

    // Authenticate into Fieldr
    await loginPage.login(email, otp);
  });

  test.describe('Negative Scenarios', () => {
    test('should validate that shift title is required', async ({ page }) => {
      await schedulePage.goto();
      await schedulePage.openAddShiftDrawer();

      // Clear or ensure Shift Name is empty
      await schedulePage.clearShiftName();

      // Attempt to publish
      await schedulePage.clickPublish();

      // Expect validation error
      await schedulePage.expectValidationError(/Shift title is required/i);
    });

    test('should validate that shift date is required when cleared', async ({ page }) => {
      await schedulePage.goto();
      await schedulePage.openAddShiftDrawer();

      // Clear the shift date
      await schedulePage.clearShiftDate();

      // Enter shift name so only date is missing
      await schedulePage.setShiftName('Test Missing Date Shift');

      // Attempt to publish
      await schedulePage.clickPublish();

      // Expect validation error
      await schedulePage.expectValidationError(/Shift date is required/i);
    });

    test('should validate that end time must be after start time', async ({ page }) => {
      await schedulePage.goto();
      await schedulePage.openAddShiftDrawer();

      // Set invalid time range: Start 3:00 PM and End 2:00 PM
      await schedulePage.setStartTime('3:00pm');
      await schedulePage.setEndTime('2:00pm');

      // Attempt to publish or verify inline error
      await schedulePage.clickPublish();

      // Expect validation error
      await schedulePage.expectValidationError(/End must be after start/i);
    });
  });

  test.describe('Positive Scenarios', () => {
    test('should successfully schedule and publish a new shift on the calendar grid', async ({ page }) => {
      await schedulePage.goto();
      await schedulePage.openAddShiftDrawer();

      const timestamp = Date.now();
      const shiftTitle = `Auto Shift ${timestamp}`;

      // Fill valid shift parameters
      await schedulePage.fillShiftDetails({
        startTime: '1:00pm',
        endTime: '2:00pm',
        shiftName: shiftTitle,
      });

      // Assign Job
      await schedulePage.assignJob();

      // Publish the shift
      await schedulePage.clickPublish();

      // Verify that the drawer closes and the shift card appears on the calendar grid
      await schedulePage.verifyShiftVisibleOnGrid(shiftTitle);
    });
  });
});
