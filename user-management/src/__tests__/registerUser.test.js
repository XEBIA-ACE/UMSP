'use strict';

/**
 * @fileoverview Unit tests for the RegisterUser use case.
 */

const RegisterUser = require('../application/usecases/RegisterUser');

// ── Helpers ──────────────────────────────────────────────────────────────────

/** @returns {import('../domain/ports/UserRepositoryPort')} */
function makeUserRepository(overrides = {}) {
  return {
    findByEmail: jest.fn().mockResolvedValue(null),
    save: jest.fn().mockImplementation(async (user) => user),
    findById: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    ...overrides,
  };
}

/** @returns {import('../domain/ports/EmailServicePort')} */
function makeEmailService(overrides = {}) {
  return {
    sendVerificationEmail: jest.fn().mockResolvedValue(undefined),
    sendPasswordResetEmail: jest.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

/** @returns {import('../domain/ports/AuthServicePort')} */
function makeAuthService(overrides = {}) {
  return {
    hashPassword: jest.fn().mockResolvedValue('hashed_password'),
    comparePassword: jest.fn(),
    generateToken: jest.fn().mockReturnValue('jwt_token'),
    verifyToken: jest.fn(),
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('RegisterUser use case', () => {
  it('should register a new user and return public JSON', async () => {
    const userRepository = makeUserRepository();
    const emailService = makeEmailService();
    const authService = makeAuthService();

    const useCase = new RegisterUser({ userRepository, emailService, authService });
    const result = await useCase.execute({ email: 'alice@example.com', password: 'secret123' });

    expect(result).toBeDefined();
    expect(result.email).toBe('alice@example.com');
    expect(result.passwordHash).toBeUndefined(); // sensitive field stripped
    expect(userRepository.save).toHaveBeenCalledTimes(1);
    expect(emailService.sendVerificationEmail).toHaveBeenCalledTimes(1);
  });

  it('should throw 409 when email already exists', async () => {
    const existingUser = { id: '1', email: 'alice@example.com' };
    const userRepository = makeUserRepository({
      findByEmail: jest.fn().mockResolvedValue(existingUser),
    });
    const emailService = makeEmailService();
    const authService = makeAuthService();

    const useCase = new RegisterUser({ userRepository, emailService, authService });

    await expect(
      useCase.execute({ email: 'alice@example.com', password: 'secret123' })
    ).rejects.toMatchObject({ status: 409 });
  });

  it('should throw 400 for invalid email format', async () => {
    const userRepository = makeUserRepository();
    const emailService = makeEmailService();
    const authService = makeAuthService();

    const useCase = new RegisterUser({ userRepository, emailService, authService });

    await expect(
      useCase.execute({ email: 'not-an-email', password: 'secret123' })
    ).rejects.toMatchObject({ status: 400 });
  });

  it('should throw 400 for password shorter than 8 characters', async () => {
    const userRepository = makeUserRepository();
    const emailService = makeEmailService();
    const authService = makeAuthService();

    const useCase = new RegisterUser({ userRepository, emailService, authService });

    await expect(
      useCase.execute({ email: 'alice@example.com', password: 'short' })
    ).rejects.toMatchObject({ status: 400 });
  });
});
