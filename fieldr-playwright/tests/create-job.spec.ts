import { test, expect } from '@playwright/test';
import { LoginPage } from '../src/pages/LoginPage';
import { JobPage } from '../src/pages/JobPage';

test.describe('Fieldr Project & Job Creation Tests', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    const email = process.env.TEST_EMAIL || 'anayra@yopmail.com';
    const otp = process.env.TEST_OTP || '';

    // Perform login
    await loginPage.login(email, otp);
  });

  test('should create a new project/job through 5-step wizard', async ({ page }) => {
    const jobPage = new JobPage(page);
    const timestamp = Date.now();
    const jobTitle = `Project Auto ${timestamp}`;

    // Step 1: Open creation wizard
    await jobPage.gotoNew();

    // Fill Step 1
    await jobPage.fillStep1JobDetails({
      title: jobTitle,
      startDate: '2026-09-10',
      endDate: '2026-09-25',
      address: '100 Broadway, New York, NY',
      radius: '150',
      description: 'Automated test project created via Playwright test suite.',
    });

    // Advance through Wizard and submit
    await jobPage.finishAndCreateJob();

    // Verify job was created and is visible in the list
    await jobPage.verifyJobCreated(jobTitle);
  });
});
