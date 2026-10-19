export const sauceUsers = {
  standard: { username: 'standard_user', password: 'secret_sauce' },
  lockedOut: { username: 'locked_out_user', password: 'secret_sauce' },
} as const;

export const products = {
  backpack: 'Sauce Labs Backpack',
  bikeLight: 'Sauce Labs Bike Light',
  boltTShirt: 'Sauce Labs Bolt T-Shirt',
} as const;

export const fakeStoreUsers = [
  { username: 'johnd', password: 'm38rmF$', userId: 1 },
  { username: 'mor_2314', password: '83r5^_', userId: 2 },
  { username: 'kevinryan', password: 'kev02937@', userId: 3 },
] as const;
