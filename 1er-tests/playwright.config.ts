import { defineConfig } from '@playwright/test';
import 'dotenv/config';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  fullyParallel: false,
  // Two headed browsers running at once caused real timeouts (network
  // contention slowed the address autocomplete past the test timeout).
  workers: 1,
  retries: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: process.env.BASE_URL || 'https://1er.softwareco.com',
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
      // Not using devices['Desktop Chrome']: it sets a fixed viewport +
      // deviceScaleFactor, and deviceScaleFactor is rejected outright when
      // viewport is null. Only 'chromium' is needed - this suite always
      // runs headed/maximized.
      use: { browserName: 'chromium' },
    },
  ],
});
