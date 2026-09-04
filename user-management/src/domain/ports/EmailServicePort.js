'use strict';

/**
 * @fileoverview Port (interface) for email delivery operations.
 * Concrete adapters must extend this class and implement every method.
 */

class EmailServicePort {
  /**
   * Sends an account-verification email containing the provided token.
   *
   * @param {string} to    - Recipient email address.
   * @param {string} token - Verification token to embed in the email.
   * @returns {Promise<void>}
   */
  // eslint-disable-next-line no-unused-vars
  async sendVerificationEmail(to, token) {
    throw new Error('EmailServicePort.sendVerificationEmail() — Not implemented');
  }

  /**
   * Sends a password-reset email containing the provided token.
   *
   * @param {string} to    - Recipient email address.
   * @param {string} token - Password-reset token to embed in the email.
   * @returns {Promise<void>}
   */
  // eslint-disable-next-line no-unused-vars
  async sendPasswordResetEmail(to, token) {
    throw new Error('EmailServicePort.sendPasswordResetEmail() — Not implemented');
  }
}

module.exports = EmailServicePort;
