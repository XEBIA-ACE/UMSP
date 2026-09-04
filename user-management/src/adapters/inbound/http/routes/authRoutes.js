'use strict';

/**
 * @fileoverview Authentication routes.
 */

const { Router } = require('express');

/**
 * Mounts authentication routes onto an Express Router.
 *
 * @param {import('../controllers/AuthController')} authController
 * @returns {import('express').Router}
 */
function createAuthRouter(authController) {
  const router = Router();

  /** POST /api/auth/register */
  router.post('/register', authController.register);

  /** POST /api/auth/login */
  router.post('/login', authController.login);

  /** POST /api/auth/recover-password */
  router.post('/recover-password', authController.recoverPasswordHandler);

  /** GET /api/auth/verify/:token */
  router.get('/verify/:token', authController.verifyAccountHandler);

  return router;
}

module.exports = createAuthRouter;
