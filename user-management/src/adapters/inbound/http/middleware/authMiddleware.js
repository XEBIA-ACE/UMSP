'use strict';

/**
 * @fileoverview Authentication middleware factory.
 * Validates the Bearer JWT in the Authorization header and attaches the
 * decoded payload to req.user.
 */

/**
 * Creates an Express middleware that protects routes with JWT authentication.
 *
 * @param {import('../../../../domain/ports/AuthServicePort')} authService
 * @returns {import('express').RequestHandler}
 */
function createAuthMiddleware(authService) {
  /**
   * @param {import('express').Request}      req
   * @param {import('express').Response}     _res
   * @param {import('express').NextFunction}  next
   * @returns {void}
   */
  return function authMiddleware(req, _res, next) {
    try {
      const authHeader = req.headers['authorization'] || req.headers['Authorization'];

      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        const err = new Error('Authorization header missing or malformed');
        err.status = 401;
        return next(err);
      }

      const token = authHeader.slice(7); // Remove "Bearer " prefix

      const decoded = authService.verifyToken(token);
      req.user = decoded; // Attach decoded payload (contains sub, email, iat, exp)

      return next();
    } catch (err) {
      err.status = 401;
      err.message = 'Invalid or expired token';
      return next(err);
    }
  };
}

module.exports = createAuthMiddleware;
