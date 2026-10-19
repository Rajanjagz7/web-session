import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import { config as appConfig } from './src/config';

dotenv.config();

export default defineConfig({
  testDir: './src/tests',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: process.env.CI
    ? [
        ['./src/utils/CustomTTAReporter.ts'],
        ['blob', { outputDir: 'blob-report' }],
        ['json', { outputFile: 'test-results/results.json' }],
        ['github'],
      ]
    : [
        ['./src/utils/CustomTTAReporter.ts'],
        ['html', { outputFolder: 'playwright-report', open: 'never' }],
        ['json', { outputFile: 'test-results/results.json' }],
        ['list'],
      ],
  use: {
    testIdAttribute: 'data-test',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: 'ui-chromium',
      testDir: './src/tests/ui',
      use: { ...devices['Desktop Chrome'], baseURL: appConfig.ui.baseUrl },
    },
    {
      name: 'ui-firefox',
      testDir: './src/tests/ui',
      use: { ...devices['Desktop Firefox'], baseURL: appConfig.ui.baseUrl },
    },
    {
      name: 'ui-webkit',
      testDir: './src/tests/ui',
      use: { ...devices['Desktop Safari'], baseURL: appConfig.ui.baseUrl },
    },
    {
      name: 'ui-mobile-chrome',
      testDir: './src/tests/ui',
      use: { ...devices['Pixel 5'], baseURL: appConfig.ui.baseUrl },
    },
    {
      name: 'api',
      testDir: './src/tests/api',
      use: { baseURL: appConfig.api.baseUrl },
    },
  ],
});
