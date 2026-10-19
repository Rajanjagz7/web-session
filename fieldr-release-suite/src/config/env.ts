import dotenv from 'dotenv';
import type { Persona } from '../notes';

dotenv.config();

const get = (key: string, fallback: string): string => {
  const v = process.env[key];
  return v !== undefined && v !== '' ? v : fallback;
};

/** Every URL and path comes from .env. Defaults are placeholders on a reserved .invalid domain, never real hosts. */
export const env = {
  baseUrl: get('BASE_URL', 'https://staff.example.invalid'),
  portalUrl: get('PORTAL_URL', 'https://portal.example.invalid'),
  adminUrl: get('ADMIN_URL', 'https://admin.example.invalid'),
  apiUrl: get('API_URL', 'https://api.example.invalid'),
  serviceToken: get('SERVICE_TOKEN', ''),
  api: {
    customers: get('API_PATH_CUSTOMERS', '/TODO/customers'),
    customer: get('API_PATH_CUSTOMER', '/TODO/customers/{id}'),
    quotes: get('API_PATH_QUOTES', '/TODO/quotes'),
    quotePdf: get('API_PATH_QUOTE_PDF', '/TODO/quotes/{id}/pdf'),
    invoices: get('API_PATH_INVOICES', '/TODO/invoices'),
    invoicePdf: get('API_PATH_INVOICE_PDF', '/TODO/invoices/{id}/pdf'),
    jobs: get('API_PATH_JOBS', '/TODO/jobs'),
    job: get('API_PATH_JOB', '/TODO/jobs/{id}'),
    jobPdf: get('API_PATH_JOB_PDF', '/TODO/jobs/{id}/pdf'),
    jobBudget: get('API_PATH_JOB_BUDGET', '/TODO/jobs/{id}/budget'),
    jobTimeLogs: get('API_PATH_JOB_TIMELOGS', '/TODO/jobs/{id}/time-logs'),
    jobWorklogReport: get('API_PATH_JOB_WORKLOG_REPORT', '/TODO/jobs/{id}/worklog-report'),
    orders: get('API_PATH_ORDERS', '/TODO/job-orders'),
    orderPdf: get('API_PATH_ORDER_PDF', '/TODO/job-orders/{id}/pdf'),
    timesheetPdf: get('API_PATH_TIMESHEET_PDF', '/TODO/timesheets/pdf'),
    reportPdf: get('API_PATH_REPORT_PDF', '/TODO/reports/{id}/pdf'),
    users: get('API_PATH_USERS', '/TODO/users'),
    user: get('API_PATH_USER', '/TODO/users/{id}'),
    roles: get('API_PATH_ROLES', '/TODO/roles'),
    invites: get('API_PATH_INVITES', '/TODO/invites'),
    invite: get('API_PATH_INVITE', '/TODO/invites/{id}'),
    portalAccess: get('API_PATH_PORTAL_ACCESS', '/TODO/customers/{id}/portal-access'),
    adminOverview: get('API_PATH_ADMIN_OVERVIEW', '/TODO/platform/overview'),
  },
  routes: {
    login: get('ROUTE_LOGIN', '/login'),
    schedule: get('ROUTE_SCHEDULE', '/TODO/schedule'),
    quotes: get('ROUTE_QUOTES', '/TODO/quotes'),
    customers: get('ROUTE_CUSTOMERS', '/TODO/customers'),
    jobs: get('ROUTE_JOBS', '/TODO/jobs'),
    jobNew: get('ROUTE_JOB_NEW', '/TODO/jobs/new'),
    roles: get('ROUTE_ROLES', '/TODO/settings/roles'),
    invites: get('ROUTE_INVITES', '/TODO/invites'),
    subscription: get('ROUTE_SUBSCRIPTION', '/TODO/settings/subscription'),
    purchaseHistory: get('ROUTE_PURCHASE_HISTORY', '/TODO/settings/purchase-history'),
    insights: get('ROUTE_INSIGHTS', '/TODO/insights'),
    profile: get('ROUTE_PROFILE', '/TODO/profile'),
    users: get('ROUTE_USERS', '/TODO/users'),
    portalQuotes: get('ROUTE_PORTAL_QUOTES', '/TODO/quotes'),
    portalJobs: get('ROUTE_PORTAL_JOBS', '/TODO/jobs'),
    adminOverview: get('ROUTE_ADMIN_OVERVIEW', '/TODO/overview'),
    adminAccounts: get('ROUTE_ADMIN_ACCOUNTS', '/TODO/accounts'),
    adminRoles: get('ROUTE_ADMIN_ROLES', '/TODO/roles'),
  },
  /** Pre-existing records the suite cannot create itself (TODO: fill in .env; tests stay fixme while blank). */
  fixtures: {
    portalCustomerId: get('PORTAL_CUSTOMER_ID', ''),
    portalCompanyName: get('PORTAL_COMPANY_NAME', ''),
    portalContactName: get('PORTAL_CONTACT_NAME', ''),
    orderId: get('FIXTURE_ORDER_ID', ''),
    reportId: get('FIXTURE_REPORT_ID', ''),
    catalogueConfigured: get('FIXTURE_CATALOGUE_ITEM_EXISTS', ''),
  },
  /** Release-note facts the notes state verbatim. */
  expected: {
    convertedBadge: get('EXPECTED_CONVERTED_BADGE_TEXT', 'Converted to Job'),
    portalAccessRemoved: get('EXPECTED_PORTAL_ACCESS_REMOVED_TEXT', 'You no longer have access to the customer portal'),
    /** TODO: not in the release notes. Fill in .env; dependent tests stay fixme while blank. */
    phoneDisplayFormat: get('EXPECTED_PHONE_DISPLAY_FORMAT', ''),
    abnDisplayFormat: get('EXPECTED_ABN_DISPLAY_FORMAT', ''),
    accountsRowLimitText: get('EXPECTED_ACCOUNTS_ROW_LIMIT_TEXT', ''),
  },
} as const;

/** Persona credentials (mobile + OTP). Blank values make auth.setup write an empty state. */
export const personaCreds: Readonly<Record<Persona, { mobile: string; otp: string; portal: boolean; admin: boolean }>> = {
  'cost-viewer': { mobile: get('PERSONA_COST_VIEWER_MOBILE', ''), otp: get('PERSONA_COST_VIEWER_OTP', ''), portal: false, admin: false },
  'no-cost-viewer': { mobile: get('PERSONA_NO_COST_VIEWER_MOBILE', ''), otp: get('PERSONA_NO_COST_VIEWER_OTP', ''), portal: false, admin: false },
  'no-permission': { mobile: get('PERSONA_NO_PERMISSION_MOBILE', ''), otp: get('PERSONA_NO_PERMISSION_OTP', ''), portal: false, admin: false },
  'portal-customer': { mobile: get('PERSONA_PORTAL_CUSTOMER_MOBILE', ''), otp: get('PERSONA_PORTAL_CUSTOMER_OTP', ''), portal: true, admin: false },
  'super-admin': { mobile: get('PERSONA_SUPER_ADMIN_MOBILE', ''), otp: get('PERSONA_SUPER_ADMIN_OTP', ''), portal: false, admin: false },
};

export const PERSONAS: readonly Persona[] = ['cost-viewer', 'no-cost-viewer', 'no-permission', 'portal-customer', 'super-admin'];

export const fill = (path: string, id: string): string => path.replace('{id}', encodeURIComponent(id));

/**
 * URL for an API call made AS the logged-in persona (request fixture, cookies from storageState).
 * TODO(confirm): assumes the app serves its API on the same origin as the app. If the API lives on API_URL with bearer
 * tokens kept in localStorage, add an Authorization header taken from the persona's storage state here (one place).
 */
export const personaApi = (path: string, base: string = env.baseUrl): string => new URL(path, base).toString();
