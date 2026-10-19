import { defineConfig, devices } from '@playwright/test';
import 'dotenv/config';
import { STORAGE_STATE_PATH } from './global-setup';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [['html', { open: 'never' }], ['list']],
  globalSetup: './global-setup.ts',
  use: {
    baseURL: process.env.BASE_URL || 'https://bcppqf-4m.myshopify.com',
    storageState: STORAGE_STATE_PATH,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'Mobile Chrome (Pixel 9, dark)',
      use: {
        ...devices['Pixel 9'],
        colorScheme: 'dark',
      },
    },
  ],
});
