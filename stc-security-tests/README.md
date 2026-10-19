# STC - Security (Sprint 1) Automation Test Suite

Automated Playwright test suite for **STC - Security** Sprint 1 (Authentication and User Management) and Gus Money companion sanity.

## Setup & Prerequisites

```bash
cd C:\Users\Baps\.gemini\antigravity-ide\scratch\stc-security-tests
npm install
```

## Running the Tests

### 1. Run All Tests on DEV Environment
```bash
npx playwright test
```

### 2. Run with UI / Interactive Browser (Headed Mode)
```bash
npx playwright test --headed
```

### 3. Run Specifically Against STAGE
```bash
npm run test:stage
```

### 4. Run Modular Suites
```bash
# Authentication tests only
npm run test:auth

# User Management tests only
npm run test:users
```

### 5. View Test Report
```bash
npx playwright show-report
```
