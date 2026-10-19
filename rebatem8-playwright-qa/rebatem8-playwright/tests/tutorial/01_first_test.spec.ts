import { test, expect } from '@playwright/test';

// Tell Playwright this test doesn't need the rebatem8 authentication session
test.use({ storageState: { cookies: [], origins: [] } });

test('Lesson 1: My very first Playwright test', async ({ page }) => {
  // Step 1: Open the official Playwright TodoMVC demo website
  console.log('1. Navigating to the demo website...');
  await page.goto('https://demo.playwright.dev/todomvc/#/');

  // Step 2: Web-First Assertion - verify the page title
  console.log('2. Checking page title...');
  await expect(page).toHaveTitle('React • TodoMVC');

  // Step 3: Locate the input field using a user-facing locator (placeholder)
  const todoInput = page.getByPlaceholder('What needs to be done?');
  await expect(todoInput).toBeVisible();

  // Step 4: Add first item to the list
  console.log('3. Typing and pressing Enter...');
  await todoInput.fill('Learn Playwright Automation');
  await todoInput.press('Enter');

  // Step 5: Add second item
  await todoInput.fill('Master TypeScript');
  await todoInput.press('Enter');

  // Step 6: Verify both items were added and are visible on the screen
  const todoItems = page.getByTestId('todo-title');
  await expect(todoItems).toHaveCount(2);
  await expect(todoItems.first()).toHaveText('Learn Playwright Automation');
  await expect(todoItems.nth(1)).toHaveText('Master TypeScript');

  // Step 7: Check off the first item
  console.log('4. Checking off the first todo item...');
  const firstCheckbox = page.getByRole('listitem').filter({ hasText: 'Learn Playwright Automation' }).getByRole('checkbox');
  await firstCheckbox.check();
  await expect(firstCheckbox).toBeChecked();

  console.log('🎉 Lesson 1 test passed successfully!');
});
