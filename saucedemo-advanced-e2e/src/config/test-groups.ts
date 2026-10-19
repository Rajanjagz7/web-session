export const Priority = {
  P0: '@P0',
  P1: '@P1',
  P2: '@P2',
} as const;

export const Feature = {
  Login: '@Login',
  Inventory: '@Inventory',
  Cart: '@Cart',
  Checkout: '@Checkout',
  AccessControl: '@AccessControl',
  Api: '@Api',
} as const;

export const Suite = {
  Smoke: '@Smoke',
  Regression: '@Regression',
} as const;
