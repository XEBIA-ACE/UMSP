# Tasks: Replace unittest with pytest and add fixture-based DB isolation

> **Scope:** `user-management` service (Node.js 20 / Jest) — migrate test infrastructure from Jest's built-in `unittest`-style patterns to pytest-style fixture-based DB isolation, and introduce per-test repository reset fixtures. The Java/Spring Boot `payment-service` already uses JUnit 5 + Mockito and is **out of scope**.

---

## Prerequisites

- [ ] [XS] Verify Node.js 20 LTS is active in the local environment by running `node --version` and confirming output matches `v20.x.x`
- [ ] [XS] Verify Jest 29.7.0 is installed by running `npx jest --version` inside `user-management/` and confirming the version matches `package.json`
- [ ] [XS] Confirm `supertest` 6.3.3 is present in `user-management/node_modules` by inspecting `user-management/package-lock.json`
- [ ] [XS] Confirm write access to `user-management/src/__tests__/` and `user-management/package.json` in the working branch

---

## Phase 1 — Preparation

- [ ] [XS] Create a feature branch `feat/pytest-style-db-isolation` from `main` in the repository root
- [ ] [S] Capture the current test baseline by running `npm test -- --coverage` in `user-management/` and saving the full output (pass/fail counts, coverage percentages per file) to `user-management/test-baseline.txt`
- [ ] [XS] Audit existing test files under `user-management/src/__tests__/` and list every file that directly instantiates `InMemoryUserRepository` without resetting `_store` between tests, recording findings in a comment at the top of each affected file
- [ ] [XS] Add `jest-fixture` pattern documentation comment block to `user-management/src/__tests__/setup/` directory (create the directory if absent) describing the fixture contract: each fixture must return a fresh `InMemoryUserRepository` instance and expose a `reset()` helper

---

## Phase 2 — Core Upgrade

- [ ] [S] Create `user-management/src/__tests__/fixtures/repositoryFixtures.js` exporting a `makeUserRepository()` factory that returns a new `InMemoryUserRepository` instance with an empty `_store`, and a `resetRepository(repo)` helper that clears `repo._store` via `repo._store.clear()`
- [ ] [S] Create `user-management/src/__tests__/fixtures/usecaseFixtures.js` exporting factory functions `makeRegisterUser(overrides)`, `makeLoginUser(overrides)`, `makeRecoverPassword(overrides)`, and `makeVerifyAccount(overrides)` — each wiring a fresh `InMemoryUserRepository` from `repositoryFixtures.js` and stub implementations of `EmailServicePort` and `AuthServicePort` as Jest `jest.fn()` mocks
- [ ] [M] Refactor `user-management/src/__tests__/` test files for `RegisterUser.js` use case to replace any shared mutable repository state with `beforeEach(() => { repo = makeUserRepository(); })` calls using fixtures from `repositoryFixtures.js`, ensuring each test receives an isolated `_store`
- [ ] [M] Refactor `user-management/src/__tests__/` test files for `LoginUser.js` use case to replace shared state with `beforeEach` fixture resets using `makeUserRepository()` from `repositoryFixtures.js` and `makeLoginUser()` from `usecaseFixtures.js`
- [ ] [M] Refactor `user-management/src/__tests__/` test files for `RecoverPassword.js` use case to replace shared state with `beforeEach` fixture resets using `makeUserRepository()` and `makeRecoverPassword()` from `usecaseFixtures.js`
- [ ] [M] Refactor `user-management/src/__tests__/` test files for `VerifyAccount.js` use case to replace shared state with `beforeEach` fixture resets using `makeUserRepository()` and `makeVerifyAccount()` from `usecaseFixtures.js`
- [ ] [S] Refactor `user-management/src/__tests__/` test files covering `InMemoryUserRepository.js` directly to use `beforeEach(() => { repo = makeUserRepository(); })` from `repositoryFixtures.js`, removing any module-level `let repo = new InMemoryUserRepository()` declarations
- [ ] [S] Update `user-management/src/__tests__/fixtures/usecaseFixtures.js` to expose a `makeNodemailerEmailAdapter(config)` stub factory returning a `jest.fn()`-backed object satisfying `EmailServicePort` interface (`sendVerificationEmail`, `sendPasswordResetEmail`), so integration-style tests can inject it without real SMTP
- [ ] [XS] Add a `globalSetup` entry in the `jest` block of `user-management/package.json` pointing to `src/__tests__/setup/globalSetup.js` (create the file with an empty async export) to reserve the hook for future DB teardown without breaking existing runs

---

## Phase 3 — Testing & Validation

- [ ] [S] Run `npm test -- --coverage` in `user-management/` and verify all previously passing tests still pass; diff output against `user-management/test-baseline.txt` and confirm zero regressions
- [ ] [XS] Verify that running a single test file in isolation (e.g. `npx jest src/__tests__/usecases/RegisterUser.test.js --runInBand`) produces the same result as running the full suite, confirming no cross-test state leakage via `InMemoryUserRepository._store`
- [ ] [S] Add at least one explicit isolation-proof test in `user-management/src/__tests__/fixtures/repositoryFixtures.test.js` that creates two independent repositories via `makeUserRepository()`, saves a user to one, and asserts the other's `_store` remains empty
- [ ] [XS] Confirm coverage for `user-management/src/adapters/outbound/persistence/InMemoryUserRepository.js` remains at or above the baseline percentage captured in `test-baseline.txt`

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [XS] Update `.github/workflows/ci.yml` `test` step for the `user-management` service to pass `--runInBand` flag to `jest` (i.e. `npm test -- --runInBand --coverage`) to prevent parallel worker interference with the in-memory store during CI runs
- [ ] [XS] Verify the `coverageDirectory` key in the `jest` block of `user-management/package.json` still points to `coverage` and that `collectCoverageFrom` includes `src/**/*.js` but excludes `src/__tests__/**` and the new `src/__tests__/fixtures/**` glob

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Update `user-management/README.md` (or the root `README.md` under the `user-management` quick-start section) to document the fixture pattern: add a "Testing" subsection explaining that `src/__tests__/fixtures/repositoryFixtures.js` and `usecaseFixtures.js` must be used for all new tests requiring DB isolation
- [ ] [XS] Add a `CHANGELOG.md` entry in `user-management/` under an `[Unreleased]` heading noting: "Replaced ad-hoc shared-state test setup with fixture-based DB isolation using `repositoryFixtures.js` and `usecaseFixtures.js`; all use-case tests now receive a fresh `InMemoryUserRepository` per test via `beforeEach`"
- [ ] [XS] Delete `user-management/test-baseline.txt` from the working branch before opening the pull request (it was a local scratch file only)