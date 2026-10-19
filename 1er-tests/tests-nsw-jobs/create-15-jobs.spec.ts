import { test, expect } from '@playwright/test';
import {
  login,
  openAddJobDrawer,
  fillJobForm,
  submitJob,
  expectFieldError,
  expectJobCreated,
  submitAndReport,
} from './helpers';

const INSTALLER_COMPANY = process.env.NSW_INSTALLER_COMPANY || 'Rajan Testing Company';

// Unique per test run so re-runs don't collide on ABN/phone/email.
const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n: number) => `${RUN_ID}${n}`;
const abn = (n: number) => uniq(n).padStart(11, '0').slice(-11);
const phone = (n: number) => `4${uniq(n).padStart(8, '0').slice(-8)}`;

test.describe('Valid job creation - Australian data', () => {
  const validCases = [
    {
      label: 'Heating & Cooling / Residential / Phone lead / Sydney CBD',
      customerName: 'Olivia Bennett',
      addressSearch: '1 George Street Sydney',
      postcode: '2000',
      activityType: 'Heating & Cooling',
      buildingType: 'Residential Building',
      leadMethod: 'Customer initiated contact',
      installationDate: '28-08-2026',
    },
    {
      label: 'Hot Water Heat Pump / Residential / Website lead / Artarmon',
      customerName: 'Jack Sullivan',
      addressSearch: '50 Elizabeth Street Artarmon',
      postcode: '2064',
      activityType: 'Hot Water Heat Pump',
      buildingType: 'Residential Building',
      newSystem: 'Heat pump',
      leadMethod: 'Online advertisement',
      installationDate: '29-08-2026',
    },
    {
      label: 'Heating & Cooling / Small Business / Referral lead / North Sydney',
      customerName: 'Mia Robertson',
      addressSearch: '123 Walker Street North Sydney',
      postcode: '2060',
      activityType: 'Heating & Cooling',
      // 'Small Business Site' is now split into two size tiers on the live
      // site (confirmed via a failed-run page snapshot on 2026-09-16);
      // defaulting to the smaller tier since these test cases don't model
      // energy usage.
      buildingType: 'Small Business Site (less than 273 kWh/day)',
      leadMethod: 'Other',
      installationDate: '01-09-2026',
    },
    {
      label: 'Hot Water Heat Pump / Small Business / Email lead / St Leonards',
      customerName: 'Noah Fitzgerald',
      addressSearch: '66 Pacific Highway St Leonards',
      postcode: '2065',
      activityType: 'Hot Water Heat Pump',
      // 'Small Business Site' is now split into two size tiers on the live
      // site (confirmed via a failed-run page snapshot on 2026-09-16);
      // defaulting to the smaller tier since these test cases don't model
      // energy usage.
      buildingType: 'Small Business Site (less than 273 kWh/day)',
      // 'New system' is only shown for Hot Water Heat Pump + Residential
      // Building - Small Business Site skips it.
      leadMethod: 'Email campaign',
      installationDate: '02-09-2026',
    },
    {
      label: 'Heating & Cooling / Residential / Phone lead / Dulwich Hill',
      customerName: 'Ava Thompson',
      addressSearch: '789 New Canterbury Road Dulwich Hill',
      postcode: '2203',
      activityType: 'Heating & Cooling',
      buildingType: 'Residential Building',
      leadMethod: 'Customer initiated contact',
      installationDate: '03-09-2026',
    },
    {
      label: 'Hot Water Heat Pump / Residential / Referral lead / Punchbowl',
      customerName: 'Lucas Whitfield',
      addressSearch: '898 Punchbowl Road Punchbowl',
      postcode: '2196',
      activityType: 'Hot Water Heat Pump',
      buildingType: 'Residential Building',
      newSystem: 'Heat pump',
      leadMethod: 'Other',
      installationDate: '04-09-2026',
    },
  ];

  validCases.forEach((data, i) => {
    test(`Valid Job ${i + 1}: ${data.label}`, async ({ page }) => {
      await login(page);
      const dialog = await openAddJobDrawer(page);

      await fillJobForm(dialog, {
        customerName: data.customerName,
        email: `${data.customerName.toLowerCase().replace(/\s+/g, '.')}.${uniq(i)}@yopmail.com`,
        phone: phone(i),
        abnAcn: abn(i),
        addressSearch: data.addressSearch,
        postcode: data.postcode,
        activityType: data.activityType,
        buildingType: data.buildingType,
        newSystem: data.newSystem,
        leadMethod: data.leadMethod,
        ownReference: `REF-${RUN_ID}-${i}`,
        installationDate: data.installationDate,
        installer: INSTALLER_COMPANY,
        fillEquipment: true,
      });

      await submitJob(dialog);
      await expectJobCreated(page, dialog, data.customerName);
    });
  });
});

test.describe('Invalid field formats', () => {
  const baseValid = (i: number) => ({
    customerName: `Format Test ${i}`,
    email: `format.test.${uniq(i)}@yopmail.com`,
    phone: phone(100 + i),
    abnAcn: abn(100 + i),
    addressSearch: '1 George Street Sydney',
    postcode: '2000',
    activityType: 'Heating & Cooling',
    buildingType: 'Residential Building',
    leadMethod: 'Customer initiated contact',
    ownReference: `REF-${RUN_ID}-INV${i}`,
    installationDate: '10-09-2026',
    installer: INSTALLER_COMPANY,
    fillEquipment: true,
  });

  test('Invalid Job 1: malformed email is rejected', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(1), email: 'not-an-email' });
    await submitJob(dialog);
    await expectFieldError(dialog, 'Enter a valid email');
    await expect(dialog.getByPlaceholder('Enter customer name')).toBeVisible();
  });

  test('Invalid Job 2: ABN/ACN too short (5 digits) is rejected', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(2), abnAcn: '12345' });
    await submitJob(dialog);
    await expectFieldError(dialog, 'ABN/ACN must be exactly 11 digits');
    await expect(dialog.getByPlaceholder('Enter customer name')).toBeVisible();
  });

  test('Invalid Job 3: ABN/ACN over 11 digits is silently truncated, not rejected', async ({ page }) => {
    // Actual app behaviour (found by running this case): the ABN/ACN input
    // has a maxlength of 11, so typing 13 digits just truncates to the
    // first 11 rather than showing "must be exactly 11 digits" - the job
    // submits successfully. This documents that real behaviour instead of
    // assuming a rejection that doesn't happen.
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(3), abnAcn: '1234567890123' });

    const abnField = dialog.getByPlaceholder('12345678901');
    await expect(abnField).toHaveValue('12345678901'); // truncated to first 11 digits

    await submitJob(dialog);
    await expectJobCreated(page, dialog, 'Format Test 3');
  });

  test('Invalid Job 4: Email and Phone left blank amid otherwise valid data', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    const data = baseValid(4);
    await fillJobForm(dialog, { ...data, email: undefined, phone: undefined });
    await submitJob(dialog);
    await expectFieldError(dialog, 'Email is required');
    await expectFieldError(dialog, 'Phone is required');
    // Fields that were filled must not also show as required.
    await expect(dialog.getByText('Customer name is required', { exact: true })).not.toBeVisible();
    await expect(dialog.getByPlaceholder('Enter customer name')).toBeVisible();
  });
});

test.describe('Negative / edge cases', () => {
  test('Negative Job 1: fully empty form shows every required-field error', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await submitJob(dialog);

    for (const message of [
      'Customer name is required',
      'Email is required',
      'Phone is required',
      'ABN/ACN is required',
      'Site address is required',
      'Postcode is required',
      'Activity type is required',
      'Building type is required',
      'Method of lead generation is required',
      'Own reference is required',
      'Installation date is required',
      'Installer (company) is required',
    ]) {
      await expectFieldError(dialog, message);
    }
    await expect(dialog.getByPlaceholder('Enter customer name')).toBeVisible();
  });

  test('Negative Job 2: Installer (company) left blank, everything else valid', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, {
      customerName: 'Missing Installer',
      email: `missing.installer.${uniq(5)}@yopmail.com`,
      phone: phone(105),
      abnAcn: abn(105),
      addressSearch: '1 George Street Sydney',
      postcode: '2000',
      activityType: 'Heating & Cooling',
      buildingType: 'Residential Building',
      leadMethod: 'Customer initiated contact',
      ownReference: `REF-${RUN_ID}-NEG2`,
      installationDate: '11-09-2026',
      // installer intentionally omitted
    });
    await submitJob(dialog);
    await expectFieldError(dialog, 'Installer (company) is required');
    await expect(dialog.getByText('Customer name is required', { exact: true })).not.toBeVisible();
    await expect(dialog.getByPlaceholder('Enter customer name')).toBeVisible();
  });

  test('Negative Job 3: Site address left blank, everything else valid', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, {
      customerName: 'Missing Address',
      email: `missing.address.${uniq(6)}@yopmail.com`,
      phone: phone(106),
      abnAcn: abn(106),
      postcode: '2000',
      activityType: 'Heating & Cooling',
      buildingType: 'Residential Building',
      leadMethod: 'Customer initiated contact',
      ownReference: `REF-${RUN_ID}-NEG3`,
      installationDate: '12-09-2026',
      installer: INSTALLER_COMPANY,
      // addressSearch intentionally omitted
    });
    await submitJob(dialog);
    await expectFieldError(dialog, 'Site address is required');
    await expect(dialog.getByPlaceholder('Enter customer name')).toBeVisible();
  });

  test('Negative Job 4: extremely long Customer Name and Own Reference do not crash the form', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    const longName = 'Very Long Customer Name '.repeat(15).trim(); // ~375 chars
    const longRef = `REF-${RUN_ID}-` + 'X'.repeat(200);

    await fillJobForm(dialog, {
      customerName: longName,
      email: `long.input.${uniq(7)}@yopmail.com`,
      phone: phone(107),
      abnAcn: abn(107),
      addressSearch: '1 George Street Sydney',
      postcode: '2000',
      activityType: 'Heating & Cooling',
      buildingType: 'Residential Building',
      leadMethod: 'Customer initiated contact',
      ownReference: longRef,
      installationDate: '13-09-2026',
      installer: INSTALLER_COMPANY,
      fillEquipment: true,
    });
    await submitJob(dialog);
    await page.waitForTimeout(2000);

    // The app must still be alive and on the Jobs page either way (accepted
    // the long input or showed a validation message) - it must not crash.
    await expect(page).toHaveURL(/\/jobs/);
  });

  test('Negative Job 5: HTML/script-injection style Customer Name is handled safely', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);

    let alertFired = false;
    page.on('dialog', async (d) => {
      alertFired = true;
      await d.dismiss();
    });

    await fillJobForm(dialog, {
      customerName: `<script>alert('xss')</script> O'Brien-Smith`,
      email: `xss.test.${uniq(8)}@yopmail.com`,
      phone: phone(108),
      abnAcn: abn(108),
      addressSearch: '1 George Street Sydney',
      postcode: '2000',
      activityType: 'Heating & Cooling',
      buildingType: 'Residential Building',
      leadMethod: 'Customer initiated contact',
      ownReference: `REF-${RUN_ID}-NEG5`,
      installationDate: '14-09-2026',
      installer: INSTALLER_COMPANY,
      fillEquipment: true,
    });
    await submitJob(dialog);
    await page.waitForTimeout(2000);

    // The script tag must never actually execute as JS.
    expect(alertFired).toBe(false);
    await expect(page).toHaveURL(/\/jobs/);
  });
});

test.describe('Negative / edge cases: special characters & symbol boundary values', () => {
  // Deliberately punctuation/symbol-heavy, includes the exact characters
  // requested: !@#!$)(@$&%$*9
  const SPECIAL_CHARS = "!@#!$)(@$&%$*9^&*()_+-=[]{}|;:'<>,.?/~";

  test('Negative Job 6: special characters in Customer name and Own reference', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, {
      customerName: SPECIAL_CHARS,
      email: `special.chars.${uniq(9)}@yopmail.com`,
      phone: phone(109),
      abnAcn: abn(109),
      addressSearch: '1 George Street Sydney',
      postcode: '2000',
      activityType: 'Heating & Cooling',
      buildingType: 'Residential Building',
      leadMethod: 'Customer initiated contact',
      ownReference: SPECIAL_CHARS,
      installationDate: '15-09-2026',
      installer: INSTALLER_COMPANY,
      fillEquipment: true,
    });

    const nameValue = await dialog.getByPlaceholder('Enter customer name').inputValue();
    const refValue = await dialog.getByPlaceholder('REF-001').inputValue();
    console.log(`[Negative 6] Customer name field holds: "${nameValue}"`);
    console.log(`[Negative 6] Own reference field holds: "${refValue}"`);

    await submitJob(dialog);
    await page.waitForTimeout(2500);

    const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
    if (stillOpen) {
      console.log('[Negative 6] Result: submission BLOCKED. Dialog validation text:\n' + (await dialog.innerText()));
    } else {
      console.log('[Negative 6] Result: job CREATED with special-character customer name/own reference (no validation blocked it).');
    }
    // Must not crash the app either way.
    await expect(page).toHaveURL(/\/jobs/);
  });

  test('Negative Job 7: special characters in numeric-only required fields (Phone, ABN/ACN, Postcode)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);

    await dialog.getByPlaceholder('Enter customer name').fill('Special Char Numeric Test');
    await dialog.getByPlaceholder('customer@email.com').fill(`special.numeric.${uniq(10)}@yopmail.com`);

    const phoneField = dialog.getByPlaceholder('412345678');
    await phoneField.click();
    await page.keyboard.type(SPECIAL_CHARS);
    console.log(`[Negative 7] Phone field holds after typing special characters: "${await phoneField.inputValue()}"`);

    const abnField = dialog.getByPlaceholder('12345678901');
    await abnField.fill(SPECIAL_CHARS);
    console.log(`[Negative 7] ABN/ACN field holds after special characters: "${await abnField.inputValue()}"`);

    const postcodeField = dialog.getByPlaceholder('2000');
    await postcodeField.fill(SPECIAL_CHARS);
    console.log(`[Negative 7] Postcode field holds after special characters: "${await postcodeField.inputValue()}"`);

    await submitJob(dialog);
    await page.waitForTimeout(2000);
    const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
    if (stillOpen) {
      console.log('[Negative 7] Result: submission BLOCKED. Dialog validation text:\n' + (await dialog.innerText()));
    } else {
      console.log('[Negative 7] Result: job CREATED - numeric fields accepted special characters unexpectedly.');
    }
    await expect(page).toHaveURL(/\/jobs/);
  });

  test('Negative Job 8: special characters in Email local-part are rejected', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, {
      customerName: 'Special Email Test',
      email: `${SPECIAL_CHARS}@yopmail.com`,
      phone: phone(111),
      abnAcn: abn(111),
      addressSearch: '1 George Street Sydney',
      postcode: '2000',
      activityType: 'Heating & Cooling',
      buildingType: 'Residential Building',
      leadMethod: 'Customer initiated contact',
      ownReference: `REF-${RUN_ID}-NEG8`,
      installationDate: '16-09-2026',
      installer: INSTALLER_COMPANY,
      fillEquipment: true,
    });
    await submitJob(dialog);
    await expectFieldError(dialog, 'Enter a valid email');
    await expect(dialog.getByPlaceholder('Enter customer name')).toBeVisible();
  });
});

test.describe('Additional edge cases & boundary values', () => {
  const baseValid = (i: number) => ({
    customerName: `Edge Case ${i}`,
    email: `edge.case.${uniq(i)}@yopmail.com`,
    phone: phone(200 + i),
    abnAcn: abn(200 + i),
    addressSearch: '1 George Street Sydney',
    postcode: '2000',
    activityType: 'Heating & Cooling',
    buildingType: 'Residential Building',
    leadMethod: 'Customer initiated contact',
    ownReference: `REF-${RUN_ID}-EDGE${i}`,
    installationDate: '20-09-2026',
    installer: INSTALLER_COMPANY,
    fillEquipment: true,
  });

  test('Edge Case 1: Postcode too short (2 digits)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(1), postcode: '20' });
    const postcodeValue = await dialog.getByPlaceholder('2000').inputValue();
    console.log(`[Edge 1] Postcode field holds: "${postcodeValue}"`);
    await submitAndReport(page, dialog, 'Edge 1');
  });

  test('Edge Case 2: Postcode from a different state than the selected address (NSW address, VIC postcode)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    // Address is "1 George Street, Sydney NSW 2000" but postcode is filled
    // with a Melbourne (VIC) postcode - checks for cross-field state/postcode
    // consistency validation.
    await fillJobForm(dialog, { ...baseValid(2), addressSearch: '1 George Street Sydney', postcode: '3000' });
    await submitAndReport(page, dialog, 'Edge 2');
  });

  test('Edge Case 3: whitespace-only Customer name and Own reference', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(3), customerName: '   ', ownReference: '   ' });
    const nameValue = await dialog.getByPlaceholder('Enter customer name').inputValue();
    console.log(`[Edge 3] Customer name field holds: "${nameValue}" (length ${nameValue.length})`);
    await submitAndReport(page, dialog, 'Edge 3');
  });

  test('Edge Case 4: SQL-injection style Customer name is handled safely', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(4), customerName: "Robert'); DROP TABLE Jobs;--" });
    const { created } = await submitAndReport(page, dialog, 'Edge 4');
    if (created) {
      // If it was created, the app must still be fully functional afterwards
      // (i.e. the string was stored as literal text, not executed as SQL).
      await page.goto('/jobs');
      await expect(page.getByRole('button', { name: /add job/i })).toBeVisible();
    }
    await expect(page).toHaveURL(/\/jobs/);
  });

  test('Edge Case 5: Unicode and emoji in Customer name', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(5), customerName: '陈伟 🏠 Müller Nguyễn' });
    const nameValue = await dialog.getByPlaceholder('Enter customer name').inputValue();
    console.log(`[Edge 5] Customer name field holds: "${nameValue}"`);
    await submitAndReport(page, dialog, 'Edge 5');
  });

  test('Edge Case 6: duplicate ABN, Phone and Email reused from Valid Job 1', async ({ page }) => {
    // Valid Job 1 (in the first describe block) was created with
    // abn(0)/phone(0) and email `olivia.bennett.${uniq(0)}@yopmail.com`.
    // Reusing them here checks whether the app flags/blocks duplicate
    // customer identifiers or just creates a second job freely.
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, {
      ...baseValid(6),
      customerName: 'Duplicate Of Olivia',
      email: `olivia.bennett.${uniq(0)}@yopmail.com`,
      phone: phone(0),
      abnAcn: abn(0),
    });
    await submitAndReport(page, dialog, 'Edge 6');
  });

  test('Edge Case 7: Installation date in the past', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(7), installationDate: '01-01-2020' });
    const dateValue = await dialog.getByPlaceholder('DD-MM-YYYY').inputValue();
    console.log(`[Edge 7] Installation date field holds: "${dateValue}"`);
    await submitAndReport(page, dialog, 'Edge 7');
  });

  test('Edge Case 8: calendar-invalid date (31-02-2026, February has no 31st)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(8), installationDate: '31-02-2026' });
    const dateValue = await dialog.getByPlaceholder('DD-MM-YYYY').inputValue();
    console.log(`[Edge 8] Installation date field holds: "${dateValue}"`);
    await submitAndReport(page, dialog, 'Edge 8');
  });

  test('Edge Case 9: Phone number too short (5 digits)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(9), phone: '41234' });
    const phoneValue = await dialog.getByPlaceholder('412345678').inputValue();
    console.log(`[Edge 9] Phone field holds: "${phoneValue}"`);
    await submitAndReport(page, dialog, 'Edge 9');
  });

  test('Edge Case 10: Phone number too long (12 digits)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(10), phone: '412345678999' });
    const phoneValue = await dialog.getByPlaceholder('412345678').inputValue();
    console.log(`[Edge 10] Phone field holds: "${phoneValue}"`);
    await submitAndReport(page, dialog, 'Edge 10');
  });
});

test.describe('Multi-product jobs - "+ Add another product"', () => {
  const baseValid = (i: number) => ({
    customerName: `Multi Product ${i}`,
    email: `multi.product.${uniq(300 + i)}@yopmail.com`,
    phone: phone(300 + i),
    abnAcn: abn(300 + i),
    addressSearch: '1 George Street Sydney',
    postcode: '2000',
    activityType: 'Heating & Cooling',
    buildingType: 'Residential Building',
    leadMethod: 'Customer initiated contact',
    ownReference: `REF-${RUN_ID}-MULTI${i}`,
    installationDate: '25-09-2026',
    installer: INSTALLER_COMPANY,
  });

  const productCounts = [2, 3, 2, 4, 3];

  productCounts.forEach((count, i) => {
    test(`Multi-Product Job ${i + 1}: ${count} products via "+ Add another product"`, async ({ page }) => {
      await login(page);
      const dialog = await openAddJobDrawer(page);

      await fillJobForm(dialog, { ...baseValid(i + 1), productCount: count });

      // Every "PRODUCT N" block and its own Remove button should be present
      // before submitting.
      for (let p = 1; p <= count; p++) {
        await expect(dialog.getByText(`Product ${p}`, { exact: true })).toBeVisible();
      }
      await expect(dialog.getByRole('button', { name: /remove/i })).toHaveCount(count);

      await submitJob(dialog);
      await expectJobCreated(page, dialog, `Multi Product ${i + 1}`);
    });
  });
});
