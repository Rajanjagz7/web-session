const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env.nsw-jobs') });

const BASE_URL = process.env.NSW_BASE_URL || 'https://nswdev.rebatem8.com.au';
const EMAIL = process.env.NSW_LOGIN_EMAIL;
const PASSWORD = process.env.NSW_LOGIN_PASSWORD;
const INSTALLER_COMPANY = process.env.NSW_INSTALLER_COMPANY || 'Rajan Testing Company';

module.exports = { BASE_URL, EMAIL, PASSWORD, INSTALLER_COMPANY };
