'use strict';

/**
 * @fileoverview User routes (protected).
 */

const { Router } = require('express');

/**
 * Mounts user routes onto an Express Router.
 * All routes are protected by the authMiddleware.
 *
 * @param {import('../controllers/UserController')}  userController
 * @param {import('express').RequestHandler}         authMiddleware
 * @returns {import('express').Router}
 */
function createUserRouter(userController, authMiddleware) {
  const router = Router();

  /** GET /api/users/profile — returns the authenticated user's public profile */
  router.get('/profile', authMiddleware, userController.getProfile);

  return router;
}

module.exports = createUserRouter;
