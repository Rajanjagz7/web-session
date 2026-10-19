import dotenv from 'dotenv';
dotenv.config();

export const config = {
  ui: {
    baseUrl: process.env.UI_BASE_URL || 'https://www.saucedemo.com',
  },
  api: {
    baseUrl: process.env.API_BASE_URL || 'https://fakestoreapi.com',
    timeout: Number(process.env.API_TIMEOUT) || 30_000,
  },
  credentials: {
    username: process.env.TEST_USERNAME || 'standard_user',
    password: process.env.TEST_PASSWORD || 'secret_sauce',
  },
  logging: {
    level: process.env.LOG_LEVEL || 'INFO',
  },
} as const;
