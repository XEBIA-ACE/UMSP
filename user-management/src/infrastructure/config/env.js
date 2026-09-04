'use strict';

/**
 * @fileoverview Loads and validates required environment variables.
 * Throws at startup if any required variable is missing.
 */

/**
 * @typedef {Object} EnvConfig
 * @property {number}  PORT          - HTTP port the server listens on.
 * @property {string}  JWT_SECRET    - Secret key used to sign JWTs.
 * @property {string}  JWT_EXPIRES_IN - JWT expiry duration (e.g. "7d").
 * @property {string}  SMTP_HOST     - SMTP server hostname.
 * @property {number}  SMTP_PORT     - SMTP server port.
 * @property {string}  SMTP_USER     - SMTP authentication username.
 * @property {string}  SMTP_PASS     - SMTP authentication password.
 * @property {string}  EMAIL_FROM    - Sender address for outgoing emails.
 * @property {string}  NODE_ENV      - Runtime environment identifier.
 */

const required = ['JWT_SECRET'];

for (const key of required) {
  if (!process.env[key]) {
    throw new Error(`[env] Missing required environment variable: ${key}`);
  }
}

/** @type {EnvConfig} */
const env = {
  PORT: parseInt(process.env.PORT || '3000', 10),
  JWT_SECRET: process.env.JWT_SECRET,
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '7d',
  SMTP_HOST: process.env.SMTP_HOST || 'localhost',
  SMTP_PORT: parseInt(process.env.SMTP_PORT || '587', 10),
  SMTP_USER: process.env.SMTP_USER || '',
  SMTP_PASS: process.env.SMTP_PASS || '',
  EMAIL_FROM: process.env.EMAIL_FROM || 'noreply@example.com',
  NODE_ENV: process.env.NODE_ENV || 'development',
};

module.exports = env;
