'use strict';

/**
 * @fileoverview User domain entity.
 */

/**
 * @typedef {Object} UserProps
 * @property {string}      id                 - UUID v4 identifier.
 * @property {string}      email              - User's email address.
 * @property {string}      passwordHash       - Bcrypt-hashed password.
 * @property {boolean}     [isVerified]       - Whether the account has been verified.
 * @property {string|null} [verificationToken]- Token sent in the verification email.
 * @property {string|null} [resetToken]       - Token sent in the password-reset email.
 * @property {Date|null}   [resetTokenExpiry] - Expiry date of the reset token.
 * @property {Date}        [createdAt]        - Record creation timestamp.
 * @property {Date}        [updatedAt]        - Record last-update timestamp.
 */

class User {
  /**
   * @param {UserProps} props
   */
  constructor(props) {
    this.id = props.id;
    this.email = props.email;
    this.passwordHash = props.passwordHash;
    this.isVerified = props.isVerified ?? false;
    this.verificationToken = props.verificationToken ?? null;
    this.resetToken = props.resetToken ?? null;
    this.resetTokenExpiry = props.resetTokenExpiry ?? null;
    this.createdAt = props.createdAt ?? new Date();
    this.updatedAt = props.updatedAt ?? new Date();
  }

  /**
   * Returns a plain object representation of the user with all sensitive
   * fields (passwordHash, verificationToken, resetToken, resetTokenExpiry) omitted.
   *
   * @returns {{ id: string, email: string, isVerified: boolean, createdAt: Date, updatedAt: Date }}
   */
  toPublicJSON() {
    return {
      id: this.id,
      email: this.email,
      isVerified: this.isVerified,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
    };
  }
}

module.exports = User;
