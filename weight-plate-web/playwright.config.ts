import { defineConfig } from '@playwright/test';

try { process.loadEnvFile('.env'); } catch { /* .env optional */ }

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  workers: 1, // tests mutate one shared staging food, so they must run serially
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL || 'https://weighplatestage.softwareco.com',
    channel: 'chrome',
    headless: false,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    {
      name: 'chrome',
      testMatch: /.*\.spec\.ts/,
      dependencies: ['setup'],
      use: { storageState: '.auth/user.json' },
    },
  ],
});
