import { expect, Page, APIRequestContext } from '@playwright/test';
import fs from 'fs';

export const FOOD_ID = process.env.FOOD_ID!;
export const EDIT_URL = `/foods/edit/${FOOD_ID}`;
const API_URL = `/api/v1/food-search/edit/${FOOD_ID}`;

export async function openEdit(page: Page) {
  await page.goto(EDIT_URL);
  await expect(page.getByRole('textbox', { name: 'Serving name' }).first()).toBeVisible();
}

/** Field locators for serving card `i` (0-based). */
export function serving(page: Page, i: number) {
  return {
    name: page.getByRole('textbox', { name: 'Serving name' }).nth(i),
    weight: page.getByRole('spinbutton', { name: 'Weight / serving' }).nth(i),
    unit: page.getByRole('textbox', { name: 'Weight unit' }).nth(i),
    calories: page.getByRole('spinbutton', { name: 'Calories (kcal)' }).nth(i),
    protein: page.getByRole('spinbutton', { name: 'Protein (g)' }).nth(i),
    carbs: page.getByRole('spinbutton', { name: 'Carbs (g)' }).nth(i),
    fat: page.getByRole('spinbutton', { name: 'Fat (g)' }).nth(i),
    fiber: page.getByRole('spinbutton', { name: 'Fiber (g)' }).nth(i),
    alcohol: page.getByRole('spinbutton', { name: 'Alcohol (ml)' }).nth(i),
    isDefault: page.getByRole('radio', { name: 'Set as default' }).nth(i),
    del: page.getByRole('button', { name: 'Delete serving' }).nth(i),
  };
}

export const updateBtn = (page: Page) => page.getByRole('button', { name: 'Update' });

/** Click Update and wait for the PUT; returns the response status. */
export async function save(page: Page): Promise<number> {
  const [res] = await Promise.all([
    page.waitForResponse((r) => r.request().method() === 'PUT' && r.url().includes('/food-search/edit/')),
    updateBtn(page).click(),
  ]);
  return res.status();
}

/** Puts the food back to its original state (captured in auth.setup). */
export async function restoreOriginal(request: APIRequestContext) {
  const orig = JSON.parse(fs.readFileSync('.auth/original.json', 'utf8'));
  const res = await request.put(API_URL, { data: orig.data, headers: orig.headers });
  expect(res.ok(), 'restore original food data').toBeTruthy();
}

export const ORIGINAL = () => JSON.parse(fs.readFileSync('.auth/original.json', 'utf8')).data;
