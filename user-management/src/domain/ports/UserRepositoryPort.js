'use strict';

/**
 * @fileoverview Port (interface) for user persistence operations.
 * Concrete adapters must extend this class and implement every method.
 */

class UserRepositoryPort {
  /**
   * Finds a user by their unique identifier.
   *
   * @param {string} id - UUID of the user.
   * @returns {Promise<import('../entities/User')|null>} The user, or null if not found.
   */
  // eslint-disable-next-line no-unused-vars
  async findById(id) {
    throw new Error('UserRepositoryPort.findById() — Not implemented');
  }

  /**
   * Finds a user by their email address.
   *
   * @param {string} email - Email address to look up.
   * @returns {Promise<import('../entities/User')|null>} The user, or null if not found.
   */
  // eslint-disable-next-line no-unused-vars
  async findByEmail(email) {
    throw new Error('UserRepositoryPort.findByEmail() — Not implemented');
  }

  /**
   * Persists a new user record.
   *
   * @param {import('../entities/User')} user - User entity to save.
   * @returns {Promise<import('../entities/User')>} The saved user entity.
   */
  // eslint-disable-next-line no-unused-vars
  async save(user) {
    throw new Error('UserRepositoryPort.save() — Not implemented');
  }

  /**
   * Updates an existing user record.
   *
   * @param {import('../entities/User')} user - User entity with updated fields.
   * @returns {Promise<import('../entities/User')>} The updated user entity.
   */
  // eslint-disable-next-line no-unused-vars
  async update(user) {
    throw new Error('UserRepositoryPort.update() — Not implemented');
  }

  /**
   * Deletes a user record by their unique identifier.
   *
   * @param {string} id - UUID of the user to delete.
   * @returns {Promise<void>}
   */
  // eslint-disable-next-line no-unused-vars
  async delete(id) {
    throw new Error('UserRepositoryPort.delete() — Not implemented');
  }
}

module.exports = UserRepositoryPort;
