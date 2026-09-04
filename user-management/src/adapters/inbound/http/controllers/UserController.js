'use strict';

/**
 * @fileoverview UserController — handles user-profile HTTP requests.
 */

class UserController {
  /**
   * @param {Object} deps
   * @param {import('../../../../domain/ports/UserRepositoryPort')} deps.userRepository
   */
  constructor({ userRepository }) {
    this.userRepository = userRepository;

    this.getProfile = this.getProfile.bind(this);
  }

  /**
   * GET /api/users/profile
   * Returns the authenticated user's public profile.
   * Requires the authMiddleware to have populated req.user.
   *
   * @param {import('express').Request & { user: import('../../../../domain/entities/User') }} req
   * @param {import('express').Response}   res
   * @param {import('express').NextFunction} next
   * @returns {Promise<void>}
   */
  async getProfile(req, res, next) {
    try {
      // req.user is attached by authMiddleware and is a full User entity
      const user = await this.userRepository.findById(req.user.sub);
      if (!user) {
        const err = new Error('User not found');
        err.status = 404;
        throw err;
      }
      res.status(200).json(user.toPublicJSON());
    } catch (err) {
      next(err);
    }
  }
}

module.exports = UserController;
