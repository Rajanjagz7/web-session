const { EMAIL, PASSWORD } = require('./config');
const { expectVisible } = require('./runner');

async function login(page) {
  await page.goto('/log-in');
  await page.getByPlaceholder(/email/i).fill(EMAIL);
  await page.getByPlaceholder(/password/i).fill(PASSWORD);
  await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
  await page.getByRole('button', { name: /add job/i }).waitFor({ state: 'visible', timeout: 20000 });
}

async function openAddJobDrawer(page) {
  await page.goto('/jobs');
  await page.getByRole('button', { name: /add job/i }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByPlaceholder('Enter customer name').waitFor({ state: 'visible' });
  return dialog;
}

async function controlForLabel(scope, labelText) {
  const label = scope.getByText(labelText, { exact: false }).first();
  const fieldWrapper = label.locator('xpath=ancestor::*[.//*[contains(@class,"select__control")]][1]');
  return fieldWrapper.locator('.select__control').first();
}

async function selectOption(scope, labelText, optionName) {
  const control = await controlForLabel(scope, labelText);
  await control.scrollIntoViewIfNeeded();
  await control.click();
  await scope.page().getByRole('option', { name: optionName, exact: true }).click();
}

async function fieldExists(scope, labelText) {
  return (await scope.getByText(labelText, { exact: false }).count()) > 0;
}

let variedOptionCounter = 0;
async function selectVariedOpenOption(page) {
  const options = page.getByRole('option');
  const count = await options.count();
  const index = count > 0 ? variedOptionCounter % count : 0;
  variedOptionCounter++;
  await options.nth(index).click();
}

async function pickAddress(dialog, searchTerm) {
  const control = await controlForLabel(dialog, 'Site address');
  await control.scrollIntoViewIfNeeded();
  await control.click();
  await dialog.page().keyboard.type(searchTerm);
  await dialog.page().waitForTimeout(1200);
  await dialog.page().getByRole('option').first().click();
}

function productContainer(dialog, index) {
  return dialog.locator('.border-dashed.border-gray-300').nth(index);
}

async function fillProductBlock(container) {
  const page = container.page();
  await selectOption(container, 'Original equipment', 'No existing system (new installation)');
  await page.waitForTimeout(500);
  if (await fieldExists(container, 'Brand')) {
    const brandControl = await controlForLabel(container, 'Brand');
    await brandControl.scrollIntoViewIfNeeded();
    await brandControl.click();
    await page.waitForTimeout(300);
    await selectVariedOpenOption(page);
    await page.waitForTimeout(500);
  }
  const modelControl = await controlForLabel(container, 'Model');
  await modelControl.scrollIntoViewIfNeeded();
  await modelControl.click();
  await page.waitForTimeout(300);
  await selectVariedOpenOption(page);
  await page.waitForTimeout(300);
}

async function fillJobForm(dialog, fields) {
  const page = dialog.page();

  if (fields.customerName !== undefined) {
    await dialog.getByPlaceholder('Enter customer name').fill(fields.customerName);
  }
  if (fields.email !== undefined) {
    await dialog.getByPlaceholder('customer@email.com').fill(fields.email);
  }
  if (fields.phone !== undefined) {
    const phoneField = dialog.getByPlaceholder('412345678');
    await phoneField.click();
    await page.keyboard.type(fields.phone);
  }
  if (fields.abnAcn !== undefined) {
    await dialog.getByPlaceholder('12345678901').fill(fields.abnAcn);
  }
  if (fields.addressSearch !== undefined) {
    await pickAddress(dialog, fields.addressSearch);
  }
  if (fields.postcode !== undefined) {
    await dialog.getByPlaceholder('2000').fill(fields.postcode);
  }
  if (fields.activityType !== undefined) {
    await selectOption(dialog, 'Activity type', fields.activityType);
  }
  if (fields.buildingType !== undefined) {
    await selectOption(dialog, 'Building type', fields.buildingType);
  }
  if (fields.newSystem !== undefined) {
    if (await fieldExists(dialog, 'New system')) {
      await selectOption(dialog, 'New system', fields.newSystem);
    }
  }
  if (fields.leadMethod !== undefined) {
    await selectOption(dialog, 'Method of lead generation', fields.leadMethod);
  }
  if (fields.ownReference !== undefined) {
    await dialog.getByPlaceholder('REF-001').fill(fields.ownReference);
  }
  if (fields.installationDate !== undefined) {
    const dateField = dialog.getByPlaceholder('DD-MM-YYYY');
    await dateField.click();
    await page.keyboard.type(fields.installationDate);
  }
  if (fields.installer !== undefined) {
    await selectOption(dialog, 'Installer (company)', fields.installer);
    await page.waitForTimeout(500);
  }
  let productCount = fields.productCount ?? (fields.fillEquipment ? 1 : undefined);
  if (productCount !== undefined && productCount > 0) {
    const addProductBtn = dialog.getByRole('button', { name: /add another product/i });
    for (let p = 1; p < productCount; p++) {
      await addProductBtn.click();
      await page.waitForTimeout(400);
    }
    for (let p = 0; p < productCount; p++) {
      await fillProductBlock(productContainer(dialog, p));
    }
  }
}

async function submitJob(dialog) {
  await dialog.getByRole('button', { name: /send engagement letter/i }).click();
}

async function expectFieldError(dialog, message) {
  await expectVisible(dialog.getByText(message, { exact: true }));
}

async function submitAndReport(page, dialog, label) {
  await submitJob(dialog);
  await page.waitForTimeout(2500);
  const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
  if (stillOpen) {
    console.log(`  [${label}] Result: submission BLOCKED. Dialog text:\n` + (await dialog.innerText()));
  } else {
    console.log(`  [${label}] Result: job CREATED.`);
  }
  return { created: !stillOpen };
}

async function expectJobCreated(page, dialog, customerName) {
  await dialog.getByPlaceholder('Enter customer name').waitFor({ state: 'hidden', timeout: 15000 });
  await expectVisible(page.getByText(customerName, { exact: false }).first(), 15000);
}

async function openJobDetail(page, jobNumber) {
  await page.goto('/jobs');
  await page.getByPlaceholder('Search Jobs...').fill(jobNumber);
  await page.waitForTimeout(1200);
  await page.locator('table tbody tr').first().locator('svg, img, button').first().click();
  await page.getByRole('button', { name: 'Job Information', exact: true }).waitFor({ state: 'visible', timeout: 15000 });
}

async function openJobDetailTab(page, tabName) {
  await page.getByRole('button', { name: tabName, exact: true }).click();
  await page.waitForTimeout(1000);
}

module.exports = {
  login,
  openAddJobDrawer,
  controlForLabel,
  selectOption,
  fieldExists,
  pickAddress,
  fillJobForm,
  submitJob,
  expectFieldError,
  submitAndReport,
  expectJobCreated,
  openJobDetail,
  openJobDetailTab,
};
