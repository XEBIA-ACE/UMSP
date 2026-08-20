'use strict';

/**
 * @fileoverview JWT + bcrypt implementation of AuthServicePort.
 */

const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const AuthServicePort = require('../../../domain/ports/AuthServicePort');

const BCRYPT_SALT_ROUNDS = 12;

class JwtAuthAdapter extends AuthServicePort {
  /**
   * @param {Object} config
   * @param {string} config.secret    - Secret key used to sign JWTs.
   * @param {string} config.expiresIn - Token expiry duration (e.g. "7d", "1h").
   */
  constructor({ secret, expiresIn }) {
    super();
    this._secret = secret;
    this._expiresIn = expiresIn;
  }

  /**
   * Generates a signed JWT for the given payload.
   *
   * @param {Record<string, unknown>} payload - Data to encode inside the token.
   * @returns {string} Signed JWT string.
   */
  generateToken(payload) {
    return jwt.sign(payload, this._secret, { expiresIn: this._expiresIn });
  }

  /**
   * Verifies and decodes a JWT string.
   *
   * @param {string} token - JWT string to verify.
   * @returns {Record<string, unknown>} Decoded token payload.
   * @throws {Error} If the token is invalid or expired.
   */
  verifyToken(token) {
    return jwt.verify(token, this._secret);
  }

  /**
   * Hashes a plain-text password using bcrypt.
   *
   * @param {string} plain - Plain-text password.
   * @returns {Promise<string>} Bcrypt hash string.
   */
  async hashPassword(plain) {
    return bcrypt.hash(plain, BCRYPT_SALT_ROUNDS);
  }

  /**
   * Compares a plain-text password against a bcrypt hash.
   *
   * @param {string} plain - Plain-text password to test.
   * @param {string} hash  - Bcrypt hash to compare against.
   * @returns {Promise<boolean>} True if the password matches the hash.
   */
  async comparePassword(plain, hash) {
    return bcrypt.compare(plain, hash);
  }
}

module.exports = JwtAuthAdapter;
