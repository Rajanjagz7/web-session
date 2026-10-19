import { test } from '@fixtures';
import { sauceUsers } from '@testdata/users';

test.describe('@P0 @Login Login', () => {
  test('should login with valid standard user credentials @Smoke', async ({ loginModule }) => {
    await test.step('Login with standard user', async () => {
      await loginModule.doLogin(sauceUsers.standard.username, sauceUsers.standard.password);
    });

    await test.step('Verify redirect to inventory page', async () => {
      await loginModule.verifyLoggedIn();
    });
  });

  test('should show error for locked out user', async ({ loginModule }) => {
    await test.step('Attempt login with locked out user', async () => {
      await loginModule.doLogin(sauceUsers.lockedOut.username, sauceUsers.lockedOut.password);
    });

    await test.step('Verify locked-out error message', async () => {
      await loginModule.verifyLoginFailed('Sorry, this user has been locked out.');
    });
  });

  test('should show error for invalid password', async ({ loginModule }) => {
    await test.step('Attempt login with wrong password', async () => {
      await loginModule.doLogin(sauceUsers.standard.username, 'wrong-password');
    });

    await test.step('Verify credential mismatch error', async () => {
      await loginModule.verifyLoginFailed('Username and password do not match');
    });
  });

  test('should show error when username is missing', async ({ loginModule }) => {
    await test.step('Submit with empty username', async () => {
      await loginModule.doLogin('', sauceUsers.standard.password);
    });

    await test.step('Verify required-field error', async () => {
      await loginModule.verifyLoginFailed('Username is required');
    });
  });

  test('should clear the error banner after a subsequent valid login', async ({
    loginModule,
  }) => {
    await test.step('Fail login once', async () => {
      await loginModule.doLogin(sauceUsers.standard.username, 'wrong-password');
      await loginModule.verifyLoginFailed('Username and password do not match');
    });

    await test.step('Retry with valid credentials', async () => {
      await loginModule.doLogin(sauceUsers.standard.username, sauceUsers.standard.password);
      await loginModule.verifyLoggedIn();
      await loginModule.verifyErrorCleared();
    });
  });
});
