'use strict';

/**
 * @fileoverview Port (interface) for authentication / cryptography operations.
 * Concrete adapters must extend this class and implement every method.
 */

class AuthServicePort {
  /**
   * Generates a signed JWT for the given payload.
   *
   * @param {Record<string, unknown>} payload - Data to encode inside the token.
   * @returns {string} Signed JWT string.
   */
  // eslint-disable-next-line no-unused-vars
  generateToken(payload) {
    throw new Error('AuthServicePort.generateToken() — Not implemented');
  }

  /**
   * Verifies and decodes a JWT string.
   *
   * @param {string} token - JWT string to verify.
   * @returns {Record<string, unknown>} Decoded token payload.
   * @throws {Error} If the token is invalid or expired.
   */
  // eslint-disable-next-line no-unused-vars
  verifyToken(token) {
    throw new Error('AuthServicePort.verifyToken() — Not implemented');
  }

  /**
   * Hashes a plain-text password using bcrypt.
   *
   * @param {string} plain - Plain-text password.
   * @returns {Promise<string>} Bcrypt hash string.
   */
  // eslint-disable-next-line no-unused-vars
  async hashPassword(plain) {
    throw new Error('AuthServicePort.hashPassword() — Not implemented');
  }

  /**
   * Compares a plain-text password against a bcrypt hash.
   *
   * @param {string} plain - Plain-text password to test.
   * @param {string} hash  - Bcrypt hash to compare against.
   * @returns {Promise<boolean>} True if the password matches the hash.
   */
  // eslint-disable-next-line no-unused-vars
  async comparePassword(plain, hash) {
    throw new Error('AuthServicePort.comparePassword() — Not implemented');
  }
}

module.exports = AuthServicePort;
