import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 60000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { open: 'never' }]
  ],
  use: {
    baseURL: 'https://sunriseclinic.dev.ozmed.health',
    headless: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'setup',
      testMatch: /.*auth\.setup\.spec\.ts/,
    },
    {
      name: 'ozmed-tests',
      testMatch: /.*ozmed\/.*\.spec\.ts/,
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'auth.json',
      },
    },
    {
      name: 'general',
      testMatch: /.*first-test\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
      }
    },
    {
      name: 'nsw-e2e',
      testMatch: /.*(nsw-rebatem8|nsw-e2e\/.*)\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
      }
    }
  ],
});
