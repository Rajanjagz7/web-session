const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests',
  timeout: 60000,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'https://dev.pmx.softwareco.com',
    headless: false,
    channel: 'chrome',
    storageState: 'test-data/auth.json',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
});
