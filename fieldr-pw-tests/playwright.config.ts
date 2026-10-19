import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';
import { env, PERSONAS } from './src/lib/env';

const authFile = (persona: string): string => path.resolve(__dirname, '.auth', `${persona}.json`);

/**
 * One setup project logs every persona in once (src/fixtures/auth.setup.ts, per-persona storageState). Then one project per
 * persona (cost-viewer-chromium, no-cost-viewer-chromium, no-permission-chromium, portal-customer-chromium,
 * super-admin-chromium) reuses that state and runs only the tests tagged with its persona (@cost-viewer, ...).
 * Area tags are in the describe and test titles: @quotes @jobs @portal @schedule @roles @customers @pickers @billing
 * @admin @security @invites @pdf @misc @insights @regression @manual
 *   npx playwright test --grep @security
 */
export default defineConfig({
  testDir: './src',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false, // personas share OTP-bypass accounts; keep their runs serial
  workers: 1,
  forbidOnly: !!process.env['CI'],
  retries: 1, // the retry records the trace
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: env.baseUrl,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts$/ },
    ...PERSONAS.map((persona) => ({
      name: `${persona}-chromium`,
      testMatch: /.*\.spec\.ts$/, // spec files live only in src/specs
      grep: new RegExp(`@${persona}(?=\\s|$)`), // double backslash: a single \s inside a template literal becomes a plain "s"
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        baseURL: persona === 'portal-customer' ? env.portalUrl : env.baseUrl,
        storageState: authFile(persona),
      },
    })),
  ],
});
