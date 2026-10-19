import { test, expect } from '@playwright/test';
import { LoginPage } from '../../src/pages/LoginPage';
import { AddJobModal } from '../../src/pages/AddJobModal';
import { JobsPage } from '../../src/pages/JobsPage';
import { AU_TEST_DATA } from '../../src/data/australian-data';

test.describe('NSW-JOB: RebateM8 NSW End-to-End Job Creation with Australian Data', () => {
  let loginPage: LoginPage;
  let addJobModal: AddJobModal;
  let jobsPage: JobsPage;

  test.beforeEach(async ({ page }) => {
    test.setTimeout(90000);
    loginPage = new LoginPage(page);
    addJobModal = new AddJobModal(page);
    jobsPage = new JobsPage(page);

    await loginPage.goto();
    await loginPage.login('admin@rebatem8nsw.com.au', 'admin@123');
    await loginPage.expectLoggedIn();
  });

  test('NSW-JOB-001: E2E Create Residential Job (Heating & Cooling) under Rajan Testing Company', async ({ page }) => {
    await jobsPage.goto();
    await addJobModal.open();

    const customer = AU_TEST_DATA.residentialCustomers[0]; // Olivia Nguyen, Sydney NSW
    const ref = `E2E-HC-${Date.now().toString().slice(-5)}`;

    await addJobModal.fillResidentialJob({
      reference: ref,
      activityType: AU_TEST_DATA.activityTypes.heatingCooling,
      leadGen: AU_TEST_DATA.leadGenerationMethods[0], // Customer initiated contact
      buildingType: AU_TEST_DATA.buildingTypes.residential,
      company: AU_TEST_DATA.installerCompany,
      installerPerson: AU_TEST_DATA.installerPerson,
      customer: customer,
    });

    // Submit and assert HTTP 201 Created
    await addJobModal.submitAndExpectSuccess();

    // Verify in Jobs table
    await jobsPage.goto();
    const row = page.locator('tr').filter({ hasText: customer.fullName }).first();
    await expect(row).toBeVisible({ timeout: 15000 });
    await expect(row).toContainText(AU_TEST_DATA.installerCompany);
    await expect(row).toContainText(AU_TEST_DATA.activityTypes.heatingCooling);
    await expect(row).toContainText('Engagement Sent');
  });

  test('NSW-JOB-002: E2E Create Residential Job (Hot Water Heat Pump) under Rajan Testing Company', async ({ page }) => {
    await jobsPage.goto();
    await addJobModal.open();

    const customer = AU_TEST_DATA.residentialCustomers[1]; // Jack Wilson, The Rocks NSW
    const ref = `E2E-HWHP-${Date.now().toString().slice(-5)}`;

    await addJobModal.fillResidentialJob({
      reference: ref,
      activityType: AU_TEST_DATA.activityTypes.hotWaterHeatPump,
      leadGen: AU_TEST_DATA.leadGenerationMethods[1], // Online advertisement
      buildingType: AU_TEST_DATA.buildingTypes.residential,
      company: AU_TEST_DATA.installerCompany,
      installerPerson: AU_TEST_DATA.installerPerson,
      customer: customer,
      newSystem: 'Heat pump',
    });

    // Submit and assert HTTP 201 Created
    await addJobModal.submitAndExpectSuccess();

    // Verify in Jobs table
    await jobsPage.goto();
    const row = page.locator('tr').filter({ hasText: customer.fullName }).first();
    await expect(row).toBeVisible({ timeout: 15000 });
    await expect(row).toContainText(AU_TEST_DATA.installerCompany);
    await expect(row).toContainText(AU_TEST_DATA.activityTypes.hotWaterHeatPump);
    await expect(row).toContainText('Engagement Sent');
  });

  test('NSW-JOB-003: E2E Create Small Business Site Job with 11-digit ABN under Rajan Testing Company', async ({ page }) => {
    await jobsPage.goto();
    await addJobModal.open();

    const biz = AU_TEST_DATA.businessCustomers[0]; // Apex Innovations, Wollongong NSW, ABN 33102417032
    const ref = `E2E-BIZ-${Date.now().toString().slice(-5)}`;

    await addJobModal.fillBusinessJob({
      reference: ref,
      activityType: AU_TEST_DATA.activityTypes.heatingCooling,
      leadGen: AU_TEST_DATA.leadGenerationMethods[2], // Social media
      buildingType: AU_TEST_DATA.buildingTypes.smallBusinessSmall,
      company: AU_TEST_DATA.installerCompany,
      installerPerson: AU_TEST_DATA.installerPerson,
      business: biz,
    });

    // Submit and assert HTTP 201 Created
    await addJobModal.submitAndExpectSuccess();

    // Verify in Jobs table
    await jobsPage.goto();
    const row = page.locator('tr').filter({ hasText: biz.businessName }).first();
    await expect(row).toBeVisible({ timeout: 15000 });
    await expect(row).toContainText(AU_TEST_DATA.installerCompany);
    await expect(row).toContainText('Business');
    await expect(row).toContainText('Engagement Sent');
  });
});
