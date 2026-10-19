import { test as base } from '@playwright/test';
import { LoginPage, InventoryPage, CartPage, CheckoutPage, NavPage } from '@pages/index';
import {
  LoginModule,
  InventoryModule,
  CartModule,
  CheckoutModule,
  NavModule,
  AccessControlModule,
} from '@modules/index';
import { AuthApi, ProductApi, CartApi } from '@api/index';

type PageFixtures = {
  loginPage: LoginPage;
  inventoryPage: InventoryPage;
  cartPage: CartPage;
  checkoutPage: CheckoutPage;
  navPage: NavPage;
};

type ModuleFixtures = {
  loginModule: LoginModule;
  inventoryModule: InventoryModule;
  cartModule: CartModule;
  checkoutModule: CheckoutModule;
  navModule: NavModule;
  accessControlModule: AccessControlModule;
};

type ApiFixtures = {
  authApi: AuthApi;
  productApi: ProductApi;
  cartApi: CartApi;
};

export const test = base.extend<PageFixtures & ModuleFixtures & ApiFixtures>({
  // Layer 2: Pages
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  inventoryPage: async ({ page }, use) => {
    await use(new InventoryPage(page));
  },
  cartPage: async ({ page }, use) => {
    await use(new CartPage(page));
  },
  checkoutPage: async ({ page }, use) => {
    await use(new CheckoutPage(page));
  },
  navPage: async ({ page }, use) => {
    await use(new NavPage(page));
  },

  // Layer 3: Modules
  loginModule: async ({ page, loginPage }, use) => {
    await use(new LoginModule(page, loginPage));
  },
  inventoryModule: async ({ page, inventoryPage }, use) => {
    await use(new InventoryModule(page, inventoryPage));
  },
  cartModule: async ({ page, cartPage }, use) => {
    await use(new CartModule(page, cartPage));
  },
  checkoutModule: async ({ page, checkoutPage }, use) => {
    await use(new CheckoutModule(page, checkoutPage));
  },
  navModule: async ({ page, navPage }, use) => {
    await use(new NavModule(page, navPage));
  },
  accessControlModule: async ({ page, loginPage }, use) => {
    await use(new AccessControlModule(page, loginPage));
  },

  // Layer 5: API
  authApi: async ({ request }, use) => {
    await use(new AuthApi(request));
  },
  productApi: async ({ request }, use) => {
    await use(new ProductApi(request));
  },
  cartApi: async ({ request }, use) => {
    await use(new CartApi(request));
  },
});

export { expect } from '@playwright/test';
