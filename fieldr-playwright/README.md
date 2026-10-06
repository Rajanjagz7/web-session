# Fieldr Playwright Automation Suite

End-to-end automated testing suite for **Fieldr Web App** (`https://c1.dev.fieldr.app/`), built using [Playwright](https://playwright.dev/) with TypeScript and the Page Object Model (POM) pattern.

---

## 📁 Project Structure

```text
fieldr-playwright/
├── src/
│   └── pages/
│       ├── LoginPage.ts         # Page Object for Fieldr login & OTP verification
│       └── JobPage.ts           # Page Object for Job/Project creation wizard (5 steps)
├── tests/
│   ├── login.spec.ts            # Authentication tests
│   └── create-job.spec.ts       # Job/Project creation end-to-end flow
├── playwright.config.ts         # Playwright test runner configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Project dependencies & npm scripts
├── .env                         # Environment variables (Base URL, email, OTP)
└── README.md                    # Documentation
```

---

## 🚀 Getting Started

### 1. Installation
In your terminal, navigate to this directory and install dependencies:
```bash
npm install
npx playwright install chromium
```

> **Note for Windows PowerShell**: If PowerShell script execution policies prevent running `npm`, run via `cmd.exe /c "npm install"` or `npm.cmd install`.

---

## 🧪 Running Tests

### Run All Tests (Headless)
```bash
npm test
```

### Run Tests in Headed Mode (Watch the browser in real-time)
```bash
npm run test:headed
```

### Run Tests in Interactive UI Mode
```bash
npm run test:ui
```

### Run a Specific Test
```bash
npx playwright test tests/create-job.spec.ts --headed
```

### View HTML Test Report
```bash
npm run report
```

---

## 🔐 Credentials & OTP Configuration

Edit `.env` to configure your test credentials:
```env
BASE_URL=https://c1.dev.fieldr.app
TEST_EMAIL=anayra@yopmail.com
TEST_OTP=<your bypass OTP>
```

You can also pass `TEST_OTP` dynamically when triggering tests from CLI:
```bash
TEST_OTP=123456 npx playwright test
```
