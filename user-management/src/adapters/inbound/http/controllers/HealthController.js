'use strict';

/**
 * @fileoverview HealthController — liveness / readiness probe endpoint.
 */

class HealthController {
  /**
   * Returns a simple health-check payload.
   *
   * @param {import('express').Request}  _req
   * @param {import('express').Response} res
   * @returns {void}
   */
  check(_req, res) {
    res.status(200).json({
      status: 'ok',
      service: 'user-management',
      timestamp: new Date().toISOString(),
    });
  }
}

module.exports = HealthController;
