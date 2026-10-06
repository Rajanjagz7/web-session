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
