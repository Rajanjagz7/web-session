import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";

dotenv.config();

const STORAGE_STATE = ".auth/admin.json";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["list"],
    ["html", { open: "never" }],
    ["junit", { outputFile: "reports/junit-ui.xml" }],
    ...(process.env.ALLURE ? [["allure-playwright"] as [string]] : [])
  ],
  use: {
    baseURL: process.env.ADMIN_BASE_URL || "https://gusdev.softwareco.com",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure"
  },
  projects: [
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], storageState: STORAGE_STATE },
      dependencies: ["setup"],
      testMatch: /(users.*|loan-products|lender-phone|lenders-verify)\.spec\.ts/
    },
    {
      // Legacy specs (newsunrisedev) keep running without the shared login
      name: "legacy",
      use: { ...devices["Desktop Chrome"] },
      testIgnore: [/(users.*|loan-products|lender-phone|lenders-verify)\.spec\.ts/, /auth\.setup\.ts/]
    }
  ]
});
