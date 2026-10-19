import { test, expect } from '@playwright/test';
import { login, openAddProjectDrawer } from './helpers';

test('shows validation errors when submitting an empty Add Project form', async ({ page }) => {
  await login(page);
  const dialog = await openAddProjectDrawer(page);

  await dialog.getByRole('button', { name: /add project/i }).click();

  for (const message of [
    'Project Name is required',
    'Company is required',
    'Benefit Type is required',
    'Consumer Name is required',
    'Email is required',
    'Phone Number is required',
    'Address is required',
    'Postcode is required',
  ]) {
    await expect(dialog.getByText(message, { exact: true })).toBeVisible();
  }

  // The form must not have actually submitted.
  await expect(page.getByPlaceholder('Enter Project Name')).toBeVisible();
});

test('shows format validation errors for invalid email and phone number', async ({ page }) => {
  await login(page);
  const dialog = await openAddProjectDrawer(page);

  await dialog.getByPlaceholder('Enter Consumer Name').fill('Test Invalid');
  await dialog.getByPlaceholder('Enter Email ID').fill('not-an-email');
  const phoneField = dialog.getByPlaceholder('Enter Phone Number');
  await phoneField.click();
  await page.keyboard.type('123');

  await dialog.getByRole('button', { name: /add project/i }).click();

  await expect(dialog.getByText('Email Id is invalid', { exact: true })).toBeVisible();
  await expect(dialog.getByText('Phone Number must be 10 digits', { exact: true })).toBeVisible();
  await expect(page.getByPlaceholder('Enter Project Name')).toBeVisible();
});
