'use strict';

/**
 * @fileoverview Health-check routes.
 */

const { Router } = require('express');
const HealthController = require('../controllers/HealthController');

/**
 * Mounts health-check routes onto an Express Router.
 *
 * @returns {import('express').Router}
 */
function createHealthRouter() {
  const router = Router();
  const controller = new HealthController();

  /** GET /api/health */
  router.get('/', controller.check.bind(controller));

  return router;
}

module.exports = createHealthRouter;
