import { test, expect } from '@playwright/test';
import { openEdit, serving, ORIGINAL } from './helpers';

// Data-integrity checks for the food's saved servings (read-only, nothing is modified).
// Failures here point at suspicious data or missing validation, not at UI bugs.
const servings = () => ORIGINAL().servingFactor as any[];

test.describe('Saved food data integrity', () => {
  test('DATA-01 every serving has the same "amount" (serving count)', async () => {
    const amounts = servings().map((s) => s.amount);
    expect(new Set(amounts).size, `amounts were ${JSON.stringify(amounts)}`).toBe(1);
  });

  test('DATA-02 calories are consistent with macros (4p + 4c + 9f, +/-25%)', async () => {
    for (const s of servings()) {
      const n = s.nutrients;
      const est = 4 * n.protein.amount + 4 * n.carbs.amount + 9 * n.fat.amount;
      if (s.calories === 0 && est === 0) continue;
      const diff = Math.abs(est - s.calories) / Math.max(est, s.calories);
      expect(diff, `${s.name}: stated ${s.calories} kcal vs ${est} kcal from macros`).toBeLessThanOrEqual(0.25);
    }
  });

  test('DATA-03 servings scale with weight (0.5 serving ~ half of 1 serving)', async () => {
    const [a, b] = servings();
    const ratio = b.weightPerServing.amount / a.weightPerServing.amount;
    expect(b.calories, `${b.name} should be ~${a.calories * ratio} kcal`).toBeCloseTo(a.calories * ratio, -1);
    expect(b.nutrients.protein.amount).toBeCloseTo(a.nutrients.protein.amount * ratio, 0);
    expect(b.nutrients.fat.amount).toBeCloseTo(a.nutrients.fat.amount * ratio, 0);
    expect(b.nutrients.carbs.amount).toBeCloseTo(a.nutrients.carbs.amount * ratio, 0);
  });

  test('DATA-04 default serving has non-zero nutrition', async () => {
    const def = servings().find((s) => s.isDefault);
    expect(def, 'a default serving exists').toBeTruthy();
    expect(def.calories, `default serving "${def.name}" shows 0 kcal to users`).toBeGreaterThan(0);
  });

  test('DATA-05 exactly one default serving', async () => {
    expect(servings().filter((s) => s.isDefault)).toHaveLength(1);
  });

  test('DATA-06 units are consistent across servings (macro and alcohol units)', async () => {
    for (const key of ['protein', 'fat', 'carbs', 'fiber', 'alcohol']) {
      const units = servings().map((s) => s.nutrients[key].unit);
      expect(new Set(units).size, `${key} units were ${JSON.stringify(units)}`).toBe(1);
    }
  });

  test('DATA-07 serving name matches its weight', async () => {
    const [a, b] = servings();
    // "0.5 serving" should weigh half of "1 serving"
    expect(b.weightPerServing.amount).toBe(a.weightPerServing.amount * 0.5);
  });

  test('DATA-08 UI shows the same values as the saved data', async ({ page }) => {
    await openEdit(page);
    const list = servings();
    for (let i = 0; i < list.length; i++) {
      const s = serving(page, i);
      await expect(s.calories).toHaveValue(String(list[i].calories));
      await expect(s.weight).toHaveValue(String(list[i].weightPerServing.amount));
      await expect(s.isDefault).toBeChecked({ checked: list[i].isDefault });
    }
  });
});
