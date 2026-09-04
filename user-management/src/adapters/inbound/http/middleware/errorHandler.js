'use strict';

/**
 * @fileoverview Global Express error-handler middleware.
 * Must be registered AFTER all routes.
 */

/**
 * Centralised error handler that formats every thrown/passed error into a
 * consistent JSON response.
 *
 * @param {Error & { status?: number }} err
 * @param {import('express').Request}   _req
 * @param {import('express').Response}  res
 * @param {import('express').NextFunction} _next  - Required 4-arg signature for Express to recognise this as an error handler.
 * @returns {void}
 */
// eslint-disable-next-line no-unused-vars
function errorHandler(err, _req, res, _next) {
  const status = err.status || 500;

  if (status >= 500) {
    console.error('[errorHandler]', err);
  }

  res.status(status).json({
    error: err.message || 'Internal Server Error',
    status,
  });
}

module.exports = errorHandler;
