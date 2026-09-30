import { test, expect, Page } from '@playwright/test';
import { openEdit, serving, updateBtn, save, restoreOriginal, ORIGINAL, EDIT_URL } from './helpers';

// Automates the TestRail cases TC-001..TC-050 for Foods > Edit > Servings & nutrients.
// Every test mutates the shared staging food, so it is restored via API after each test.
test.afterEach(async ({ request }) => {
  await restoreOriginal(request);
});

const NEEDS_CONSUMER_APP =
  'Admin edit page has no nutrition calculation UI; needs the consumer app/API (nutrition_per_100g x grams / 100).';

type Field = 'name' | 'weight' | 'unit' | 'calories' | 'protein' | 'carbs' | 'fat' | 'fiber' | 'alcohol';

/** Fill fields of serving card i. */
async function fillServing(page: Page, i: number, d: Partial<Record<Field, string>>) {
  const s = serving(page, i);
  for (const [k, v] of Object.entries(d)) await s[k as Field].fill(v as string);
}

const confirmIfAsked = async (page: Page) => {
  const dlg = page.getByRole('dialog');
  if (await dlg.isVisible({ timeout: 1000 }).catch(() => false)) {
    await dlg.getByRole('button', { name: /delete|yes|confirm|ok/i }).click();
  }
};

const saveAndVerify = async (page: Page, field: Field, value: string) => {
  await openEdit(page);
  await serving(page, 0)[field].fill(value);
  expect(await save(page)).toBe(200);
  await openEdit(page);
  await expect(serving(page, 0)[field]).toHaveValue(value);
};

// Validation: no PUT should be sent and a message should show on the field.
const expectRejected = async (page: Page, field: Field, value: string, msg: RegExp) => {
  await openEdit(page);
  let put = 0;
  page.on('request', (r) => {
    if (r.method() === 'PUT') put++;
  });
  await serving(page, 0)[field].fill(value);
  await updateBtn(page).click();
  await expect(page.getByText(msg).first()).toBeVisible();
  await page.waitForTimeout(500);
  expect(put, 'no save request should be sent').toBe(0);
  expect(page.url()).toContain(EDIT_URL);
};

test.describe('Serving UI', () => {
  test('TC-001 serving section displays all controls', async ({ page }) => {
    await openEdit(page);
    await expect(page.getByRole('heading', { name: 'Servings & nutrients' })).toBeVisible();
    const s = serving(page, 0);
    for (const f of [s.name, s.weight, s.unit, s.calories, s.protein, s.carbs, s.fat, s.fiber, s.alcohol, s.isDefault, s.del]) {
      await expect(f).toBeVisible();
    }
    await expect(updateBtn(page)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add serving' })).toBeVisible();
  });

  test('TC-002 existing serving details populated', async ({ page }) => {
    await openEdit(page);
    const o = ORIGINAL().servingFactor;
    for (let i = 0; i < o.length; i++) {
      const s = serving(page, i);
      await expect(s.name).toHaveValue(o[i].name);
      await expect(s.weight).toHaveValue(String(o[i].weightPerServing.amount));
      await expect(s.unit).toHaveValue(o[i].weightPerServing.unit);
      await expect(s.calories).toHaveValue(String(o[i].calories));
      await expect(s.protein).toHaveValue(String(o[i].nutrients.protein.amount));
      await expect(s.carbs).toHaveValue(String(o[i].nutrients.carbs.amount));
      await expect(s.fat).toHaveValue(String(o[i].nutrients.fat.amount));
    }
  });

  test('TC-003 create new serving with valid data', async ({ page }) => {
    await openEdit(page);
    await page.getByRole('button', { name: 'Add serving' }).click();
    await fillServing(page, 2, { name: 'QA serving', weight: '50', unit: 'g', calories: '100', protein: '10', carbs: '5', fat: '4', fiber: '2', alcohol: '0' });
    expect(await save(page)).toBe(200);
    await openEdit(page);
    const s = serving(page, 2);
    await expect(s.name).toHaveValue('QA serving');
    await expect(s.weight).toHaveValue('50');
    await expect(s.calories).toHaveValue('100');
    await expect(s.protein).toHaveValue('10');
    await expect(s.fiber).toHaveValue('2');
  });

  test('TC-004 weight accepts whole number', ({ page }) => saveAndVerify(page, 'weight', '50'));
  test('TC-005 weight accepts decimal', ({ page }) => saveAndVerify(page, 'weight', '45.5'));
  test('TC-006 serving name accepts text', ({ page }) => saveAndVerify(page, 'name', '0.5 serving QA'));
  test('TC-007 weight unit editable', ({ page }) => saveAndVerify(page, 'unit', 'ml'));
  test('TC-008 calories accepts numeric', ({ page }) => saveAndVerify(page, 'calories', '267'));
  test('TC-009 protein accepts decimal', ({ page }) => saveAndVerify(page, 'protein', '24.4'));
  test('TC-010 carbs accepts decimal', ({ page }) => saveAndVerify(page, 'carbs', '2.7'));
  test('TC-011 fat accepts decimal', ({ page }) => saveAndVerify(page, 'fat', '19.8'));
  test('TC-012 fiber accepts numeric', ({ page }) => saveAndVerify(page, 'fiber', '3'));
  test('TC-013 alcohol accepts zero', ({ page }) => saveAndVerify(page, 'alcohol', '0'));

  test('TC-014 zero nutrition values can be saved', async ({ page }) => {
    await openEdit(page);
    await fillServing(page, 0, { calories: '0', protein: '0', carbs: '0', fat: '0', fiber: '0', alcohol: '0' });
    expect(await save(page)).toBe(200);
    await openEdit(page);
    for (const f of ['calories', 'protein', 'carbs', 'fat', 'fiber', 'alcohol'] as Field[]) {
      await expect(serving(page, 0)[f]).toHaveValue('0');
    }
  });

  test('TC-015 negative calories rejected', ({ page }) => expectRejected(page, 'calories', '-100', /Must be >= 0/));
  test('TC-016 negative serving weight rejected', ({ page }) => expectRejected(page, 'weight', '-50', /Must be >= 0|greater than 0|must be/i));

  test('TC-017 letters cannot be entered in numeric fields', async ({ page }) => {
    await openEdit(page);
    for (const f of ['weight', 'calories', 'protein', 'carbs', 'fat', 'fiber', 'alcohol'] as Field[]) {
      const el = serving(page, 0)[f];
      await el.click();
      await el.press('Control+a');
      await page.keyboard.type('abc');
      expect(await el.inputValue(), f).not.toMatch(/[a-z]/i);
    }
  });

  test('TC-018 empty serving name validation', ({ page }) => expectRejected(page, 'name', '', /Required/));
  test('TC-019 empty weight validation', ({ page }) => expectRejected(page, 'weight', '', /Required|must be/i));
  test('TC-020 empty weight unit validation', ({ page }) => expectRejected(page, 'unit', '', /Required/));

  test('TC-021 empty calories handling', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).calories.fill('');
    await updateBtn(page).click();
    await page.waitForTimeout(1500);
    // Either validation blocks it, or it saves - but never NaN/undefined.
    await expect(page.locator('body')).not.toContainText(/NaN|undefined/);
  });

  test('TC-022 empty macro fields handling', async ({ page }) => {
    await openEdit(page);
    await fillServing(page, 0, { protein: '', fat: '', carbs: '' });
    await updateBtn(page).click();
    await page.waitForTimeout(1500);
    await expect(page.locator('body')).not.toContainText(/NaN|undefined/);
  });

  test('TC-023 set serving 1 as default and persist', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).isDefault.check();
    expect(await save(page)).toBe(200);
    await openEdit(page);
    await expect(serving(page, 0).isDefault).toBeChecked();
    await expect(serving(page, 1).isDefault).not.toBeChecked();
  });

  test('TC-024 only one serving can be default', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).isDefault.check();
    await serving(page, 1).isDefault.check();
    await expect(page.getByRole('radio', { name: 'Set as default', checked: true })).toHaveCount(1);
  });

  test('TC-025 default persists after refresh', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).isDefault.check();
    expect(await save(page)).toBe(200);
    await openEdit(page);
    await page.reload();
    await expect(serving(page, 0).isDefault).toBeChecked();
  });

  test('TC-026 changing default removes previous default', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).isDefault.check();
    await expect(serving(page, 1).isDefault).not.toBeChecked();
  });

  test('TC-027 serving can be deleted', async ({ page }) => {
    await openEdit(page);
    await page.getByRole('button', { name: 'Add serving' }).click();
    const headings = page.getByRole('heading', { name: /^Serving \d+$/ });
    await expect(headings).toHaveCount(3);
    await serving(page, 2).del.click();
    await confirmIfAsked(page);
    await expect(headings).toHaveCount(2);
  });

  test('TC-028 deleting default serving leaves a valid default state', async ({ page }) => {
    await openEdit(page);
    await serving(page, 1).del.click(); // serving 2 is the default
    await confirmIfAsked(page);
    await expect(page.getByRole('heading', { name: /^Serving \d+$/ })).toHaveCount(1);
    // A remaining serving should be auto-assigned as default (or save blocked) - never 2+ defaults.
    const checked = await page.getByRole('radio', { name: 'Set as default', checked: true }).count();
    expect(checked).toBeLessThanOrEqual(1);
  });

  test('TC-029 update saves all fields together', async ({ page }) => {
    await openEdit(page);
    const d = { name: 'QA all fields', weight: '75', unit: 'g', calories: '199', protein: '12.5', carbs: '7.5', fat: '3.5', fiber: '1.5', alcohol: '0.5' };
    await fillServing(page, 0, d);
    expect(await save(page)).toBe(200);
    await openEdit(page);
    for (const [k, v] of Object.entries(d)) await expect(serving(page, 0)[k as Field], k).toHaveValue(v);
  });

  test('TC-030 cancel discards changes', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).calories.fill('999');
    await page.getByRole('button', { name: 'Cancel' }).click();
    await openEdit(page);
    await expect(serving(page, 0).calories).toHaveValue(String(ORIGINAL().servingFactor[0].calories));
  });

  test('TC-031 saved values remain after reopening', async ({ page }) => {
    await openEdit(page);
    await serving(page, 1).calories.fill('123');
    expect(await save(page)).toBe(200);
    await page.goto('/foods');
    await openEdit(page);
    await expect(serving(page, 1).calories).toHaveValue('123');
  });
});

test.describe('Stored nutrition data (calculation inputs)', () => {
  test('TC-032 100g serving keeps source per-100g values exactly', async ({ page }) => {
    await openEdit(page);
    await fillServing(page, 0, { weight: '100', unit: 'g', calories: '267', protein: '24.4', fat: '19.8', carbs: '2.7' });
    expect(await save(page)).toBe(200);
    await openEdit(page);
    const s = serving(page, 0);
    await expect(s.calories).toHaveValue('267');
    await expect(s.protein).toHaveValue('24.4');
    await expect(s.fat).toHaveValue('19.8');
    await expect(s.carbs).toHaveValue('2.7');
  });

  for (const tc of [
    'TC-033 50g = 50%',
    'TC-034 200g = 2x',
    'TC-035 45g calculation',
    'TC-036 multiple servings (2 x 45g)',
    'TC-037 0.5 serving',
    'TC-038 3 servings',
    'TC-039 no compounding (45->90->45)',
    'TC-040 rounding behaviour',
    'TC-046 linear scaling across servings',
    'TC-050 downstream meal/summary reflects update',
  ]) {
    test(tc, async () => {
      test.skip(true, NEEDS_CONSUMER_APP);
    });
  }

  test('TC-041 very small serving weight', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).weight.fill('0.1');
    const status = await save(page);
    expect(status).toBe(200);
    await openEdit(page);
    await expect(serving(page, 0).weight).toHaveValue('0.1');
  });

  test('TC-042 extremely large serving weight is validated', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).weight.fill('999999');
    await updateBtn(page).click();
    await expect(page.getByText(/max|maximum|must be <=|too large|less than/i).first(), 'expected a max-value validation').toBeVisible({ timeout: 3000 });
  });

  test('TC-043 duplicate serving name handling', async ({ page }) => {
    await openEdit(page);
    await serving(page, 1).name.fill(await serving(page, 0).name.inputValue());
    await updateBtn(page).click();
    await expect(page.getByText(/duplicate|already exists|unique/i).first(), 'expected duplicate-name validation').toBeVisible({ timeout: 3000 });
  });

  test('TC-044 abnormally high OpenFoodFacts values are stored unchanged', async ({ page }) => {
    await openEdit(page);
    await fillServing(page, 0, { calories: '267', protein: '24.4', fat: '19.8', carbs: '2.7' });
    expect(await save(page)).toBe(200);
    await openEdit(page);
    await expect(serving(page, 0).protein).toHaveValue('24.4');
  });

  test('TC-045 missing nutrition value never shows NaN/undefined', async ({ page }) => {
    await openEdit(page);
    await serving(page, 0).protein.fill('');
    await updateBtn(page).click();
    await page.waitForTimeout(1500);
    await expect(page.locator('body')).not.toContainText(/NaN|undefined/);
    await openEdit(page);
    await expect(page.locator('body')).not.toContainText(/NaN|undefined/);
  });

  test('TC-047 update with unchanged data succeeds', async ({ page }) => {
    await openEdit(page);
    expect(await save(page)).toBe(200);
    await expect(page).toHaveURL(/\/foods$/);
  });

  test('TC-048 rapid multiple Update clicks send a single request', async ({ page }) => {
    await openEdit(page);
    let puts = 0;
    page.on('request', (r) => {
      if (r.method() === 'PUT') puts++;
    });
    await updateBtn(page).click({ clickCount: 3, delay: 20 }).catch(() => {});
    await page.waitForTimeout(2500);
    expect(puts).toBe(1);
  });

  test('TC-049 API failure keeps user on edit page', async ({ page }) => {
    await openEdit(page);
    await page.route('**/food-search/edit/**', (route) =>
      route.request().method() === 'PUT' ? route.fulfill({ status: 500, body: '{"message":"boom"}' }) : route.continue(),
    );
    await serving(page, 0).calories.fill('321');
    await updateBtn(page).click();
    await page.waitForTimeout(2000);
    expect(page.url()).toContain(EDIT_URL);
  });
});
