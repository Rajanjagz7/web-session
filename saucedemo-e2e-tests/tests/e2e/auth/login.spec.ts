import { test, expect } from '../../../fixtures/pages.fixture';
import { users } from '../../../utils/test-data';

test.describe('Login', () => {
  test.beforeEach(async ({ loginPage }) => {
    await loginPage.goto();
  });

  test('should login with valid standard user credentials @smoke', async ({ page, loginPage }) => {
    await loginPage.login(users.standard.username, users.standard.password);
    await expect(page).toHaveURL(/inventory\.html/);
    await expect(page.getByTestId('title')).toHaveText('Products');
  });

  test('should show error for locked out user', async ({ loginPage }) => {
    await loginPage.login(users.lockedOut.username, users.lockedOut.password);
    await loginPage.expectErrorMessage('Sorry, this user has been locked out.');
  });

  test('should show error for invalid password', async ({ loginPage }) => {
    await loginPage.login(users.standard.username, 'wrong-password');
    await loginPage.expectErrorMessage('Username and password do not match');
  });

  test('should show error when username is missing', async ({ loginPage }) => {
    await loginPage.login('', users.standard.password);
    await loginPage.expectErrorMessage('Username is required');
  });

  test('should show error when password is missing', async ({ loginPage }) => {
    await loginPage.login(users.standard.username, '');
    await loginPage.expectErrorMessage('Password is required');
  });

  test('should show error when both username and password are empty', async ({ loginPage }) => {
    await loginPage.login('', '');
    await loginPage.expectErrorMessage('Username is required');
  });

  test('should reject a username with the wrong case', async ({ loginPage }) => {
    await loginPage.login('Standard_User', users.standard.password);
    await loginPage.expectErrorMessage('Username and password do not match');
  });

  test('should reject a valid username with wrong-case password', async ({ loginPage }) => {
    await loginPage.login(users.standard.username, 'Secret_Sauce');
    await loginPage.expectErrorMessage('Username and password do not match');
  });

  test('should reject a username with leading/trailing whitespace', async ({ loginPage }) => {
    await loginPage.login(`  ${users.standard.username}  `, users.standard.password);
    await loginPage.expectErrorMessage('Username and password do not match');
  });

  test('should not allow a SQL-injection-style username to bypass login', async ({
    page,
    loginPage,
  }) => {
    await loginPage.login(`' OR '1'='1`, `' OR '1'='1`);
    await loginPage.expectErrorMessage('Username and password do not match');
    await expect(page).not.toHaveURL(/inventory\.html/);
  });

  test('should not allow an unregistered username to log in', async ({ loginPage }) => {
    await loginPage.login('not_a_real_user', 'not_a_real_password');
    await loginPage.expectErrorMessage('Username and password do not match');
  });

  test('should clear the error banner after a subsequent valid login', async ({
    page,
    loginPage,
  }) => {
    await loginPage.login(users.standard.username, 'wrong-password');
    await loginPage.expectErrorMessage('Username and password do not match');

    await loginPage.login(users.standard.username, users.standard.password);
    await expect(page).toHaveURL(/inventory\.html/);
    await expect(loginPage.errorMessage).toBeHidden();
  });
});
