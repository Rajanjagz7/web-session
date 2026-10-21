import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testIgnore: /newsunrise|scratch/,
  timeout: 30_000,
  fullyParallel: true,
  retries: 0,
  outputDir: 'test-results-mobile',
  reporter: [['json', { outputFile: 'mobile-results.json' }], ['html', { outputFolder: 'playwright-report-mobile', open: 'never' }], ['line']],
  use: {
    baseURL: process.env.BASE_URL || 'https://bcppqf-4m.myshopify.com',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'Pixel 7', use: { ...devices['Pixel 7'] } },
    { name: 'Galaxy S9+', use: { ...devices['Galaxy S9+'] } },
    { name: 'iPhone SE', use: { ...devices['iPhone SE'] } },
    { name: 'iPhone 14', use: { ...devices['iPhone 14'] } },
    { name: 'iPad Mini', use: { ...devices['iPad Mini'] } },
  ],
});
