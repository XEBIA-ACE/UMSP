# Spec: Add pytest-cov for Test Coverage Reporting

## Summary

This spec covers the addition of `pytest-cov` as a development dependency to the `user-management` Node.js service's test infrastructure to enable structured test coverage reporting. Based on the provided source context, the `user-management` service already uses Jest with coverage enabled via `jest --coverage` and a `coverageDirectory` configuration. The relevant Python testing tooling (`pytest-cov`) referenced in the task title does not match the actual stack (Node.js 20 / Jest 29). This spec therefore addresses coverage reporting improvements within the **existing Jest-based test setup** for the `user-management` service, as that is the only test infrastructure present in the provided context. Any Python/pytest scope is marked as TODO pending clarification.

---

## Motivation

- The `user-management` service already invokes `jest --coverage` in the `test` npm script, but there is no enforced coverage threshold, no designated reporter format beyond Jest's default, and no artifact output configuration suitable for CI consumption (e.g., lcov, Cobertura, or JSON summary).
- Without a structured coverage report format, CI pipelines cannot gate merges on coverage regressions or publish coverage badges/dashboards.
- Upgrade urgency: **medium** (per tech analysis).
- The existing `devDependencies` in `package.json` include `jest@^29.7.0` but no coverage reporter plugins or threshold enforcement, representing addressable tech debt.

---

## Current State

The following configuration elements in `user-management/package.json` are directly affected:

| Element | Current Value |
|---|---|
| `scripts.test` | `"jest --coverage"` |
| `devDependencies.jest` | `^29.7.0` |
| `jest.coverageDirectory` | `"coverage"` |
| `jest.collectCoverageFrom` | `["src/**/*.js", "!src/__tests__/**"]` |
| `jest.coverageReporters` | Not set (Jest default: `text`, `lcov`, `clover`) |
| `jest.coverageThreshold` | Not set |

Existing test files covered by `collectCoverageFrom`:
- `src/__tests__/health.test.js` — integration tests for `GET /api/health`
- `src/__tests__/loginUser.test.js` — unit tests for `LoginUser` use case
- `src/__tests__/registerUser.test.js` — unit tests for `RegisterUser` use case

Source modules included in coverage collection:
- `src/application/usecases/RecoverPassword.js`
- `src/application/usecases/RegisterUser.js`
- `src/adapters/outbound/persistence/InMemoryUserRepository.js`
- `src/adapters/outbound/auth/JwtAuthAdapter.js`
- `src/adapters/inbound/http/controllers/AuthController.js`
- `src/adapters/inbound/http/routes/authRoutes.js`

> **Note:** The `payment-service` uses Java 17 / Spring Boot 3.2 / JUnit 5 / Mockito and has no relationship to `pytest-cov` or Jest. It is out of scope for this task.

> **TODO:** Confirm whether the task title "Add pytest-cov" refers to a Python service not present in the provided source context. If a Python service exists elsewhere in the monorepo, a separate spec is required.

---

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| `jest.coverageReporters` (package.json) | Not configured (Jest defaults) | Explicitly set to include `text`, `lcov`, and `json-summary` reporters | N |
| `jest.coverageThreshold` (package.json) | Not configured (no enforcement) | Minimum thresholds defined for `branches`, `functions`, `lines`, and `statements` | N |
| `devDependencies` (package.json) | No additional coverage tooling | TODO: Confirm whether any supplementary Jest coverage plugin (e.g., `jest-junit` for CI XML output) is required | N |
| `scripts.test` (package.json) | `"jest --coverage"` | Unchanged — coverage flags already present; threshold enforcement is declarative via Jest config | N |
| CI pipeline (`ci.yml`) | TODO: Current coverage artifact upload behaviour unknown | Coverage artifact (lcov or json-summary) uploaded and optionally enforced as a merge gate | N |

---

## Compatibility & Breaking Changes

| Change | Impact | Migration Path |
|---|---|---|
| Adding `coverageThreshold` | Existing test runs that fall below the configured threshold will fail the `npm test` command | Review current coverage percentages before setting thresholds; set initial thresholds at or below the current measured baseline, then ratchet upward incrementally |
| Adding explicit `coverageReporters` | Replaces Jest's implicit defaults; `clover` format will no longer be generated unless explicitly listed | Any downstream tooling consuming `coverage/clover.xml` must be updated to use `lcov` or `json-summary` instead — TODO: confirm whether any such tooling exists |
| CI artifact path change | TODO: Unknown — depends on current CI configuration in `.github/workflows/ci.yml` | TODO |

---

## Acceptance Criteria

1. **Given** the `user-management` service has all dependencies installed, **when** `npm test` is executed, **then** a `coverage/` directory is produced containing at minimum an `lcov.info` file and a `coverage-summary.json` file.

2. **Given** the Jest configuration includes `coverageReporters` with `lcov` and `json-summary`, **when** `npm test` completes successfully, **then** the `coverage/lcov-report/index.html` file is present and readable in a browser without errors.

3. **Given** a `coverageThreshold` is configured for `lines` at the agreed minimum percentage, **when** `npm test` is run against the current test suite, **then** the command exits with code `0` (all thresholds met).

4. **Given** a source file under `src/**/*.js` (excluding `src/__tests__/**`) has a code path that is not exercised by any test, **when** `npm test` is run and the uncovered lines cause the `lines` threshold to be breached, **then** the command exits with a non-zero code and Jest prints a coverage threshold failure message.

5. **Given** the CI pipeline runs on a pull request, **when** `npm test` executes in CI, **then** the coverage report artifact is uploaded and accessible from the workflow run summary without manual steps.

6. **Given** the `collectCoverageFrom` pattern `["src/**/*.js", "!src/__tests__/**"]` is in effect, **when** coverage is collected, **then** all use-case files (`RecoverPassword.js`, `RegisterUser.js`, etc.) appear in the coverage report, and no test helper files from `src/__tests__/` appear.

7. **Given** the `coverageDirectory` is set to `"coverage"`, **when** `npm test` runs, **then** all coverage output files are written exclusively to the `coverage/` directory and no coverage files are written to the project root or `src/`.

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | Does "Add pytest-cov" refer to a Python service not present in the provided source context? If so, which service, and where is its source located? | TODO | TODO |
| 2 | What are the current measured coverage percentages (lines, branches, functions, statements) for the `user-management` service, to be used as the baseline for initial threshold values? | TODO | TODO |
| 3 | Is there an existing `.github/workflows/ci.yml` that uploads coverage artifacts, and if so, what format does it currently expect? | TODO | TODO |
| 4 | Is a machine-readable XML coverage format (e.g., Cobertura) required for integration with a code quality dashboard (e.g., SonarQube, Codecov, Coveralls)? | TODO | TODO |
| 5 | Should coverage thresholds be enforced as a hard merge gate in CI, or only reported as a warning? | TODO | TODO |
| 6 | Is `jest-junit` or a similar JUnit XML reporter needed for CI test result reporting in addition to coverage? | TODO | TODO |