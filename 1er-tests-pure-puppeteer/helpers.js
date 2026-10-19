// Puppeteer port of the Playwright NSW-jobs helpers (see
// ../1er-tests-pure-playwright/helpers.js for the source of truth on
// behaviour). Puppeteer has no getByRole/getByPlaceholder locator API, so
// these use CSS attribute selectors (placeholders) and the built-in `xpath/`
// query handler (text/role lookups) instead.

const { BASE_URL } = require('./config');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function xp(selector) {
  return `xpath/${selector}`;
}

/** Polls for an xpath match (optionally scoped to an ElementHandle) since ElementHandle has no waitForSelector. */
async function waitXPath(scope, xpath, { timeout = 15000, poll = 150 } = {}) {
  const start = Date.now();
  let lastErr;
  while (Date.now() - start < timeout) {
    try {
      const handle = await scope.$(xp(xpath));
      if (handle) {
        const box = await handle.boundingBox().catch(() => null);
        if (box) return handle;
      }
    } catch (err) {
      lastErr = err;
    }
    await sleep(poll);
  }
  throw new Error(`Timed out waiting for xpath: ${xpath}${lastErr ? ` (${lastErr.message})` : ''}`);
}

async function clearAndType(page, el, value) {
  await el.click({ clickCount: 3 });
  await page.keyboard.press('Backspace');
  await el.type(String(value), { delay: 10 });
}

async function fillByPlaceholder(page, placeholderSubstr, value) {
  const selector = `[placeholder*="${placeholderSubstr}" i]`;
  const el = await page.waitForSelector(selector, { visible: true, timeout: 15000 });
  await clearAndType(page, el, value);
}

async function clickByText(scope, page, tag, textSubstr) {
  const lower = textSubstr.toLowerCase();
  const tagCheck = tag === 'button' ? '(self::button or @role="button")' : `self::${tag}`;
  const xpath = `.//*[${tagCheck} and contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "${lower}")]`;
  const el = await waitXPath(scope, xpath);
  await el.click();
  return el;
}

async function login(page) {
  await page.goto(`${BASE_URL}/log-in`, { waitUntil: 'networkidle2' });
  await fillByPlaceholder(page, 'email', require('./config').EMAIL);
  await fillByPlaceholder(page, 'password', require('./config').PASSWORD);
  await clickByText(page, page, 'button', 'log in').catch(() => clickByText(page, page, 'button', 'sign in'));
  await waitXPath(page, `.//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add job')]`, { timeout: 20000 });
}

async function openAddJobDrawer(page) {
  await page.goto(`${BASE_URL}/jobs`, { waitUntil: 'networkidle2' });
  await sleep(800);
  await clickByText(page, page, 'button', 'add job');
  // The .drawer wrapper (role="dialog") has a zero-height bounding box even
  // when open - its .drawer-content child holds the real size - so only
  // wait for presence here, then rely on the customer-name field (which
  // does have real dimensions) for the actual visibility gate.
  const dialog = await page.waitForSelector('[role="dialog"]', { timeout: 20000 });
  await dialog.waitForSelector('[placeholder="Enter customer name"]', { visible: true, timeout: 10000 });
  return dialog;
}

/**
 * Finds the "*Label" text within `scope`, walks up to the nearest ancestor
 * that also contains a `.select__control`, and returns that control.
 * Mirrors 1er-tests-pure-playwright/helpers.js controlForLabel exactly,
 * just expressed as one relative XPath instead of chained locators.
 */
const UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const LOWER = 'abcdefghijklmnopqrstuvwxyz';
// Capitalization of field labels isn't consistent across activity types
// (e.g. "Original equipment" vs "Original Equipment"), so label matching
// must be case-insensitive - this translate() trick is XPath 1.0's
// standard workaround (no case-insensitive contains() in XPath 1.0).
function ciContains(expr, needle) {
  return `contains(translate(${expr}, "${UPPER}", "${LOWER}"), "${needle.toLowerCase()}")`;
}

async function controlForLabel(scope, labelText) {
  const has = ciContains('normalize-space(string(.))', labelText);
  const xpath =
    `.//*[${has} and not(.//*[${has}])]` +
    `/ancestor::*[.//*[contains(@class,"select__control")]][1]` +
    `//*[contains(@class,"select__control")][1]`;
  return waitXPath(scope, xpath);
}

async function fieldExists(scope, labelText) {
  const has = ciContains('normalize-space(string(.))', labelText);
  const el = await scope.$(xp(`.//*[${has}]`));
  return el !== null;
}

async function selectOption(scope, page, labelText, optionName) {
  const control = await controlForLabel(scope, labelText);
  await control.evaluate((el) => el.scrollIntoView({ block: 'center' }));
  await control.click();
  const optionXPath = `.//*[@role="option"][normalize-space(string(.))="${optionName}"]`;
  const option = await waitXPath(page, optionXPath);
  await option.click();
}

let variedOptionCounter = 0;
async function selectVariedOpenOption(page) {
  const options = await page.$$('[role="option"]');
  const count = options.length;
  const index = count > 0 ? variedOptionCounter % count : 0;
  variedOptionCounter++;
  if (count > 0) await options[index].click();
}

async function pickAddress(dialog, page, searchTerm) {
  const control = await controlForLabel(dialog, 'Site address');
  await control.evaluate((el) => el.scrollIntoView({ block: 'center' }));
  await control.click();
  await page.keyboard.type(searchTerm, { delay: 15 });
  await sleep(1200);
  const option = await waitXPath(page, `.//*[@role="option"]`);
  await option.click();
}

async function productContainers(dialog) {
  return dialog.$$('.border-dashed.border-gray-300');
}

async function fillProductBlock(container, page) {
  await selectOption(container, page, 'Original equipment', 'No existing system (new installation)');
  await sleep(500);
  if (await fieldExists(container, 'Brand')) {
    const brandControl = await controlForLabel(container, 'Brand');
    await brandControl.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await brandControl.click();
    await sleep(300);
    await selectVariedOpenOption(page);
    await sleep(500);
  }
  const modelControl = await controlForLabel(container, 'Model');
  await modelControl.evaluate((el) => el.scrollIntoView({ block: 'center' }));
  await modelControl.click();
  await sleep(300);
  await selectVariedOpenOption(page);
  await sleep(300);
}

/**
 * Fills whichever fields are present in `fields`. Order matters: Activity
 * type before Building type/New system, Installer before the Equipment
 * block (which only exists once an installer is chosen).
 */
async function fillJobForm(dialog, page, fields) {
  if (fields.customerName !== undefined) {
    const el = await dialog.waitForSelector('[placeholder="Enter customer name"]', { visible: true });
    await clearAndType(page, el, fields.customerName);
  }
  if (fields.email !== undefined) {
    const el = await dialog.waitForSelector('[placeholder="customer@email.com"]', { visible: true });
    await clearAndType(page, el, fields.email);
  }
  if (fields.phone !== undefined) {
    const el = await dialog.waitForSelector('[placeholder="412345678"]', { visible: true });
    await el.click();
    await page.keyboard.type(fields.phone, { delay: 10 });
  }
  if (fields.abnAcn !== undefined) {
    const el = await dialog.waitForSelector('[placeholder="12345678901"]', { visible: true });
    await clearAndType(page, el, fields.abnAcn);
  }
  if (fields.addressSearch !== undefined) {
    await pickAddress(dialog, page, fields.addressSearch);
  }
  if (fields.postcode !== undefined) {
    const el = await dialog.waitForSelector('[placeholder="2000"]', { visible: true });
    await clearAndType(page, el, fields.postcode);
  }
  if (fields.activityType !== undefined) {
    await selectOption(dialog, page, 'Activity type', fields.activityType);
  }
  if (fields.buildingType !== undefined) {
    await selectOption(dialog, page, 'Building type', fields.buildingType);
  }
  if (fields.newSystem !== undefined) {
    if (await fieldExists(dialog, 'New system')) {
      await selectOption(dialog, page, 'New system', fields.newSystem);
    }
  }
  if (fields.leadMethod !== undefined) {
    await selectOption(dialog, page, 'Method of lead generation', fields.leadMethod);
  }
  if (fields.ownReference !== undefined) {
    const el = await dialog.waitForSelector('[placeholder="REF-001"]', { visible: true });
    await clearAndType(page, el, fields.ownReference);
  }
  if (fields.installationDate !== undefined) {
    const el = await dialog.waitForSelector('[placeholder="DD-MM-YYYY"]', { visible: true });
    await el.click();
    await page.keyboard.type(fields.installationDate, { delay: 10 });
  }
  if (fields.installer !== undefined) {
    await selectOption(dialog, page, 'Installer (company)', fields.installer);
    await sleep(1200);
  }
  const productCount = fields.productCount ?? (fields.fillEquipment ? 1 : undefined);
  if (productCount !== undefined && productCount > 0) {
    for (let p = 1; p < productCount; p++) {
      await clickByText(dialog, page, 'button', 'add another product');
      await sleep(400);
    }
    const containers = await productContainers(dialog);
    for (let p = 0; p < productCount; p++) {
      await fillProductBlock(containers[p], page);
    }
  }
}

async function submitJob(dialog, page) {
  await clickByText(dialog, page, 'button', 'send engagement letter');
}

/**
 * Submits, waits, then reports whether the job was created or blocked -
 * mirrors submitAndReport in the Playwright helpers (always resolves rather
 * than asserting, since this is exploratory/data-creation, not assertions).
 */
async function submitAndReport(page, dialog, label) {
  await submitJob(dialog, page);
  await sleep(2500);
  const stillOpenEl = await dialog.$('[placeholder="Enter customer name"]');
  let stillOpen = false;
  if (stillOpenEl) {
    const box = await stillOpenEl.boundingBox().catch(() => null);
    stillOpen = box !== null;
  }
  if (stillOpen) {
    const text = await dialog.evaluate((el) => el.innerText).catch(() => '');
    console.log(`  [${label}] Result: submission BLOCKED. Dialog text:\n${text}`);
  } else {
    console.log(`  [${label}] Result: job CREATED.`);
  }
  return { created: !stillOpen };
}

module.exports = {
  sleep,
  login,
  openAddJobDrawer,
  controlForLabel,
  selectOption,
  fieldExists,
  pickAddress,
  fillJobForm,
  submitJob,
  submitAndReport,
};
