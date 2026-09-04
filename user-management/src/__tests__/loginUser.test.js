'use strict';

/**
 * @fileoverview Unit tests for the LoginUser use case.
 */

const LoginUser = require('../application/usecases/LoginUser');

function makeUserRepository(overrides = {}) {
  return {
    findByEmail: jest.fn(),
    findById: jest.fn(),
    save: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    ...overrides,
  };
}

function makeAuthService(overrides = {}) {
  return {
    hashPassword: jest.fn(),
    comparePassword: jest.fn().mockResolvedValue(true),
    generateToken: jest.fn().mockReturnValue('jwt_token'),
    verifyToken: jest.fn(),
    ...overrides,
  };
}

describe('LoginUser use case', () => {
  const verifiedUser = {
    id: 'user-1',
    email: 'alice@example.com',
    passwordHash: 'hashed',
    isVerified: true,
    toPublicJSON() {
      return { id: this.id, email: this.email };
    },
  };

  it('should return a token and public user on valid credentials', async () => {
    const userRepository = makeUserRepository({
      findByEmail: jest.fn().mockResolvedValue(verifiedUser),
    });
    const authService = makeAuthService();

    const useCase = new LoginUser({ userRepository, authService });
    const result = await useCase.execute({ email: 'alice@example.com', password: 'secret123' });

    expect(result.token).toBe('jwt_token');
    expect(result.user.email).toBe('alice@example.com');
    expect(result.user.passwordHash).toBeUndefined();
  });

  it('should throw 401 when user is not found', async () => {
    const userRepository = makeUserRepository({
      findByEmail: jest.fn().mockResolvedValue(null),
    });
    const authService = makeAuthService();

    const useCase = new LoginUser({ userRepository, authService });

    await expect(
      useCase.execute({ email: 'nobody@example.com', password: 'secret123' })
    ).rejects.toMatchObject({ status: 401 });
  });

  it('should throw 401 when password does not match', async () => {
    const userRepository = makeUserRepository({
      findByEmail: jest.fn().mockResolvedValue(verifiedUser),
    });
    const authService = makeAuthService({
      comparePassword: jest.fn().mockResolvedValue(false),
    });

    const useCase = new LoginUser({ userRepository, authService });

    await expect(
      useCase.execute({ email: 'alice@example.com', password: 'wrong' })
    ).rejects.toMatchObject({ status: 401 });
  });

  it('should throw 403 when account is not verified', async () => {
    const unverifiedUser = { ...verifiedUser, isVerified: false };
    const userRepository = makeUserRepository({
      findByEmail: jest.fn().mockResolvedValue(unverifiedUser),
    });
    const authService = makeAuthService();

    const useCase = new LoginUser({ userRepository, authService });

    await expect(
      useCase.execute({ email: 'alice@example.com', password: 'secret123' })
    ).rejects.toMatchObject({ status: 403 });
  });
});
