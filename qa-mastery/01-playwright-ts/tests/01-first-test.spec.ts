import { test, expect } from '@playwright/test';

test.describe('TodoMVC Application - Core Journey', () => {

  test.beforeEach(async ({ page }) => {
    // 1. Navigation: Navigate to the target web application
    await page.goto('https://demo.playwright.dev/todomvc/#/');
  });

  test('should allow a user to add new todo items', async ({ page }) => {
    // 2. Locate an element: Best practice is using user-facing locators
    // getByPlaceholder matches what real users see on screen
    const newTodoInput = page.getByPlaceholder('What needs to be done?');

    // 3. User Action: Type into the input and press Enter
    await newTodoInput.fill('Learn Playwright with TypeScript');
    await newTodoInput.press('Enter');

    await newTodoInput.fill('Master AI Test Engineering');
    await newTodoInput.press('Enter');

    // 4. Assertions: Validate that both items exist in the DOM
    const todoItems = page.getByTestId('todo-item');

    // Playwright auto-waits for these assertions to pass!
    await expect(todoItems).toHaveCount(2);
    await expect(todoItems.first()).toHaveText('Learn Playwright with TypeScript');
    await expect(todoItems.nth(1)).toHaveText('Master AI Test Engineering');
  });

  test('should allow a user to mark a todo item as completed', async ({ page }) => {
    const newTodoInput = page.getByPlaceholder('What needs to be done?');
    await newTodoInput.fill('Finish Phase 1 of QA Roadmap');
    await newTodoInput.press('Enter');

    const todoItem = page.getByTestId('todo-item').first();

    // Find the checkbox inside the todo item and check it
    const checkbox = todoItem.getByRole('checkbox');
    await checkbox.check();

    // Verify the checkbox is checked and item has 'completed' class
    await expect(checkbox).toBeChecked();
    await expect(todoItem).toHaveClass(/completed/);
  });
  test('should allow a uset to mark a todo item as delete', async ({ page }) => {
    const newTodoInput = page.getByPlaceholder('What needs to be done?')
    await newTodoInput.fill('Delete a todo item')
    await newTodoInput.press('Enter')
    const todoItem = page.getByTestId('todo-item').first()

  })
});

