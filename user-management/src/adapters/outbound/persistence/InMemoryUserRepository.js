'use strict';

/**
 * @fileoverview In-memory implementation of UserRepositoryPort.
 * Suitable for development, testing, and as a reference implementation.
 */

const UserRepositoryPort = require('../../../domain/ports/UserRepositoryPort');
const User = require('../../../domain/entities/User');

class InMemoryUserRepository extends UserRepositoryPort {
  constructor() {
    super();
    /** @type {Map<string, User>} */
    this._store = new Map();
  }

  /**
   * Finds a user by their unique identifier.
   *
   * @param {string} id
   * @returns {Promise<User|null>}
   */
  async findById(id) {
    return this._store.get(id) ?? null;
  }

  /**
   * Finds a user by their email address (case-insensitive).
   *
   * @param {string} email
   * @returns {Promise<User|null>}
   */
  async findByEmail(email) {
    const normalised = email.toLowerCase();
    for (const user of this._store.values()) {
      if (user.email.toLowerCase() === normalised) {
        return user;
      }
    }
    return null;
  }

  /**
   * Persists a new user entity.
   *
   * @param {User} user
   * @returns {Promise<User>}
   */
  async save(user) {
    this._store.set(user.id, user);
    return user;
  }

  /**
   * Updates an existing user entity.
   * Stamps updatedAt before persisting.
   *
   * @param {User} user
   * @returns {Promise<User>}
   * @throws {Error} If the user does not exist in the store.
   */
  async update(user) {
    if (!this._store.has(user.id)) {
      const err = new Error(`User with id "${user.id}" not found`);
      err.status = 404;
      throw err;
    }
    user.updatedAt = new Date();
    this._store.set(user.id, user);
    return user;
  }

  /**
   * Deletes a user by their unique identifier.
   *
   * @param {string} id
   * @returns {Promise<void>}
   * @throws {Error} If the user does not exist in the store.
   */
  async delete(id) {
    if (!this._store.has(id)) {
      const err = new Error(`User with id "${id}" not found`);
      err.status = 404;
      throw err;
    }
    this._store.delete(id);
  }

  /**
   * Finds a user by their verificationToken.
   * Convenience method used by VerifyAccount use case.
   *
   * @param {string} token
   * @returns {Promise<User|null>}
   */
  async findByVerificationToken(token) {
    for (const user of this._store.values()) {
      if (user.verificationToken === token) {
        return user;
      }
    }
    return null;
  }

  /**
   * Finds a user by their resetToken.
   * Convenience method used by password-reset flows.
   *
   * @param {string} token
   * @returns {Promise<User|null>}
   */
  async findByResetToken(token) {
    for (const user of this._store.values()) {
      if (user.resetToken === token) {
        return user;
      }
    }
    return null;
  }

  /**
   * Clears all entries from the store.
   * Intended for use in test fixtures to provide per-test isolation.
   * TODO: Review usage in pytest fixtures — call this in a function-scoped
   * fixture's teardown (yield-based) to reset state between tests.
   *
   * @returns {void}
   */
  clear() {
    this._store.clear();
  }
}

module.exports = InMemoryUserRepository;