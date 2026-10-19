# Gus Money Admin Panel - QA Automation & Test Plan

## 1. Executive Summary
This document defines the comprehensive end-to-end QA test plan and Playwright TypeScript automation framework for the **Gus Money** / Sunrise Rewards Admin Panel.

## 2. Target Environments
| Environment | Base URL | Auth Mechanism | Notes |
| :--- | :--- | :--- | :--- |
| **Development** | `https://newsunrisedev.softwareco.com` | Email + Password | Active Dev instance |
| **Staging** | `https://stage.newsunrise.com.au` | Email + Password | Pre-production |
| **Production** | `https://app.newsunrise.com.au` | Email + Password | Live Admin |

## 3. Test Modules & Coverage Scope
- **AUTH**: Authentication & Authorization (Admin Login, Session Expiry, Password Security, 401s)
- **DASH**: Admin Dashboard & Analytics (KPI counters, active customers, transaction volumes)
- **CUST**: Customers & Users (Participant profiles, phone/email verification, loyalty balance)
- **GM-REW**: Gus Money & Global Rewards (Earn/burn rules, tier definitions, points ledger)
- **DEAL**: Deals & Promotions (Promo codes, store assignments, start/end date constraints)
- **STORE**: Store Network & Facilities (Store list, facility mapping, regional clustering)
- **TXN**: Financial Audit & Transactions (MYOB sync, CSV/XLSX export, reconciliation)

## 4. Test Case Matrix (Sample)
| ID | Title | Module | Preconditions | Steps | Test Data | Expected Result | Priority | Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| GM-AUTH-001 | Valid Admin Login | AUTH | Admin account exists | 1. Enter email<br>2. Enter password<br>3. Click Sign in | `admin@yopmail.com` / `Admin@123` | Redirects to Dashboard, session stored | P0 | Functional |
| GM-AUTH-002 | Invalid Password Rejection | AUTH | Valid user email | 1. Enter valid email<br>2. Enter wrong pass<br>3. Click Sign in | `WrongPass@123` | 401 Unauthorized alert displayed | P0 | Negative |
| GM-AUTH-003 | Non-existent User Rejection | AUTH | Database online | 1. Enter unregistered email<br>2. Submit | `fakeuser99@yopmail.com` | "User does not exist" message | P1 | Negative |
| GM-REW-001 | Global Rewards Page Guard | GM-REW | Unauthenticated session | 1. Navigate directly to `/reward/global-rewards` | N/A | Immediate redirect to `/sign-in` | P0 | Security |
| GM-REW-002 | Export Rewards Report | GM-REW | Authenticated as Admin | 1. Go to Global Rewards<br>2. Click Export | Active filters | Excel (`.xlsx`) download initiated | P1 | Functional |

## 5. Execution Commands
```bash
# Run all tests headlessly
npx playwright test

# Run authentication test suite
npx playwright test tests/auth.spec.ts

# Open HTML test report
npx playwright show-report
```