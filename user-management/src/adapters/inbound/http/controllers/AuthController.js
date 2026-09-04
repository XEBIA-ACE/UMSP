'use strict';

/**
 * @fileoverview AuthController — handles authentication-related HTTP requests.
 */

class AuthController {
  /**
   * @param {Object} useCases
   * @param {import('../../../../application/usecases/RegisterUser')}     useCases.registerUser
   * @param {import('../../../../application/usecases/LoginUser')}        useCases.loginUser
   * @param {import('../../../../application/usecases/RecoverPassword')}  useCases.recoverPassword
   * @param {import('../../../../application/usecases/VerifyAccount')}    useCases.verifyAccount
   */
  constructor({ registerUser, loginUser, recoverPassword, verifyAccount }) {
    this.registerUser = registerUser;
    this.loginUser = loginUser;
    this.recoverPassword = recoverPassword;
    this.verifyAccount = verifyAccount;

    // Bind methods so they can be used directly as Express route handlers
    this.register = this.register.bind(this);
    this.login = this.login.bind(this);
    this.recoverPasswordHandler = this.recoverPasswordHandler.bind(this);
    this.verifyAccountHandler = this.verifyAccountHandler.bind(this);
  }

  /**
   * POST /api/auth/register
   * Registers a new user account.
   *
   * @param {import('express').Request}  req
   * @param {import('express').Response} res
   * @param {import('express').NextFunction} next
   * @returns {Promise<void>}
   */
  async register(req, res, next) {
    try {
      const { email, password } = req.body;
      const user = await this.registerUser.execute({ email, password });
      res.status(201).json({ message: 'Registration successful. Please verify your email.', user });
    } catch (err) {
      next(err);
    }
  }

  /**
   * POST /api/auth/login
   * Authenticates a user and returns a JWT.
   *
   * @param {import('express').Request}  req
   * @param {import('express').Response} res
   * @param {import('express').NextFunction} next
   * @returns {Promise<void>}
   */
  async login(req, res, next) {
    try {
      const { email, password } = req.body;
      const result = await this.loginUser.execute({ email, password });
      res.status(200).json(result);
    } catch (err) {
      next(err);
    }
  }

  /**
   * POST /api/auth/recover-password
   * Initiates the password-recovery flow.
   *
   * @param {import('express').Request}  req
   * @param {import('express').Response} res
   * @param {import('express').NextFunction} next
   * @returns {Promise<void>}
   */
  async recoverPasswordHandler(req, res, next) {
    try {
      const { email } = req.body;
      const result = await this.recoverPassword.execute({ email });
      res.status(200).json(result);
    } catch (err) {
      next(err);
    }
  }

  /**
   * GET /api/auth/verify/:token
   * Verifies a user account using the token from the verification email.
   *
   * @param {import('express').Request}  req
   * @param {import('express').Response} res
   * @param {import('express').NextFunction} next
   * @returns {Promise<void>}
   */
  async verifyAccountHandler(req, res, next) {
    try {
      const { token } = req.params;
      const result = await this.verifyAccount.execute({ token });
      res.status(200).json(result);
    } catch (err) {
      next(err);
    }
  }
}

module.exports = AuthController;
