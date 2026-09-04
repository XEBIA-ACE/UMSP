# Plan: Replace unittest with pytest and Add Fixture-Based DB Isolation

## Overview

**Migration strategy: Feature-flag gated / strangler-fig within the test layer**

The modernization target is the **`user-management` Node.js service** test suite. The source code confirms the service uses **Jest** (not Python's `unittest`), and the existing test infrastructure is defined in `user-management/package.json` with `jest@^29.7.0` and `supertest@^6.3.3`. The `payment-service` (Java/Spring Boot) already uses JUnit 5 with Mockito — no changes are needed there.

**Interpretation of the task:** "Replace unittest with pytest and add fixture-based DB isolation" maps onto this JavaScript codebase as: **replace ad-hoc Jest test setup/teardown patterns with structured Jest fixture functions (analogous to pytest fixtures) and add per-test DB isolation using the `InMemoryUserRepository` reset pattern.** No Python runtime exists in this repository; pytest is not applicable. The plan addresses the spirit of the goal within the actual stack.

**Justification:** The risk score is medium and the effort is moderate. A strangler-fig approach within the test layer is appropriate — new fixture-based helpers are introduced alongside existing tests, existing tests are migrated file-by-file, and the old patterns are removed only after the new ones are verified green in CI. This avoids a big-bang rewrite that could break CI coverage gates.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 | Audit existing test files under `user-management/src/__tests__/`; document all `beforeEach`/`afterEach` patterns and direct repository instantiation | None | 0.5 person-days |
| 2 | Create shared fixture module (`src/__tests__/fixtures/db.js`) providing factory functions for a fresh `InMemoryUserRepository` and seeded user objects; create `src/__tests__/fixtures/app.js` for Express app factory with injected test dependencies | Phase 1 complete | 1 person-day |
| 3 | Migrate unit tests (use-case layer: `RegisterUser`, `LoginUser`, `RecoverPassword`, `VerifyAccount`) to use fixtures; enforce per-test isolation via fixture reset | Phase 2 complete | 1 person-day |
| 4 | Migrate integration/adapter tests (HTTP layer via `supertest`) to use fixture-based app factory; add DB state assertions per test | Phase 3 complete | 1 person-day |
| 5 | Add Jest `globalSetup`/`globalTeardown` stubs and enforce coverage gates in CI; remove legacy ad-hoc setup patterns | Phase 4 complete | 0.5 person-days |

**Total estimated effort: ~4 person-days**

---

## Component Changes

### `user-management/src/__tests__/fixtures/db.js` *(new file)*

- Exports a `createFreshRepository()` factory that returns a new `InMemoryUserRepository` instance for each test, guaranteeing zero shared state between tests.
- Exports a `seedUser(repo, overrides)` helper that creates and persists a default `User` entity, accepting field overrides — analogous to a pytest fixture with parametrize.
- Exports a `seedVerifiedUser(repo, overrides)` convenience helper.

**Affected classes:** `InMemoryUserRepository` (`user-management/src/adapters/outbound/persistence/InMemoryUserRepository.js`) — consumed read-only; no structural changes to the class itself.

### `user-management/src/__tests__/fixtures/app.js` *(new file)*

- Exports a `createTestApp({ userRepository, emailService, authService })` factory that wires the Express application with injected test doubles, replacing any environment-level singleton.
- The `emailService` default will be a Jest mock (`jest.fn()`) satisfying `EmailServicePort`.
- The `authService` default will be a lightweight stub satisfying `AuthServicePort`.

**Affected files:** `user-management/index.js` or the Express app factory — the app must accept dependency injection rather than constructing its own adapters. If the current entry point hard-wires adapters, a thin factory wrapper must be extracted.

### `user-management/src/__tests__/usecases/RegisterUser.test.js` *(modified)*

- Replace direct `new InMemoryUserRepository()` calls in each test body with `createFreshRepository()` from the fixture module.
- Replace inline user construction with `seedUser()`.
- Each `describe` block gets a `let repo; beforeEach(() => { repo = createFreshRepository(); })` pattern.

**Affected class:** `RegisterUser` (`user-management/src/application/usecases/RegisterUser.js`) — no changes to production code.

### `user-management/src/__tests__/usecases/LoginUser.test.js` *(modified)*

- Same fixture migration as `RegisterUser.test.js`.
- `seedVerifiedUser()` replaces manual user construction + `isVerified: true` inline setup.

**Affected class:** `LoginUser` (`user-management/src/application/usecases/LoginUser.js`) — no changes to production code.

### `user-management/src/__tests__/usecases/RecoverPassword.test.js` *(modified)*

- Replace inline repository and email mock setup with `createFreshRepository()` and the shared email mock fixture.

**Affected class:** `RecoverPassword` (`user-management/src/application/usecases/RecoverPassword.js`) — no changes to production code.

### `user-management/src/__tests__/usecases/VerifyAccount.test.js` *(modified)*

- Replace inline token setup with `seedUser(repo, { verificationToken: 'test-token', isVerified: false })`.

**Affected class:** `VerifyAccount` (`user-management/src/application/usecases/VerifyAccount.js`) — no changes to production code.

### `user-management/src/__tests__/integration/*.test.js` *(modified)*

- Replace `supertest(app)` calls that rely on a singleton app with `supertest(createTestApp({ userRepository: createFreshRepository() }))`.
- Each test or `beforeEach` creates a fresh repository, ensuring HTTP-layer tests do not share DB state.

### `user-management/package.json` *(modified)*

- Add `jest.setupFilesAfterFramework` or `jest.globalSetup` entry pointing to `src/__tests__/setup.js` if global teardown hooks are needed.
- No version changes required — `jest@^29.7.0` fully supports all fixture patterns used.

---

## Dependency Upgrade Plan

| Dependency | Current Version | Target Version | Breaking Changes | Migration Notes |
|---|---|---|---|---|
| `jest` | `^29.7.0` | `^29.7.0` (no change) | None | Already at target version; fixture patterns are native Jest |
| `supertest` | `^6.3.3` | `^6.3.3` (no change) | None | No upgrade needed; used as-is in integration fixtures |
| `nodemon` | `^3.0.2` | `^3.0.2` (no change) | None | Dev-only; unaffected |

> **Note:** The tech analysis does not specify target versions beyond what is in `package.json`. All version numbers above are sourced exclusively from `user-management/package.json`. No new runtime dependencies are required for this task.

---

## Infrastructure Changes

**CI/CD (`github/workflows/ci.yml`):**
- Add a coverage gate step for the `user-management` service: fail the build if line coverage drops below the threshold established in Phase 5 (TODO: confirm current baseline coverage percentage from CI run before setting gate).
- The `npm test` script (`jest --coverage`) is unchanged; the fixture migration does not alter the test runner invocation.

**Docker:** N/A — not applicable to this task. Test fixtures run in-process; no container changes are needed.

**Kubernetes manifests:** N/A — not applicable to this task.

**IaC:** N/A — not applicable to this task.

**TODO:** Confirm whether `.github/workflows/ci.yml` already runs `npm test` for `user-management` and whether a coverage threshold is enforced. The workflow file is referenced in `AGENTS.md` but its contents are not provided in context.

---

## Rollback Strategy

### Phase 1 (Audit)
- No code changes; fully reversible by discarding the audit document.

### Phase 2 (Fixture module creation)
- Delete `src/__tests__/fixtures/db.js` and `src/__tests__/fixtures/app.js`.
- No existing tests are modified in this phase; CI remains green.

### Phase 3 (Unit test migration)
- Each test file is migrated independently. If a migrated file causes regressions, revert that single file via `git checkout -- src/__tests__/usecases/<file>.test.js`.
- The fixture module remains in place for subsequent re-migration.

### Phase 4 (Integration test migration)
- Same per-file revert strategy: `git checkout -- src/__tests__/integration/<file>.test.js`.
- The `createTestApp` fixture can be reverted independently of the repository fixture.

### Phase 5 (CI gate enforcement)
- If the coverage gate causes unexpected failures, lower the threshold or temporarily comment out the gate step in `ci.yml` while investigating.
- Remove the `jest.globalSetup` entry from `package.json` if the teardown hook causes issues.

**All phases are independently reversible via `git revert` or per-file `git checkout` without affecting production code.**

---

## Testing Strategy

### Test Pyramid

**Unit tests** (`src/__tests__/usecases/`)
- Tool: Jest `^29.7.0`
- Scope: Each use case (`RegisterUser`, `LoginUser`, `RecoverPassword`, `VerifyAccount`) tested in isolation with a fresh `InMemoryUserRepository` per test.
- Coverage target: **≥ 90% line coverage** on `src/application/usecases/**`.
- Fixture pattern: `createFreshRepository()` in `beforeEach`; `seedUser()` / `seedVerifiedUser()` for precondition setup.
- CI gate: `jest --coverage --coverageThreshold='{"./src/application/usecases/":{"lines":90}}'`

**Integration tests** (`src/__tests__/integration/`)
- Tool: Jest `^29.7.0` + Supertest `^6.3.3`
- Scope: HTTP adapter layer — routes, controllers, middleware — tested against a real Express app wired with `InMemoryUserRepository` (no external services).
- Coverage target: **≥ 80% line coverage** on `src/adapters/**`.
- Fixture pattern: `createTestApp({ userRepository: createFreshRepository() })` per test or `beforeEach`.
- DB isolation assertion: After each mutating HTTP call, assert repository state directly via `repo.findByEmail()` or `repo.findById()` to confirm persistence side-effects.

**Regression tests**
- The full `npm test` run (all Jest suites) acts as the regression gate on every PR.
- `jest --runInBand` may be used in CI to avoid flakiness from parallel in-memory state if the app factory is not perfectly isolated (TODO: verify after Phase 4).

**Performance tests**
- N/A for this task — fixture-based DB isolation uses `InMemoryUserRepository` which has no I/O latency. No performance benchmarks are required.

**CI gates summary:**

| Gate | Trigger | Failure action |
|---|---|---|
| `npm test -- --coverage` | Every PR and push to main | Block merge |
| Line coverage ≥ 90% (usecases) | Every PR | Block merge |
| Line coverage ≥ 80% (adapters) | Every PR | Block merge |
| No skipped tests (`--ci` flag) | Every PR | Block merge |

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| Test audit complete; all existing patterns documented | Phase 1 | Day 1 | TODO |
| Fixture modules (`db.js`, `app.js`) merged and passing | Phase 2 | Day 2 | TODO |
| All use-case unit tests migrated to fixtures | Phase 3 | Day 3 | TODO |
| All integration tests migrated; per-test DB isolation verified | Phase 4 | Day 4 | TODO |
| CI coverage gates active; legacy setup patterns removed | Phase 5 | Day 4 (afternoon) | TODO |

> Effort derived from the moderate upgrade option estimate (~4 person-days total). All owner fields are TODO pending team assignment.