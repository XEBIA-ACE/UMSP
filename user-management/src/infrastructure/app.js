'use strict';

/**
 * @fileoverview Express application factory.
 * Wires together all adapters, use-cases, and routes into a single app instance.
 */

const express = require('express');
const env = require('./config/env');

// ── Outbound adapters ──────────────────────────────────────────────────────────
const InMemoryUserRepository = require('../adapters/outbound/persistence/InMemoryUserRepository');
const NodemailerEmailAdapter = require('../adapters/outbound/email/NodemailerEmailAdapter');
const JwtAuthAdapter = require('../adapters/outbound/auth/JwtAuthAdapter');

// ── Use cases ──────────────────────────────────────────────────────────────────
const RegisterUser = require('../application/usecases/RegisterUser');
const LoginUser = require('../application/usecases/LoginUser');
const RecoverPassword = require('../application/usecases/RecoverPassword');
const VerifyAccount = require('../application/usecases/VerifyAccount');

// ── Inbound controllers ────────────────────────────────────────────────────────
const AuthController = require('../adapters/inbound/http/controllers/AuthController');
const UserController = require('../adapters/inbound/http/controllers/UserController');

// ── Middleware ─────────────────────────────────────────────────────────────────
const errorHandler = require('../adapters/inbound/http/middleware/errorHandler');
const createAuthMiddleware = require('../adapters/inbound/http/middleware/authMiddleware');

// ── Routes ─────────────────────────────────────────────────────────────────────
const healthRoutes = require('../adapters/inbound/http/routes/healthRoutes');
const authRoutes = require('../adapters/inbound/http/routes/authRoutes');
const userRoutes = require('../adapters/inbound/http/routes/userRoutes');

/**
 * Creates and configures the Express application.
 *
 * @returns {import('express').Application} Configured Express app.
 */
function createApp() {
  // ── Instantiate adapters ─────────────────────────────────────────────────────
  const userRepository = new InMemoryUserRepository();

  const emailService = new NodemailerEmailAdapter({
    host: env.SMTP_HOST,
    port: env.SMTP_PORT,
    user: env.SMTP_USER,
    pass: env.SMTP_PASS,
    from: env.EMAIL_FROM,
  });

  const authService = new JwtAuthAdapter({
    secret: env.JWT_SECRET,
    expiresIn: env.JWT_EXPIRES_IN,
  });

  // ── Instantiate use cases ────────────────────────────────────────────────────
  const registerUser = new RegisterUser({ userRepository, emailService, authService });
  const loginUser = new LoginUser({ userRepository, authService });
  const recoverPassword = new RecoverPassword({ userRepository, emailService });
  const verifyAccount = new VerifyAccount({ userRepository });

  // ── Instantiate controllers ──────────────────────────────────────────────────
  const authController = new AuthController({
    registerUser,
    loginUser,
    recoverPassword,
    verifyAccount,
  });
  const userController = new UserController({ userRepository });

  // ── Auth middleware (closure over authService) ───────────────────────────────
  const authMiddleware = createAuthMiddleware(authService);

  // ── Build Express app ────────────────────────────────────────────────────────
  const app = express();

  app.use(express.json());

  // Mount routes
  app.use('/api/health', healthRoutes());
  app.use('/api/auth', authRoutes(authController));
  app.use('/api/users', userRoutes(userController, authMiddleware));

  // Global error handler (must be last)
  app.use(errorHandler);

  return app;
}

module.exports = { createApp };
