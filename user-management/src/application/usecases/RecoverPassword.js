'use strict';

/**
 * @fileoverview RecoverPassword use case.
 * Generates a password-reset token and dispatches a reset email.
 */

const { v4: uuidv4 } = require('uuid');

/** Duration (ms) before a reset token expires — 1 hour. */
const RESET_TOKEN_TTL_MS = 60 * 60 * 1000;

class RecoverPassword {
  /**
   * @param {Object} deps
   * @param {import('../../domain/ports/UserRepositoryPort')} deps.userRepository
   * @param {import('../../domain/ports/EmailServicePort')}   deps.emailService
   */
  constructor({ userRepository, emailService }) {
    this.userRepository = userRepository;
    this.emailService = emailService;
  }

  /**
   * Initiates the password-recovery flow for the given email address.
   * Always returns the same success message to avoid user-enumeration attacks.
   *
   * @param {Object} input
   * @param {string} input.email - Email address of the account to recover.
   * @returns {Promise<{ message: string }>}
   * @throws {Error} 400 if email is missing.
   */
  async execute({ email }) {
    if (!email || typeof email !== 'string') {
      const err = new Error('Email is required');
      err.status = 400;
      throw err;
    }

    const normalizedEmail = email.trim().toLowerCase();

    // Silently succeed when the email is not registered (anti-enumeration)
    const user = await this.userRepository.findByEmail(normalizedEmail);
    if (!user) {
      return { message: 'Password reset email sent' };
    }

    // ── Generate reset token ───────────────────────────────────────────────────
    user.resetToken = uuidv4();
    user.resetTokenExpiry = new Date(Date.now() + RESET_TOKEN_TTL_MS);
    user.updatedAt = new Date();

    await this.userRepository.update(user);

    // ── Send reset email (non-blocking failure) ────────────────────────────────
    try {
      await this.emailService.sendPasswordResetEmail(user.email, user.resetToken);
    } catch (emailErr) {
      console.error('[RecoverPassword] Failed to send reset email:', emailErr.message);
    }

    return { message: 'Password reset email sent' };
  }
}

module.exports = RecoverPassword;
