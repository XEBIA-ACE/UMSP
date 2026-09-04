# Spec: Replace unittest with pytest and Add Fixture-Based DB Isolation

## Summary

This spec covers the migration of the `user-management` service's test suite from its current Jest-based setup to pytest, and the introduction of fixture-based database isolation for tests that interact with the in-memory user repository (`InMemoryUserRepository`). The expected outcome is a test suite that uses pytest conventions, eliminates shared mutable state between tests via scoped fixtures, and produces equivalent or better coverage of the existing use cases (`RegisterUser`, `LoginUser`, `RecoverPassword`, `VerifyAccount`) and adapters.

> **Note:** The source code provided is a Node.js/JavaScript codebase using Jest, not a Python codebase using unittest. The task description references "unittest" and "pytest," which are Python testing frameworks. This spec is written against the stated modernization goal as literally described. Where the actual technology stack conflicts with the goal, those gaps are called out in Open Questions.

---

## Motivation

- **Tech debt:** The current test configuration in `package.json` uses Jest 29.7.0 with a custom `testMatch` glob (`**/src/__tests__/**/*.test.js`). The modernization goal targets replacement with pytest and fixture-based isolation, indicating a planned language or toolchain migration.
- **DB isolation gap:** The `InMemoryUserRepository` uses a shared `Map` (`this._store`) instance. Without per-test fixture teardown, tests that mutate the store (e.g., `RegisterUser`, `VerifyAccount`) can leak state into subsequent tests, causing non-deterministic failures.
- **Upgrade urgency:** Medium — no CVEs or EOL dates are cited in the tech analysis, but the lack of test isolation is an active source of flaky tests and maintenance burden.
- **Compliance/quality:** Fixture-based isolation is a prerequisite for reliable CI gating on the GitHub Actions pipeline described in `AGENTS.md`.

---

## Current State

### Test Runner & Configuration

| Key | Current Value |
|---|---|
| Test framework | Jest 29.7.0 (devDependency in `user-management/package.json`) |
| Test runner script | `jest --coverage` (npm script `test`) |
| Test match pattern | `**/src/__tests__/**/*.test.js` |
| Coverage output | `coverage/` directory |
| Coverage source | `src/**/*.js` excluding `src/__tests__/**` |
| Integration test helper | `supertest` 6.3.3 |

### Repository Under Test

- **`InMemoryUserRepository`** (`user-management/src/adapters/outbound/persistence/InMemoryUserRepository.js`): Backed by `this._store = new Map()`. Instance is constructed once and shared across all tests unless explicitly reset. Exposes: `findById`, `findByEmail`, `save`, `update`, `delete`, `findByVerificationToken`, `findByResetToken`.

### Use Cases Under Test

- `RegisterUser` — depends on `userRepository`, `emailService`, `authService`
- `LoginUser` — depends on `userRepository`, `authService`
- `RecoverPassword` — depends on `userRepository`, `emailService`
- `VerifyAccount` — depends on `userRepository`

### Outbound Adapters Under Test

- `NodemailerEmailAdapter` — depends on SMTP config; currently stubbed/mocked in tests
- `InMemoryUserRepository` — used directly in integration-style tests

### Key Behaviours Affected

- Each use case constructs its own dependencies via constructor injection (`{ userRepository, authService, emailService }`), making them straightforward to test with injected fakes or mocks.
- `InMemoryUserRepository.update()` throws an `Error` with `status = 404` if the user does not exist.
- `InMemoryUserRepository.delete()` throws an `Error` with `status = 404` if the user does not exist.
- `RecoverPassword` silently succeeds (anti-enumeration) when the email is not found.
- `VerifyAccount` delegates token lookup to `findByVerificationToken` when available on the repository.

---

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| Test framework | Jest 29.7.0 | pytest (version TODO) | Y — all test files must be rewritten |
| Test file location | `user-management/src/__tests__/**/*.test.js` | TODO — pytest discovery convention (e.g., `tests/` directory with `test_*.py` files) | Y — directory structure changes |
| Test runner npm script | `jest --coverage` | TODO — pytest invocation command | Y — `npm test` script changes or is replaced |
| Coverage tooling | Jest built-in coverage | pytest-cov (version TODO) | Y |
| Integration HTTP helper | `supertest` 6.3.3 | TODO — Python HTTP test client (e.g., `httpx`, `requests`) | Y |
| `InMemoryUserRepository` isolation | Shared `Map` instance across tests; no teardown | Per-test fixture that provides a fresh repository instance with empty `_store` | N — production code unchanged |
| Mock/stub mechanism | Jest `jest.fn()` / manual stubs | pytest fixtures returning mock objects (e.g., `unittest.mock.MagicMock` or `pytest-mock`) | Y — mock syntax changes |
| `RegisterUser` test setup | `beforeEach` / `afterEach` Jest hooks | pytest fixture with function scope | Y |
| `LoginUser` test setup | `beforeEach` / `afterEach` Jest hooks | pytest fixture with function scope | Y |
| `RecoverPassword` test setup | `beforeEach` / `afterEach` Jest hooks | pytest fixture with function scope | Y |
| `VerifyAccount` test setup | `beforeEach` / `afterEach` Jest hooks | pytest fixture with function scope | Y |

---

## Compatibility & Breaking Changes

| Breaking Change | Migration Path for Callers |
|---|---|
| Jest removed as test runner | Remove `jest` and `supertest` from `devDependencies` in `package.json`; update `scripts.test` to invoke pytest. TODO — confirm whether a `package.json` wrapper or a standalone Python test runner config is used. |
| Test file format changes from `.test.js` to `.py` | All existing test files in `src/__tests__/` must be rewritten as Python test modules. The Jest `testMatch` glob in `package.json` must be removed or replaced. |
| `jest.fn()` mocks replaced | All mock collaborators (`emailService`, `authService`) must be re-expressed as pytest fixtures using `unittest.mock.MagicMock` or `pytest-mock`'s `mocker` fixture. |
| `beforeEach` / `afterEach` hooks replaced | Converted to pytest fixtures with `function` scope. Each test function receives a fresh `InMemoryUserRepository`-equivalent instance via fixture injection. |
| Coverage report format changes | CI pipeline (`ci.yml`) must be updated to parse pytest-cov output instead of Jest coverage JSON. TODO — confirm coverage threshold requirements. |
| `supertest` HTTP integration tests replaced | TODO — identify Python equivalent for HTTP-level integration tests against the Express app, or confirm these tests are out of scope for this migration. |
| `nodemon` dev dependency unaffected | `nodemon` is a runtime dev tool, not a test tool; no change required. |

---

## Acceptance Criteria

1. **Given** the test suite is executed, **when** the pytest runner is invoked, **then** all tests that previously passed under Jest pass under pytest with no failures.

2. **Given** a test for `RegisterUser.execute()`, **when** the test runs, **then** it receives a fresh, empty repository instance via a function-scoped pytest fixture, and no state from a prior test is present in the repository.

3. **Given** two tests that both call `RegisterUser.execute()` with the same email address, **when** they run in sequence, **then** neither test fails due to a "Email is already registered" conflict caused by state leakage from the other test.

4. **Given** a test for `LoginUser.execute()` that requires a pre-existing verified user, **when** the fixture sets up that user in the repository, **then** the test can authenticate successfully, and a subsequent unrelated test does not see that user in its repository instance.

5. **Given** a test for `VerifyAccount.execute()` that calls `findByVerificationToken`, **when** the test runs, **then** the repository fixture provides an isolated store so that tokens created in other tests do not interfere.

6. **Given** a test for `RecoverPassword.execute()` with an unregistered email, **when** `execute` is called, **then** the test asserts the returned message equals `'Password reset email sent'` without any exception being raised, verifiable by pytest's assertion output.

7. **Given** the full test suite runs in CI, **when** the GitHub Actions `ci.yml` workflow executes, **then** the pipeline exits with code 0 only if all pytest tests pass and coverage meets the defined threshold (TODO — threshold value).

8. **Given** a mock `emailService` collaborator is injected into `RegisterUser`, **when** `execute` is called with a valid new user, **then** the test asserts that `sendVerificationEmail` was called exactly once with the correct email address, using pytest's mock assertion API.

9. **Given** a mock `emailService` that raises an exception during `sendVerificationEmail`, **when** `RegisterUser.execute()` is called, **then** the test asserts that no exception propagates to the caller (non-blocking failure behaviour is preserved).

10. **Given** the pytest configuration is committed, **when** a developer runs the test command locally, **then** pytest discovers and executes all test modules without requiring manual path configuration.

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | Is this migration targeting a rewrite of the Node.js service in Python, or is pytest being run against the JavaScript codebase via a bridge (e.g., `pytest-js`)? The source code is entirely JavaScript/Node.js, which is incompatible with native pytest. | TODO | TODO |
| 2 | If the service remains in Node.js, should "pytest" be interpreted as a metaphor for a Jest upgrade with fixture-style `beforeEach` isolation, or is a full language migration planned? | TODO | TODO |
| 3 | What is the target pytest version? | TODO | TODO |
| 4 | What Python version is required if a language migration is in scope? | TODO | TODO |
| 5 | What is the minimum acceptable code coverage threshold for the migrated test suite? | TODO | TODO |
| 6 | Are HTTP-level integration tests (currently using `supertest`) in scope for this migration, or only unit tests for use cases and repository adapters? | TODO | TODO |
| 7 | Should the `InMemoryUserRepository` be ported to Python as a test double, or will a real database (e.g., PostgreSQL 15 via Testcontainers, as referenced in `AGENTS.md`) be used for DB isolation fixtures? | TODO | TODO |
| 8 | Does the CI pipeline (`ci.yml`) need to be updated to install Python and pytest, and if so, what Python environment management tool is used (e.g., `pip`, `poetry`, `uv`)? | TODO | TODO |
| 9 | Are there existing pytest fixtures or a `conftest.py` in any part of the monorepo that this work should align with? | TODO | TODO |
| 10 | What is the migration strategy for the `PaymentControllerTest` and `PaymentApplicationServiceTest` in the Java `payment-service`? Those tests use JUnit 5 + Mockito, not unittest — are they in scope? | TODO | TODO |