import { test as base } from '@playwright/test';
import { LoginPage, DashboardPage } from '@pages/index';
import { LoginModule } from '@modules/index';

type Fixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  loginModule: LoginModule;
  /** OTP-bypass fixture: a fully authenticated session for the QA account. */
  loggedIn: void;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
  loginModule: async ({ page, loginPage, dashboardPage }, use) => {
    await use(new LoginModule(page, loginPage, dashboardPage));
  },
  loggedIn: async ({ loginModule }, use) => {
    await loginModule.loginWithMobile();
    await use();
  },
});

export { expect } from '@playwright/test';
