'use strict';

/**
 * @fileoverview LoginUser use case.
 * Authenticates a user by email + password and returns a signed JWT.
 */

class LoginUser {
  /**
   * @param {Object} deps
   * @param {import('../../domain/ports/UserRepositoryPort')} deps.userRepository
   * @param {import('../../domain/ports/AuthServicePort')}    deps.authService
   */
  constructor({ userRepository, authService }) {
    this.userRepository = userRepository;
    this.authService = authService;
  }

  /**
   * Authenticates a user and issues a JWT.
   *
   * @param {Object} input
   * @param {string} input.email    - The user's email address.
   * @param {string} input.password - The user's plain-text password.
   * @returns {Promise<{ token: string, user: ReturnType<import('../../domain/entities/User')['toPublicJSON']> }>}
   * @throws {Error} 400 if email or password are missing.
   * @throws {Error} 401 if credentials are invalid.
   * @throws {Error} 403 if the account has not been verified.
   */
  async execute({ email, password }) {
    // ── Input validation ───────────────────────────────────────────────────────
    if (!email || !password) {
      const err = new Error('Email and password are required');
      err.status = 400;
      throw err;
    }

    const normalizedEmail = email.trim().toLowerCase();

    // ── Lookup user ────────────────────────────────────────────────────────────
    const user = await this.userRepository.findByEmail(normalizedEmail);
    if (!user) {
      const err = new Error('Invalid email or password');
      err.status = 401;
      throw err;
    }

    // ── Verified check ─────────────────────────────────────────────────────────
    if (!user.isVerified) {
      const err = new Error('Account has not been verified. Please check your email.');
      err.status = 403;
      throw err;
    }

    // ── Password comparison ────────────────────────────────────────────────────
    const isMatch = await this.authService.comparePassword(password, user.passwordHash);
    if (!isMatch) {
      const err = new Error('Invalid email or password');
      err.status = 401;
      throw err;
    }

    // ── Generate token ─────────────────────────────────────────────────────────
    const token = this.authService.generateToken({ sub: user.id, email: user.email });

    return { token, user: user.toPublicJSON() };
  }
}

module.exports = LoginUser;
