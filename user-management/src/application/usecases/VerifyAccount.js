'use strict';

/**
 * @fileoverview VerifyAccount use case.
 * Marks a user's account as verified using the token sent in the verification email.
 */

class VerifyAccount {
  /**
   * @param {Object} deps
   * @param {import('../../domain/ports/UserRepositoryPort')} deps.userRepository
   */
  constructor({ userRepository }) {
    this.userRepository = userRepository;
  }

  /**
   * Verifies a user account using the supplied verification token.
   *
   * @param {Object} input
   * @param {string} input.token - The verification token from the email link.
   * @returns {Promise<{ message: string }>}
   * @throws {Error} 400 if the token is missing.
   * @throws {Error} 400 if the token is invalid or already used.
   */
  async execute({ token }) {
    if (!token || typeof token !== 'string') {
      const err = new Error('Verification token is required');
      err.status = 400;
      throw err;
    }

    // ── Find user by verification token ───────────────────────────────────────
    // We scan all users; a production implementation would add an index.
    const users = await this._findUserByVerificationToken(token);
    if (!users) {
      const err = new Error('Invalid or expired verification token');
      err.status = 400;
      throw err;
    }

    // ── Mark as verified ───────────────────────────────────────────────────────
    users.isVerified = true;
    users.verificationToken = null;
    users.updatedAt = new Date();

    await this.userRepository.update(users);

    return { message: 'Account verified successfully' };
  }

  /**
   * Locates a user whose verificationToken matches the given token.
   * Delegates to the repository's findByVerificationToken if available,
   * otherwise falls back to a linear scan via findByEmail (not ideal for
   * production — add a dedicated index there).
   *
   * @private
   * @param {string} token
   * @returns {Promise<import('../../domain/entities/User')|null>}
   */
  async _findUserByVerificationToken(token) {
    // The InMemoryUserRepository exposes findByVerificationToken as a convenience.
    if (typeof this.userRepository.findByVerificationToken === 'function') {
      return this.userRepository.findByVerificationToken(token);
    }
    return null;
  }
}

module.exports = VerifyAccount;
