import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests', fullyParallel: false, workers: 1, retries: 0,
  globalSetup: './tests/global-setup.ts', globalTeardown: './tests/global-teardown.ts',
  timeout: 30000, expect: { timeout: 8000 },
  reporter: [['list'], ['html', {open: 'never'}], ['json', {outputFile: 'results/results.json'}]],
  outputDir: 'test-results',
  use: {
    baseURL: process.env.BASE_URL || 'https://nswdev.rebatem8.com.au',
    viewport: {width: 1440, height: 900},
    // Prevent credentials, cookies and business data entering traces/videos/screenshots.
    trace: 'off', screenshot: 'off', video: 'off',
    actionTimeout: 10000, navigationTimeout: 20000,
  },
  projects: [
    {name: 'chromium', use: {...devices['Desktop Chrome']}},
    ...(process.env.CROSS_BROWSER === '1' ? [
      {name: 'firefox', use: {...devices['Desktop Firefox']}},
      {name: 'webkit', use: {...devices['Desktop Safari']}}
    ] : []),
  ],
});
