'use strict';

/**
 * @fileoverview Nodemailer implementation of EmailServicePort.
 */

const nodemailer = require('nodemailer');
const EmailServicePort = require('../../../domain/ports/EmailServicePort');

class NodemailerEmailAdapter extends EmailServicePort {
  /**
   * @param {Object} config
   * @param {string} config.host  - SMTP hostname.
   * @param {number} config.port  - SMTP port.
   * @param {string} config.user  - SMTP auth username.
   * @param {string} config.pass  - SMTP auth password.
   * @param {string} config.from  - Sender address (e.g. "noreply@example.com").
   */
  constructor({ host, port, user, pass, from }) {
    super();
    this._from = from;
    this._transporter = nodemailer.createTransport({
      host,
      port,
      secure: port === 465,
      auth: user && pass ? { user, pass } : undefined,
    });
  }

  /**
   * Sends an account-verification email.
   *
   * @param {string} to    - Recipient email address.
   * @param {string} token - Verification token.
   * @returns {Promise<void>}
   */
  async sendVerificationEmail(to, token) {
    const verifyUrl = `${process.env.APP_BASE_URL || 'http://localhost:3000'}/api/auth/verify/${token}`;

    await this._transporter.sendMail({
      from: this._from,
      to,
      subject: 'Verify your account',
      text: `Please verify your account by visiting: ${verifyUrl}`,
      html: `
        <p>Thank you for registering!</p>
        <p>Please verify your account by clicking the link below:</p>
        <p><a href="${verifyUrl}">Verify my account</a></p>
        <p>If you did not create an account, you can safely ignore this email.</p>
      `,
    });
  }

  /**
   * Sends a password-reset email.
   *
   * @param {string} to    - Recipient email address.
   * @param {string} token - Password-reset token.
   * @returns {Promise<void>}
   */
  async sendPasswordResetEmail(to, token) {
    const resetUrl = `${process.env.APP_BASE_URL || 'http://localhost:3000'}/reset-password?token=${token}`;

    await this._transporter.sendMail({
      from: this._from,
      to,
      subject: 'Reset your password',
      text: `Reset your password by visiting: ${resetUrl}\n\nThis link expires in 1 hour.`,
      html: `
        <p>You requested a password reset.</p>
        <p>Click the link below to set a new password (valid for 1 hour):</p>
        <p><a href="${resetUrl}">Reset my password</a></p>
        <p>If you did not request this, you can safely ignore this email.</p>
      `,
    });
  }
}

module.exports = NodemailerEmailAdapter;
