'use strict';

/**
 * @fileoverview RegisterUser use case.
 * Orchestrates user registration: validation → duplicate check → hash password
 * → persist → send verification email.
 */

const { v4: uuidv4 } = require('uuid');
const User = require('../../domain/entities/User');

class RegisterUser {
  /**
   * @param {Object} deps
   * @param {import('../../domain/ports/UserRepositoryPort')} deps.userRepository
   * @param {import('../../domain/ports/EmailServicePort')}   deps.emailService
   * @param {import('../../domain/ports/AuthServicePort')}    deps.authService
   */
  constructor({ userRepository, emailService, authService }) {
    this.userRepository = userRepository;
    this.emailService = emailService;
    this.authService = authService;
  }

  /**
   * Registers a new user account.
   *
   * @param {Object} input
   * @param {string} input.email    - The user's email address.
   * @param {string} input.password - The user's plain-text password.
   * @returns {Promise<ReturnType<User['toPublicJSON']>>} Public user representation.
   * @throws {Error} 400 if email or password are missing / invalid.
   * @throws {Error} 409 if the email is already registered.
   */
  async execute({ email, password }) {
    // ── Input validation ───────────────────────────────────────────────────────
    if (!email || typeof email !== 'string') {
      const err = new Error('Email is required');
      err.status = 400;
      throw err;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      const err = new Error('Invalid email format');
      err.status = 400;
      throw err;
    }

    if (!password || typeof password !== 'string' || password.length < 8) {
      const err = new Error('Password must be at least 8 characters');
      err.status = 400;
      throw err;
    }

    const normalizedEmail = email.trim().toLowerCase();

    // ── Duplicate check ────────────────────────────────────────────────────────
    const existing = await this.userRepository.findByEmail(normalizedEmail);
    if (existing) {
      const err = new Error('Email is already registered');
      err.status = 409;
      throw err;
    }

    // ── Hash password & build entity ───────────────────────────────────────────
    const passwordHash = await this.authService.hashPassword(password);
    const verificationToken = uuidv4();

    const user = new User({
      id: uuidv4(),
      email: normalizedEmail,
      passwordHash,
      isVerified: false,
      verificationToken,
    });

    // ── Persist ────────────────────────────────────────────────────────────────
    await this.userRepository.save(user);

    // ── Send verification email (non-blocking failure) ─────────────────────────
    try {
      await this.emailService.sendVerificationEmail(user.email, verificationToken);
    } catch (emailErr) {
      console.error('[RegisterUser] Failed to send verification email:', emailErr.message);
    }

    return user.toPublicJSON();
  }
}

module.exports = RegisterUser;
