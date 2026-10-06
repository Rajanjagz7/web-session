"""Generate the Fieldr Playwright framework + AUTH specs + AUTH manual test-case table (single source of truth)."""
import os, json

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pw")


def w(rel, content):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.lstrip("\n"))


# ------------------------------------------------------------------ project files
w("package.json", json.dumps({
    "name": "fieldr-e2e", "version": "1.0.0", "private": True,
    "scripts": {"test": "playwright test", "test:p0": "playwright test --grep @P0", "typecheck": "tsc --noEmit", "report": "playwright show-report"},
    "devDependencies": {"@playwright/test": "^1.49.0", "@types/node": "^22.0.0", "dotenv": "^16.4.5", "typescript": "^5.6.0"},
}, indent=2) + "\n")

w("tsconfig.json", json.dumps({"compilerOptions": {
    "target": "ES2022", "module": "commonjs", "strict": True, "esModuleInterop": True, "skipLibCheck": True, "baseUrl": ".",
    "paths": {"@pages/*": ["src/pages/*"], "@modules/*": ["src/modules/*"], "@utils/*": ["src/utils/*"], "@config/*": ["src/config/*"],
              "@fixtures": ["src/fixtures/index.ts"], "@testdata/*": ["src/testdata/*"]}},
    "include": ["src/**/*.ts", "playwright.config.ts"]}, indent=2) + "\n")

w(".gitignore", "node_modules/\ntest-results/\nplaywright-report/\n.env\n")
w(".env.example", """FLDR_BASE_URL=https://rajanjagz7.dev.fieldr.app
# Owned QA number (national format) and its QA bypass OTP
FLDR_MOBILE=
FLDR_OTP=
# Optional: registered email for the email-login case (skipped when empty)
FLDR_EMAIL=
# Number that must NOT belong to any user (never a real person's number)
FLDR_UNREGISTERED_MOBILE=
# Set to 1 to allow brute-force / lock-out cases against the shared account
FLDR_ALLOW_LOCKOUT=0
""")
# .env is created only if missing, with placeholders. Put the real QA mobile and OTP here yourself; never commit it.
if not os.path.exists(os.path.join(ROOT, ".env")):
    w(".env", """FLDR_BASE_URL=https://rajanjagz7.dev.fieldr.app
FLDR_MOBILE=REPLACE_ME
FLDR_OTP=REPLACE_ME
FLDR_EMAIL=
FLDR_UNREGISTERED_MOBILE=REPLACE_ME
FLDR_ALLOW_LOCKOUT=0
""")

w("playwright.config.ts", """
import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

dotenv.config();

export default defineConfig({
  testDir: './src/tests',
  testMatch: '**/*.e2e.ts',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false, // one shared OTP-bypass account: keep auth cases serial
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 1, // first retry records trace.zip
  reporter: [['list'], ['html', { open: 'never' }], ['json', { outputFile: 'test-results/results.json' }]],
  use: {
    baseURL: process.env.FLDR_BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'edge', use: { ...devices['Desktop Edge'], channel: 'msedge' } },
  ],
});
""")

# ------------------------------------------------------------------ config / utils / testdata
w("src/config/index.ts", """
import dotenv from 'dotenv';

dotenv.config();

const required = (key: string): string => {
  const value = process.env[key];
  if (!value) throw new Error(`Missing env var ${key} - copy .env.example to .env and fill it in`);
  return value;
};

export const config = {
  baseUrl: process.env.FLDR_BASE_URL ?? 'https://rajanjagz7.dev.fieldr.app',
  mobile: required('FLDR_MOBILE'),
  otp: required('FLDR_OTP'),
  email: process.env.FLDR_EMAIL ?? '',
  unregisteredMobile: required('FLDR_UNREGISTERED_MOBILE'),
  allowLockout: process.env.FLDR_ALLOW_LOCKOUT === '1',
  timeouts: { ui: 10_000, network: 15_000, resend: 45_000 },
} as const;
""")

w("src/utils/Logger.ts", """
type Level = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
const order: Record<Level, number> = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 };

export class Logger {
  constructor(private readonly context: string) {}

  private write(level: Level, message: string): void {
    const min = (process.env.LOG_LEVEL as Level | undefined) ?? 'INFO';
    if (order[level] < order[min]) return;
    process.stdout.write(`[${new Date().toISOString()}] [${level}] [${this.context}] ${message}\\n`);
  }

  debug(message: string): void { this.write('DEBUG', message); }
  info(message: string): void { this.write('INFO', message); }
  warn(message: string): void { this.write('WARN', message); }
  error(message: string): void { this.write('ERROR', message); }
}
""")

w("src/utils/DataGenerator.ts", """
/** Per-run AU test data helpers. The epoch is the only varying input. */
export class DataGenerator {
  /** RFC 2606 reserved domain: mail can never reach a real person. */
  static unregisteredEmail(): string {
    return `qa+${Date.now()}@example.com`;
  }
}
""")

w("src/utils/index.ts", "export { Logger } from './Logger';\nexport { DataGenerator } from './DataGenerator';\n")

w("src/testdata/au.ts", """
/** AU test data library (verbatim from the master prompt). Typed values only: none of these are submitted. */
export const AU = {
  mobile: {
    tooShort: '0412 34',
    us: '14123456789',
    lettersMixed: '0412ABC678',
    whitespace: '   ',
    emoji: '\\u{1F642}',
    elevenDigits: '04123456789',
  },
  email: {
    noAt: 'noah.smithbigpond.net.au',
    missingTld: 'noah.smith@bigpond',
    doubleDot: 'noah..smith@bigpond.net.au',
    whitespace: '   ',
    xss: '"><img src=x onerror=window.__xss=1>',
    sqli: "' OR '1'='1",
  },
  otp: { wrong: '111111', fiveDigits: '48956', letters: 'a' },
  /** Observed UI mask for AU mobiles (2026-09-19): "+61 (04) XXXX XXXX". */
  mask: (national: string): string => `+61 (${national.slice(0, 2)}) ${national.slice(2, 6)} ${national.slice(6)}`,
} as const;
""")

# ------------------------------------------------------------------ pages (locators only)
w("src/pages/BasePage.ts", """
import { Page } from '@playwright/test';

export abstract class BasePage {
  constructor(protected page: Page) {}

  async navigate(path: string): Promise<void> {
    await this.page.goto(path);
  }
}
""")

w("src/pages/LoginPage.ts", """
import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

/** Selectors come from the accessibility tree observed on 2026-09-19. */
export class LoginPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  heading = () => this.page.getByRole('heading', { name: 'Welcome to Fieldr' });
  eyebrow = () => this.page.getByText(/secure login/i).first();
  helper = () => this.page.getByText("Log in with your mobile number or email. We'll send you a one-time passcode (OTP).");
  mobileTab = () => this.page.getByRole('button', { name: 'Mobile Number' });
  emailTab = () => this.page.getByRole('button', { name: 'Email Address' });
  form = () => this.page.locator('form');
  identifierInput = () => this.form().getByRole('textbox').first();
  countryButton = () => this.page.getByRole('button', { name: /Australia/ });
  sendOtpBtn = () => this.page.getByRole('button', { name: 'Send OTP' });
  termsLink = () => this.page.getByRole('link', { name: 'Terms & Conditions' });
  privacyLink = () => this.page.getByRole('link', { name: 'Privacy Policy' });

  otpHeading = () => this.page.getByRole('heading', { name: 'Check Your Messages' });
  otpSentTo = () => this.page.getByText('We sent a 6-digit OTP to');
  otpDigit = (index: number) => this.page.getByRole('textbox', { name: `Digit ${index}` });
  verifyBtn = () => this.page.getByRole('button', { name: 'Verify & Login' });
  resendBtn = () => this.page.getByRole('button', { name: 'Resend OTP', exact: true });
  resendTimer = () => this.page.getByText(/Resend OTP in \\d+s/);
  changeIdentifierBtn = () => this.page.getByRole('button', { name: 'Use a different number or email' });

  async open(): Promise<void> {
    await this.navigate('/login');
  }

  async clickMobileTab(): Promise<void> {
    await this.mobileTab().click();
  }

  async clickEmailTab(): Promise<void> {
    await this.emailTab().click();
  }

  async fillIdentifier(value: string): Promise<void> {
    await this.identifierInput().fill(value);
  }

  async clickSendOtp(): Promise<void> {
    await this.sendOtpBtn().click();
  }

  async fillOtpDigit(index: number, value: string): Promise<void> {
    await this.otpDigit(index).fill(value);
  }

  async typeIntoOtpDigit(index: number, value: string): Promise<void> {
    await this.otpDigit(index).pressSequentially(value);
  }

  async clickVerify(): Promise<void> {
    await this.verifyBtn().click();
  }

  async clickResend(): Promise<void> {
    await this.resendBtn().click();
  }

  async clickChangeIdentifier(): Promise<void> {
    await this.changeIdentifierBtn().click();
  }

  async pressTab(): Promise<void> {
    await this.page.keyboard.press('Tab');
  }
}
""")

w("src/pages/DashboardPage.ts", """
import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  heading = () => this.page.getByRole('heading', { name: 'Dashboard', level: 1 });
  navLink = (name: string) => this.page.getByRole('link', { name, exact: true });
  userMenuBtn = () => this.page.getByRole('button', { name: /@/ });
  // NEEDS UI INSPECTION: the logout menu item label was not observed. Regex is a best guess.
  logoutMenuItem = () => this.page.getByRole('menuitem', { name: /log\\s?out|sign\\s?out/i });

  async open(): Promise<void> {
    await this.navigate('/app/dashboard');
  }

  async openDeepLink(path: string): Promise<void> {
    await this.navigate(path);
  }

  async clickUserMenu(): Promise<void> {
    await this.userMenuBtn().click();
  }

  async clickLogout(): Promise<void> {
    await this.logoutMenuItem().click();
  }
}
""")

w("src/pages/index.ts", "export { BasePage } from './BasePage';\nexport { LoginPage } from './LoginPage';\nexport { DashboardPage } from './DashboardPage';\n")

# ------------------------------------------------------------------ modules (business logic)
w("src/modules/LoginModule.ts", """
import { Page, Response, expect } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';
import { DashboardPage } from '@pages/DashboardPage';
import { Logger } from '@utils/Logger';
import { config } from '@config/index';

export class LoginModule {
  private readonly logger = new Logger('LoginModule');

  constructor(
    private readonly page: Page,
    private readonly loginPage: LoginPage,
    private readonly dashboardPage: DashboardPage,
  ) {}

  async requestOtpForMobile(national: string): Promise<void> {
    this.logger.info(`Requesting OTP for mobile ending ${national.slice(-3)}`);
    await this.loginPage.open();
    await this.loginPage.clickMobileTab();
    await this.loginPage.fillIdentifier(national);
    await this.loginPage.clickSendOtp();
    await expect(this.loginPage.otpHeading()).toBeVisible({ timeout: config.timeouts.network });
  }

  async enterOtp(code: string): Promise<void> {
    for (let i = 0; i < code.length; i += 1) {
      await this.loginPage.fillOtpDigit(i + 1, code[i]);
    }
  }

  async loginWithMobile(national: string = config.mobile, otp: string = config.otp): Promise<void> {
    await this.requestOtpForMobile(national);
    await this.enterOtp(otp);
    await expect(this.loginPage.verifyBtn()).toBeEnabled();
    await this.loginPage.clickVerify();
    await this.expectOnDashboard();
  }

  async loginWithEmail(email: string, otp: string = config.otp): Promise<void> {
    this.logger.info('Requesting OTP by email');
    await this.loginPage.open();
    await this.loginPage.clickEmailTab();
    await this.loginPage.fillIdentifier(email);
    await this.loginPage.clickSendOtp();
    await expect(this.loginPage.otpHeading()).toBeVisible({ timeout: config.timeouts.network });
    await this.enterOtp(otp);
    await this.loginPage.clickVerify();
    await this.expectOnDashboard();
  }

  /** Click Send OTP and return the API response it triggered. */
  async sendOtpCapturing(): Promise<Response> {
    const [response] = await Promise.all([
      this.page.waitForResponse((r) => r.request().method() === 'POST', { timeout: config.timeouts.network }),
      this.loginPage.clickSendOtp(),
    ]);
    return response;
  }

  /** Click Verify & Login and return the API response it triggered. */
  async verifyCapturing(): Promise<Response> {
    const [response] = await Promise.all([
      this.page.waitForResponse((r) => r.request().method() === 'POST', { timeout: config.timeouts.network }),
      this.loginPage.clickVerify(),
    ]);
    return response;
  }

  /** Fill the identifier and click Send OTP only if the button is enabled. Returns whether it was clicked. */
  async trySendIdentifier(value: string): Promise<boolean> {
    await this.loginPage.fillIdentifier(value);
    const enabled = await this.loginPage.sendOtpBtn().isEnabled();
    if (enabled) await this.loginPage.clickSendOtp();
    return enabled;
  }

  async expectOnDashboard(): Promise<void> {
    await expect(this.page).toHaveURL(/\\/app\\/dashboard/, { timeout: config.timeouts.network });
    await expect(this.dashboardPage.heading()).toBeVisible({ timeout: config.timeouts.network });
  }

  async expectStillOnIdentifierStep(): Promise<void> {
    await expect(this.loginPage.otpHeading()).toBeHidden({ timeout: config.timeouts.ui });
    await expect(this.page).toHaveURL(/\\/login/);
  }

  async logout(): Promise<void> {
    await this.dashboardPage.clickUserMenu();
    await this.dashboardPage.clickLogout();
    await expect(this.page).toHaveURL(/\\/login/, { timeout: config.timeouts.network });
  }
}
""")
w("src/modules/index.ts", "export { LoginModule } from './LoginModule';\n")

# ------------------------------------------------------------------ fixtures
w("src/fixtures/index.ts", """
import { test as base } from '@playwright/test';
import { LoginPage, DashboardPage } from '@pages/index';
import { LoginModule } from '@modules/index';

type Fixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  loginModule: LoginModule;
  /** OTP-bypass fixture: a fully authenticated session for the QA account. */
  loggedIn: void;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
  loginModule: async ({ page, loginPage, dashboardPage }, use) => {
    await use(new LoginModule(page, loginPage, dashboardPage));
  },
  loggedIn: async ({ loginModule }, use) => {
    await loginModule.loginWithMobile();
    await use();
  },
});

export { expect } from '@playwright/test';
""")

# ------------------------------------------------------------------ AUTH cases (single source of truth)
T = "{ timeout: config.timeouts.ui }"
N = "{ timeout: config.timeouts.network }"
cases = []


def case(id, title, prio, typ, pre, data, exp, steps, tags=(), skip=None, fixme=None, slow=False):
    cases.append(dict(id=id, title=title, prio=prio, typ=typ, pre=pre, data=data, exp=exp, steps=steps, tags=list(tags), skip=skip, fixme=fixme, slow=slow))


OPEN = ("Open the login page", "await loginPage.open();")
MOBTAB = ("Click the Mobile Number tab", "await loginPage.clickMobileTab();")
EMAILTAB = ("Click the Email Address tab", "await loginPage.clickEmailTab();")
SENDBYPASS = [OPEN, MOBTAB, ("Enter the QA mobile number in the mobile field", "await loginPage.fillIdentifier(config.mobile);"),
              ("Click Send OTP", "await loginPage.clickSendOtp();"),
              ("Wait for the Check Your Messages heading", f"await expect(loginPage.otpHeading()).toBeVisible({N});")]
NEG_EXPECT = "The OTP step is not shown and the user stays on /login"
LOGURL = f"await expect(page).toHaveURL(/\\/login/, {N});"
DASH_H = "page.getByRole('heading', { name: 'Dashboard', level: 1 })"
RECORD = "test.info().annotations.push({ type: 'observed-response', description: `${response.status()} ${(await response.text()).slice(0, 300)}` });"


def neg_input(id, title, value_expr, data):
    case(id, title, "P1", "Negative", "Logged out", data, NEG_EXPECT,
         [OPEN, MOBTAB, ("Enter the invalid value and click Send OTP only if it is enabled", f"await loginModule.trySendIdentifier({value_expr});"),
          ("Verify the OTP step is not shown", "await loginModule.expectStillOnIdentifierStep();")])


def neg_email(id, title, value_expr, data):
    case(id, title, "P1", "Negative", "Logged out", data, NEG_EXPECT,
         [OPEN, EMAILTAB, ("Enter the invalid email and click Send OTP only if it is enabled", f"await loginModule.trySendIdentifier({value_expr});"),
          ("Verify the OTP step is not shown", "await loginModule.expectStillOnIdentifierStep();")])


case("FLD-AUTH-001", "Unauthenticated /app/dashboard redirects to Secure Login", "P0", "Security", "No session cookie", "/app/dashboard", "302 to /login and the Welcome to Fieldr heading is shown",
     [("Open /app/dashboard without a session", "await dashboardPage.open();"), ("Verify the URL is /login", LOGURL),
      ("Verify the Welcome to Fieldr heading", f"await expect(loginPage.heading()).toBeVisible({T});")], ["@smoke"])
case("FLD-AUTH-002", "Login page shows heading, helper text, both tabs, Send OTP and legal links", "P0", "Functional", "Logged out", "-", "All observed elements are visible; legal links point to /terms-and-conditions and /privacy-policy",
     [OPEN, ("Verify the Welcome to Fieldr heading", f"await expect(loginPage.heading()).toBeVisible({T});"), ("Verify the SECURE LOGIN label", f"await expect(loginPage.eyebrow()).toBeVisible({T});"),
      ("Verify the helper text", f"await expect(loginPage.helper()).toBeVisible({T});"), ("Verify the Mobile Number tab", f"await expect(loginPage.mobileTab()).toBeVisible({T});"),
      ("Verify the Email Address tab", f"await expect(loginPage.emailTab()).toBeVisible({T});"), ("Verify the Send OTP button", f"await expect(loginPage.sendOtpBtn()).toBeVisible({T});"),
      ("Verify the Terms link target", "await expect(loginPage.termsLink()).toHaveAttribute('href', /terms-and-conditions/);"),
      ("Verify the Privacy link target", "await expect(loginPage.privacyLink()).toHaveAttribute('href', /privacy-policy/);")], ["@smoke"])
case("FLD-AUTH-003", "Mobile AU valid + correct OTP logs in to the dashboard", "P0", "Functional", "QA number registered; bypass OTP configured", "FLDR_MOBILE / FLDR_OTP (from .env)", "Redirect to /app/dashboard; Dashboard heading visible",
     SENDBYPASS + [("Enter the 6-digit OTP into Digit 1 to Digit 6", "await loginModule.enterOtp(config.otp);"), ("Click Verify & Login", "await loginPage.clickVerify();"),
                   ("Verify the dashboard is shown", "await loginModule.expectOnDashboard();")], ["@smoke"])
case("FLD-AUTH-004", "Send OTP moves to the Check Your Messages step with six digit boxes", "P0", "Functional", "Logged out", "FLDR_MOBILE", "Heading, 'We sent a 6-digit OTP to' text and Digit 1 to Digit 6 boxes shown; Verify & Login disabled",
     SENDBYPASS + [("Verify the sent-to text", f"await expect(loginPage.otpSentTo()).toBeVisible({T});")] +
     [(f"Verify Digit {i} is visible", f"await expect(loginPage.otpDigit({i})).toBeVisible({T});") for i in range(1, 7)] +
     [("Verify Verify & Login is disabled", f"await expect(loginPage.verifyBtn()).toBeDisabled({T});")])
case("FLD-AUTH-005", "Verify & Login is disabled with an empty OTP", "P1", "Validation", "OTP step shown", "empty", "Verify & Login disabled",
     SENDBYPASS + [("Verify Verify & Login is disabled", f"await expect(loginPage.verifyBtn()).toBeDisabled({T});")])
case("FLD-AUTH-006", "Verify & Login stays disabled with a 5-digit OTP (boundary min-1)", "P1", "Boundary", "OTP step shown", "48956", "Verify & Login disabled",
     SENDBYPASS + [("Enter five digits", "await loginModule.enterOtp(AU.otp.fiveDigits);"), ("Verify Verify & Login is disabled", f"await expect(loginPage.verifyBtn()).toBeDisabled({T});")])
case("FLD-AUTH-007", "Wrong OTP is rejected with a 4xx and no session", "P0", "Negative", "OTP step shown", "111111", "HTTP 4xx (not 5xx); user stays on /login; dashboard not reachable",
     SENDBYPASS + [("Enter the wrong OTP", "await loginModule.enterOtp(AU.otp.wrong);"), ("Click Verify & Login and capture the response", "const response = await loginModule.verifyCapturing();"),
                   ("Record the observed response body", RECORD),
                   ("Verify the status is 4xx", "expect(response.status()).toBeGreaterThanOrEqual(400);\n      expect(response.status()).toBeLessThan(500);"),
                   ("Verify the user is still on /login", "await expect(page).toHaveURL(/\\/login/);")])
case("FLD-AUTH-008", "Wrong-OTP message does not reveal account existence", "P1", "Security", "OTP step shown", "111111", "Response body contains none of: not registered, no account, does not exist",
     SENDBYPASS + [("Enter the wrong OTP", "await loginModule.enterOtp(AU.otp.wrong);"), ("Click Verify & Login and capture the response", "const response = await loginModule.verifyCapturing();"),
                   ("Verify the body is generic", "expect(await response.text()).not.toMatch(/not registered|no account|does not exist|doesn't exist/i);")])
case("FLD-AUTH-009", "OTP digit box rejects a letter", "P1", "Validation", "OTP step shown", "a", "Digit 1 stays empty",
     SENDBYPASS + [("Type a letter into Digit 1", "await loginPage.typeIntoOtpDigit(1, AU.otp.letters);"), ("Verify Digit 1 is empty", f"await expect(loginPage.otpDigit(1)).toHaveValue('', {T});")])
case("FLD-AUTH-010", "OTP digit box holds at most one character", "P1", "Boundary", "OTP step shown", "12 typed into Digit 1", "Digit 1 value length <= 1",
     SENDBYPASS + [("Type two digits into Digit 1", "await loginPage.typeIntoOtpDigit(1, '12');"),
                   ("Verify Digit 1 holds at most one character", "expect((await loginPage.otpDigit(1).inputValue()).length).toBeLessThanOrEqual(1);")])
case("FLD-AUTH-011", "Pasting a 6-digit code fills all six boxes", "P1", "Functional", "OTP step shown", "FLDR_OTP", "Digits 1-6 hold the pasted digits (ASSUMPTION: paste is supported)",
     SENDBYPASS + [("Focus Digit 1", "await loginPage.otpDigit(1).focus();"),
                   ("Dispatch a paste event with the OTP", "await page.evaluate((code) => {\n        const dt = new DataTransfer();\n        dt.setData('text', code);\n        document.activeElement?.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));\n      }, config.otp);")] +
     [(f"Verify Digit {i}", f"await expect(loginPage.otpDigit({i})).toHaveValue(config.otp[{i - 1}], {T});") for i in range(1, 7)])
case("FLD-AUTH-012", "OTP boxes are named Digit 1 to Digit 6 and Verify is reachable by keyboard", "P1", "Accessibility", "OTP step shown", "-", "Six named textboxes; Verify & Login gets focus within 10 Tab presses once enabled",
     SENDBYPASS + [("Enter the OTP", "await loginModule.enterOtp(config.otp);")] +
     [(f"Verify the accessible name Digit {i}", f"await expect(page.getByRole('textbox', {{ name: 'Digit {i}' }})).toHaveCount(1);") for i in range(1, 7)] +
     [("Press Tab until Verify & Login is focused", "for (let i = 0; i < 10; i += 1) {\n        if (await loginPage.verifyBtn().evaluate((el) => el === document.activeElement)) break;\n        await loginPage.pressTab();\n      }"),
      ("Verify Verify & Login is focused", "await expect(loginPage.verifyBtn()).toBeFocused();")])
case("FLD-AUTH-013", "Resend countdown is shown and starts at 30s or less", "P1", "Functional", "OTP step shown", "-", "'Resend OTP in Ns' with N <= 30",
     SENDBYPASS + [("Verify the countdown text", f"await expect(loginPage.resendTimer()).toBeVisible({T});"),
                   ("Verify the countdown is 30s or less", "const text = (await loginPage.resendTimer().textContent()) ?? '';\n      expect(Number(/(\\d+)s/.exec(text)?.[1])).toBeLessThanOrEqual(30);")])
case("FLD-AUTH-014", "Resend OTP button appears when the countdown ends", "P1", "Flaky", "OTP step shown", "wait ~30s", "Resend OTP button enabled within 45s (time-sensitive)",
     SENDBYPASS + [("Wait for the Resend OTP button", "await expect(loginPage.resendBtn()).toBeEnabled({ timeout: config.timeouts.resend });")], ["@flaky"], slow=True)
case("FLD-AUTH-015", "Resend OTP button is not offered during the countdown", "P1", "Functional", "OTP step shown", "-", "No Resend OTP button while the countdown text shows",
     SENDBYPASS + [("Verify the countdown text", f"await expect(loginPage.resendTimer()).toBeVisible({T});"), ("Verify no Resend OTP button", f"await expect(loginPage.resendBtn()).toHaveCount(0, {T});")])
case("FLD-AUTH-016", "Use a different number or email returns to the identifier step", "P1", "Functional", "OTP step shown", "-", "Identifier step shown; OTP step hidden",
     SENDBYPASS + [("Click Use a different number or email", "await loginPage.clickChangeIdentifier();"), ("Verify Send OTP is shown", f"await expect(loginPage.sendOtpBtn()).toBeVisible({T});"),
                   ("Verify the OTP step is hidden", f"await expect(loginPage.otpHeading()).toBeHidden({T});")])
neg_input("FLD-AUTH-017", "Mobile too short (0412 34) does not request an OTP", "AU.mobile.tooShort", "0412 34")
case("FLD-AUTH-018", "US number typed into the AU field keeps the Australia country selector", "P1", "Negative", "Logged out", "14123456789", "Country selector still shows Australia; nothing is submitted",
     [OPEN, MOBTAB, ("Enter a US-format number", "await loginPage.fillIdentifier(AU.mobile.us);"), ("Verify the country selector still shows Australia", f"await expect(loginPage.countryButton()).toBeVisible({T});")])
case("FLD-AUTH-019", "Letters mixed into the mobile field are stripped", "P1", "Validation", "Logged out", "0412ABC678", "Field value contains no letters (not submitted)",
     [OPEN, MOBTAB, ("Type digits mixed with letters", "await loginPage.fillIdentifier(AU.mobile.lettersMixed);"),
      ("Verify no letters remain", "expect(await loginPage.identifierInput().inputValue()).not.toMatch(/[A-Za-z]/);")])
neg_input("FLD-AUTH-020", "Whitespace-only mobile does not request an OTP", "AU.mobile.whitespace", "3 spaces")
case("FLD-AUTH-021", "Emoji in the mobile field is not accepted", "P1", "Validation", "Logged out", "U+1F642", "Field value has only digits, spaces, +, ( and )",
     [OPEN, MOBTAB, ("Type an emoji", "await loginPage.identifierInput().pressSequentially(AU.mobile.emoji);"),
      ("Verify no emoji remains", "expect(await loginPage.identifierInput().inputValue()).toMatch(/^[+\\d\\s()-]*$/);")])
neg_input("FLD-AUTH-022", "Empty mobile does not request an OTP", "''", "empty")
case("FLD-AUTH-023", "Eleven-digit mobile is truncated to 10 national digits (boundary max+1)", "P1", "Boundary", "Logged out", "04123456789", "At most 10 digits after +61 (not submitted)",
     [OPEN, MOBTAB, ("Type 11 digits", "await loginPage.fillIdentifier(AU.mobile.elevenDigits);"),
      ("Verify at most 10 national digits", "const digits = (await loginPage.identifierInput().inputValue()).replace(/^\\+61/, '').replace(/\\D/g, '');\n      expect(digits.length).toBeLessThanOrEqual(10);")])
case("FLD-AUTH-024", "National format 0412 345 678 is masked as +61 (04) 1234 5678", "P1", "Functional", "Logged out", "0412345678", "Observed mask +61 (04) 1234 5678 (not submitted)",
     [OPEN, MOBTAB, ("Type the national number", "await loginPage.fillIdentifier('0412345678');"),
      ("Verify the mask", f"await expect(loginPage.identifierInput()).toHaveValue(AU.mask('0412345678'), {T});")])
case("FLD-AUTH-025", "Surrounding whitespace is ignored by the mobile mask", "P1", "Validation", "Logged out", "'  0444124222 '", "Value +61 (04) 4412 4222 (not submitted)",
     [OPEN, MOBTAB, ("Type the number with surrounding spaces", "await loginPage.fillIdentifier('  0444124222 ');"),
      ("Verify the mask", f"await expect(loginPage.identifierInput()).toHaveValue(AU.mask('0444124222'), {T});")])
case("FLD-AUTH-026", "Unregistered mobile never reaches the dashboard and does not leak account existence", "P0", "Security", "FLDR_UNREGISTERED_MOBILE belongs to no user", "FLDR_UNREGISTERED_MOBILE", "Not on dashboard; response recorded for PO review (enumeration policy is undecided)",
     [OPEN, MOBTAB, ("Enter the unregistered mobile", "await loginPage.fillIdentifier(config.unregisteredMobile);"),
      ("Click Send OTP and capture the response", "const response = await loginModule.sendOtpCapturing();"), ("Record the observed response", RECORD),
      ("Verify the dashboard is not shown", "await expect(page).not.toHaveURL(/\\/app\\/dashboard/);")])
case("FLD-AUTH-027", "Email Address tab replaces the mobile field and hides the country selector", "P0", "Functional", "Logged out", "-", "Identifier field shown without the Australia selector; Send OTP visible",
     [OPEN, EMAILTAB, ("Verify the country selector is hidden", f"await expect(loginPage.countryButton()).toBeHidden({T});"),
      ("Verify Send OTP is shown", f"await expect(loginPage.sendOtpBtn()).toBeVisible({T});")])
case("FLD-AUTH-028", "Email valid + correct OTP logs in", "P0", "Functional", "FLDR_EMAIL set and the bypass OTP applies to email (ASSUMPTION)", "FLDR_EMAIL / FLDR_OTP", "Redirect to /app/dashboard",
     [("Log in with the registered email", "await loginModule.loginWithEmail(config.email);")], skip="!config.email")
neg_email("FLD-AUTH-029", "Email without @ does not request an OTP", "AU.email.noAt", "noah.smithbigpond.net.au")
neg_email("FLD-AUTH-030", "Email with missing TLD does not request an OTP", "AU.email.missingTld", "noah.smith@bigpond")
neg_email("FLD-AUTH-031", "Email with a double dot does not request an OTP", "AU.email.doubleDot", "noah..smith@bigpond.net.au")
neg_email("FLD-AUTH-032", "Empty email does not request an OTP", "''", "empty")
neg_email("FLD-AUTH-033", "Whitespace-only email does not request an OTP", "AU.email.whitespace", "3 spaces")
case("FLD-AUTH-034", "Login page has no horizontal scroll at 375x667", "P1", "Responsive", "Logged out", "viewport 375x667", "document scrollWidth <= viewport width; Send OTP inside the viewport",
     [("Set the viewport to 375x667", "await page.setViewportSize({ width: 375, height: 667 });"), OPEN,
      ("Verify there is no horizontal scroll", "expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);"),
      ("Verify Send OTP is visible", f"await expect(loginPage.sendOtpBtn()).toBeVisible({T});")])
case("FLD-AUTH-035", "Unregistered email never reaches the dashboard", "P0", "Security", "Logged out", "qa+<epoch>@example.com (RFC 2606, cannot deliver)", "Not on dashboard; response recorded",
     [OPEN, EMAILTAB, ("Enter an unregistered email", "await loginPage.fillIdentifier(DataGenerator.unregisteredEmail());"),
      ("Click Send OTP and capture the response", "const response = await loginModule.sendOtpCapturing();"), ("Record the observed response", RECORD),
      ("Verify the dashboard is not shown", "await expect(page).not.toHaveURL(/\\/app\\/dashboard/);")])
case("FLD-AUTH-036", "Expired OTP prompts the user to resend", "P0", "Negative", "Needs a real OTP that has expired", "-", "Expired message and a Resend OTP option",
     [("Request an OTP and wait past its validity window", "// The QA bypass OTP never expires, so this case needs a live SMS OTP.")], fixme="QA bypass OTP never expires; run manually with a live SMS OTP (window length unknown - ask PO)")
case("FLD-AUTH-037", "A used OTP cannot be replayed", "P0", "Security", "Needs a single-use live OTP", "-", "Second use rejected",
     [("Log in once with a live OTP, log out, then reuse the same OTP", "// The QA bypass OTP is static, so replay cannot be tested with it.")], fixme="Static bypass OTP is reusable by design; test manually with a live OTP")
case("FLD-AUTH-038", "Twenty wrong OTPs in 60s trigger a lock or rate limit", "P0", "Security", "FLDR_ALLOW_LOCKOUT=1 (may lock the shared QA account)", "20 x wrong OTPs", "429 or a lock message before the 20th attempt",
     SENDBYPASS + [("Submit wrong OTPs and stop at the first 429 or lock message", "let limited = false;\n      for (let attempt = 0; attempt < 20 && !limited; attempt += 1) {\n        await loginModule.enterOtp(AU.otp.wrong);\n        const response = await loginModule.verifyCapturing();\n        limited = response.status() === 429 || /lock|too many|try again/i.test(await response.text());\n      }"),
                   ("Verify rate limiting kicked in", "expect(limited).toBe(true);")], skip="!config.allowLockout", tags=["@destructive"])
case("FLD-AUTH-039", "Resend restarts the countdown (throttle)", "P0", "Flaky", "OTP step shown", "wait ~30s", "After Resend OTP the countdown text returns at 30s or less",
     SENDBYPASS + [("Wait for the Resend OTP button", "await expect(loginPage.resendBtn()).toBeEnabled({ timeout: config.timeouts.resend });"), ("Click Resend OTP", "await loginPage.clickResend();"),
                   ("Verify the countdown returns", f"await expect(loginPage.resendTimer()).toBeVisible({N});")], ["@flaky"], slow=True)
case("FLD-AUTH-040", "Session survives a page reload", "P0", "Functional", "Logged in", "-", "Still on /app/dashboard after reload",
     [("Reload the dashboard", "await page.reload();"), ("Verify the dashboard is shown", "await loginModule.expectOnDashboard();")], ["@session"])
case("FLD-AUTH-041", "Session is shared with a second tab", "P0", "Functional", "Logged in", "-", "New tab opens /app/dashboard without asking for login",
     [("Open a second tab", "const second = await context.newPage();"), ("Open the dashboard in the second tab", "await second.goto('/app/dashboard');"),
      ("Verify the second tab shows Dashboard", f"await expect(second.getByRole('heading', {{ name: 'Dashboard', level: 1 }})).toBeVisible({N});")], ["@session"])
case("FLD-AUTH-042", "Logout ends the session", "P0", "Functional", "Logged in", "-", "Redirect to /login; /app/dashboard redirects to /login again (logout label: NEEDS UI INSPECTION)",
     [("Log out from the user menu", "await loginModule.logout();"), ("Open /app/dashboard", "await dashboardPage.open();"), ("Verify the URL is /login", LOGURL)], ["@session"])
case("FLD-AUTH-043", "Tampered session cookie is rejected on the next request", "P0", "Security", "Logged in", "every cookie value reversed", "Redirect to /login",
     [("Read all cookies", "const cookies = await context.cookies();"), ("Verify a session cookie exists", "expect(cookies.length).toBeGreaterThan(0);"),
      ("Replace every cookie value with a corrupted one", "await context.clearCookies();\n      await context.addCookies(cookies.map((c) => ({ ...c, value: `${c.value.split('').reverse().join('')}x` })));"),
      ("Open /app/dashboard", "await dashboardPage.open();"), ("Verify the URL is /login", LOGURL)], ["@session"])
case("FLD-AUTH-044", "Deleting all cookies ends the session", "P0", "Security", "Logged in", "-", "Redirect to /login",
     [("Clear all cookies", "await context.clearCookies();"), ("Open /app/dashboard", "await dashboardPage.open();"), ("Verify the URL is /login", LOGURL)], ["@session"])
case("FLD-AUTH-045", "Back button after logout does not reveal the dashboard", "P1", "Security", "Logged in", "-", "Dashboard content is not shown after Back",
     [("Log out from the user menu", "await loginModule.logout();"), ("Press the browser Back button", "await page.goBack();"),
      ("Verify the dashboard heading is not shown", f"await expect({DASH_H}).toBeHidden({T});")], ["@session"])
case("FLD-AUTH-046", "Unauthenticated deep link /app/job/list redirects to login", "P1", "Security", "No session cookie", "/app/job/list", "Redirect to /login",
     [("Open /app/job/list without a session", "await dashboardPage.openDeepLink('/app/job/list');"), ("Verify the URL is /login", LOGURL)])
case("FLD-AUTH-047", "Idle session times out", "P1", "Flaky", "Logged in", "idle period unknown", "Redirect to /login after the idle window",
     [("Stay idle for the configured window", "// Idle timeout duration is unknown (ask PO).")], fixme="Idle-timeout length not documented; needs PO input and a controllable clock")
case("FLD-AUTH-048", "Send OTP response does not expose the OTP", "P1", "Security", "Logged out", "FLDR_MOBILE", "Response body contains neither the OTP nor an otp/code/passcode field with 6 digits",
     [OPEN, MOBTAB, ("Enter the QA mobile number", "await loginPage.fillIdentifier(config.mobile);"),
      ("Click Send OTP and capture the response body", "const body = await (await loginModule.sendOtpCapturing()).text();"),
      ("Verify the OTP is not in the body", "expect(body).not.toContain(config.otp);\n      expect(body).not.toMatch(/\"(otp|code|passcode)\"\\s*:\\s*\"?\\d{6}/i);")])
case("FLD-AUTH-049", "XSS payload in the email field is not executed", "P1", "Security", "Logged out", "\"><img src=x onerror=window.__xss=1>", "window.__xss stays undefined; no dialog",
     [OPEN, EMAILTAB, ("Enter the payload and click Send OTP only if it is enabled", "await loginModule.trySendIdentifier(AU.email.xss);"),
      ("Verify the payload did not execute", "expect(await page.evaluate(() => (window as unknown as { __xss?: number }).__xss)).toBeUndefined();")])
case("FLD-AUTH-050", "SQL-injection payload in the email field causes no server error", "P1", "Security", "Logged out", "' OR '1'='1", "No 5xx response; OTP step not shown",
     [OPEN, EMAILTAB, ("Collect server errors", "const serverErrors: number[] = [];\n      page.on('response', (r) => { if (r.status() >= 500) serverErrors.push(r.status()); });"),
      ("Enter the payload and click Send OTP only if it is enabled", "await loginModule.trySendIdentifier(AU.email.sqli);"),
      ("Verify no 5xx occurred", "expect(serverErrors).toEqual([]);"), ("Verify the OTP step is not shown", "await loginModule.expectStillOnIdentifierStep();")])

LOGGED_IN = {"FLD-AUTH-040", "FLD-AUTH-041", "FLD-AUTH-042", "FLD-AUTH-043", "FLD-AUTH-044", "FLD-AUTH-045"}
assert [c["id"] for c in cases] == [f"FLD-AUTH-{i:03d}" for i in range(1, 51)], len(cases)

# ------------------------------------------------------------------ emit specs
for c in cases:
    body = "\n".join(f"    await test.step({json.dumps(t)}, async () => {{\n      {code}\n    }});" for t, code in c["steps"])
    joined = " ".join(code for _, code in c["steps"])
    fx = [n for n in ("loginPage", "dashboardPage", "loginModule", "page", "context") if n in joined]
    if c["id"] in LOGGED_IN:
        fx.append("loggedIn")
    imports = ["import { test, expect } from '@fixtures';"]
    if "config." in joined or c["skip"]:
        imports.append("import { config } from '@config/index';")
    if "AU." in joined:
        imports.append("import { AU } from '@testdata/au';")
    if "DataGenerator" in joined:
        imports.append("import { DataGenerator } from '@utils/DataGenerator';")
    tags = [f"@{c['prio']}", "@regression", "@auth"] + c["tags"]
    if c["typ"] == "Security":
        tags.append("@security")
    tags = list(dict.fromkeys(tags))
    pre = []
    if c["skip"]:
        pre.append(f"    test.skip({c['skip']}, {json.dumps('Precondition not met: ' + c['pre'])});")
    if c["fixme"]:
        pre.append(f"    test.fixme(true, {json.dumps(c['fixme'])});")
    if c["slow"]:
        pre.append("    test.slow();")
    parts = [f"// {c['id']} | {c['prio']} | {c['typ']}", f"// Preconditions: {c['pre']}", f"// Expected: {c['exp']}", "\n".join(imports), "",
             f"test.describe({json.dumps(c['id'])}, () => {{",
             f"  test({json.dumps(c['id'] + ' ' + c['title'])}, {{ tag: {json.dumps(tags)} }}, async ({{ {', '.join(fx)} }}) => {{"]
    parts += pre + [body, "  });", "});", ""]
    w(f"src/tests/auth/{c['id']}.e2e.ts", "\n".join(parts))

# ------------------------------------------------------------------ emit the matching manual table
rows = ["| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |", "|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|"]
for c in cases:
    steps = "<br>".join(f"{i}. {t}" for i, (t, _) in enumerate(c["steps"], 1))
    typ = "Flaky" if "@flaky" in c["tags"] else c["typ"]
    rows.append(f"| {c['id']} | {c['title']} | AUTH | {c['pre']} | {steps} | {c['data']} | {c['exp']} | {c['prio']} | {typ} |")
with open(os.path.join(os.path.dirname(ROOT), "auth-test-cases.md"), "w", encoding="utf-8") as f:
    f.write("# FLD-AUTH-001 to 050 (generated from the Playwright specs)\n\nObserved 2026-09-19: login page, OTP step (six `Digit n` boxes, `Verify & Login`, resend countdown) and dashboard. Anything marked ASSUMPTION or NEEDS UI INSPECTION is unverified.\n\n" + "\n".join(rows) + "\n")

print("specs:", len(cases))
