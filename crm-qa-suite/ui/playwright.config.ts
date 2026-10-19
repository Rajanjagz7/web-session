import { defineConfig, devices } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Same env contract as the API suite: real env vars first, then ../.env and ../.env.<CRM_ENV>.
function loadEnv(file: string) {
  if (!fs.existsSync(file)) return;
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const i = line.indexOf('=');
    const key = line.slice(0, i).trim();
    const val = line.slice(i + 1).trim().replace(/^["']|["']$/g, '');
    if (!(key in process.env)) process.env[key] = val;
  }
}
const root = path.resolve(__dirname, '..');
loadEnv(path.join(root, '.env'));
if (process.env.CRM_ENV) loadEnv(path.join(root, `.env.${process.env.CRM_ENV}`));

export const AUTH_FILE = path.join(__dirname, '.auth', 'user.json');
const baseURL = process.env.CRM_BASE_URL ?? 'https://crm.staging.notbhavik.dev';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../reports/ui-html', open: 'never' }],
    ['junit', { outputFile: '../reports/ui-junit.xml' }],
    ...(process.env.ALLURE ? [['allure-playwright', { resultsDir: '../allure-results' }] as [string, object]] : []),
  ],
  use: {
    baseURL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    headless: process.env.HEADED ? false : true,
  },
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: AUTH_FILE }, dependencies: ['setup'] },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], storageState: AUTH_FILE }, dependencies: ['setup'] },
    { name: 'webkit', use: { ...devices['Desktop Safari'], storageState: AUTH_FILE }, dependencies: ['setup'] },
    { name: 'mobile', use: { ...devices['Pixel 7'], storageState: AUTH_FILE }, dependencies: ['setup'], testMatch: /responsive\.spec\.ts/ },
  ],
});
