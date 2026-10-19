// Reuses the existing NSW creds file from 1er-tests instead of duplicating
// it or adding a dotenv dependency - just a tiny inline parser.
const fs = require('fs');
const path = require('path');

const envPath = path.join(__dirname, '..', '1er-tests', '.env.nsw-jobs');
const env = {};
for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;
  const eq = trimmed.indexOf('=');
  if (eq === -1) continue;
  env[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
}

module.exports = {
  BASE_URL: process.env.NSW_BASE_URL || env.NSW_BASE_URL || 'https://nswdev.rebatem8.com.au',
  EMAIL: process.env.NSW_LOGIN_EMAIL || env.NSW_LOGIN_EMAIL,
  PASSWORD: process.env.NSW_LOGIN_PASSWORD || env.NSW_LOGIN_PASSWORD,
  INSTALLER_COMPANY: process.env.NSW_INSTALLER_COMPANY || env.NSW_INSTALLER_COMPANY || 'Rajan Testing Company',
};
