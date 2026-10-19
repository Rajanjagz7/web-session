import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';
import { env, PERSONAS } from './src/config/env';

const authFile = (persona: string): string => path.resolve(__dirname, '.auth', `${persona}.json`);

/**
 * Projects: one "setup" project that logs every persona in once, then one project per persona that reuses that
 * storageState and runs only the tests tagged with that persona (@cost-viewer, @no-cost-viewer, @no-permission,
 * @portal-customer, @super-admin). Area tags (@quotes, @portal, @security ...) are in the describe and test titles:
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
      name: persona,
      testMatch: /.*\.spec\.ts$/,
      grep: new RegExp(`@${persona}(?=\\s|$)`),
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        baseURL: persona === 'portal-customer' ? env.portalUrl : env.baseUrl,
        storageState: authFile(persona),
      },
    })),
  ],
});
