import { defineConfig, devices } from '@playwright/test';
import 'dotenv/config';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  fullyParallel: false,
  retries: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: process.env.BASE_URL || 'https://nswdev.rebatem8.com.au',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    // viewport: null + --start-maximized makes Chrome open maximized
    // using the real screen size instead of Playwright's fixed default
    // viewport.
    viewport: null,
    launchOptions: {
      args: ['--start-maximized'],
    },
  },
  projects: [
    {
      name: 'chromium',
      // Not spreading devices['Desktop Chrome'] here: it sets a fixed
      // viewport and deviceScaleFactor, and deviceScaleFactor is
      // rejected outright when viewport is null. Only 'chromium' is
      // needed since this suite always runs headed/maximized.
      use: { browserName: 'chromium' },
    },
  ],
});
