import { defineConfig } from '@playwright/test';
import 'dotenv/config';
import path from 'path';

// Separate env file so these NSW/rebateM8 creds don't collide with the
// existing 1er.softwareco .env used by the other suite.
require('dotenv').config({ path: path.resolve(__dirname, '.env.nsw-jobs'), override: true });

export default defineConfig({
  testDir: './tests-nsw-jobs',
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['html', { open: 'never', outputFolder: 'nsw-jobs-report' }], ['list']],
  use: {
    baseURL: process.env.NSW_BASE_URL || 'https://nswdev.rebatem8.com.au',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    viewport: null,
    launchOptions: {
      args: ['--start-maximized'],
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
});
