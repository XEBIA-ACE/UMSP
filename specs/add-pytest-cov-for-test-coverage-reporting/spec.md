# Spec: Add pytest-cov for Test Coverage Reporting

## Summary

This spec covers the addition of `pytest-cov` as a development dependency to the `user-management` Node.js service's test infrastructure to enable structured test coverage reporting. Based on the provided source context, the `user-management` service already uses Jest with coverage enabled via `jest --coverage` and a `coverageDirectory` configuration. The relevant Python testing tooling (`pytest-cov`) referenced in the task title does not match the actual stack (Node.js 20 / Jest 29.7.0). This spec therefore addresses coverage reporting improvements within the **existing Jest-based test setup** for the `user-management` service, as that is the only test infrastructure present in the provided context. Any Python/pytest scope is marked as TODO pending clarification.

---

## Motivation

- The `user-management` service already invokes `jest --coverage` in the `test` npm script, but the current Jest configuration does not specify coverage reporters, coverage thresholds, or output formats beyond a bare `coverageDirectory` setting.
- Without explicit reporter configuration, coverage output is limited to the default terminal summary and is not consumable by CI tooling (e.g., GitHub Actions coverage annotations, Codecov, or SonarQube).
- Upgrade urgency: **medium** — no EOL or CVE driver; the gap is a tech-debt item preventing visibility into untested code paths across use cases such as `RecoverPassword`, `RegisterUser`, `LoginUser`, and their associated adapters.
- The `collectCoverageFrom` field in `package.json` already scopes collection to `src/**/*.js` excluding `src/__tests__/**`, which is correct but incomplete without threshold enforcement.

---

## Current State

The following configuration elements in `user-management/package.json` govern the existing test and coverage behaviour:

| Config Key | Current Value | Effect |
|---|---|---|
| `scripts.test` | `"jest --coverage"` | Runs all tests and collects coverage |
| `jest.testEnvironment` | `"node"` | Node.js test environment |
| `jest.testMatch` | `["**/src/__tests__/**/*.test.js"]` | Matches test files under `src/__tests__/` |
| `jest.coverageDirectory` | `"coverage"` | Output directory for coverage artefacts |
| `jest.collectCoverageFrom` | `["src/**/*.js", "!src/__tests__/**"]` | Source files included in coverage collection |

**Existing test files covered by collection:**
- `src/__tests__/health.test.js` — integration tests for `GET /api/health`
- `src/__tests__/loginUser.test.js` — unit tests for `LoginUser` use case
- `src/__tests__/registerUser.test.js` — unit tests for `RegisterUser` use case

**Notable source files currently included in collection but lacking dedicated tests:**
- `src/application/usecases/RecoverPassword.js`
- `src/adapters/inbound/http/controllers/AuthController.js`
- `src/adapters/inbound/http/routes/authRoutes.js`
- `src/adapters/outbound/auth/JwtAuthAdapter.js`
- `src/adapters/outbound/persistence/InMemoryUserRepository.js`

**devDependencies (current):**

| Package | Version |
|---|---|
| `jest` | `^29.7.0` |
| `supertest` | `^6.3.3` |
| `nodemon` | `^3.0.2` |

There is no `coverageReporters`, `coverageThreshold`, or `coverageProvider` key present in the Jest configuration block.

---

## Proposed Changes

> **Note:** The task title references `pytest-cov`, a Python tool. The codebase is Node.js/Jest. This spec addresses coverage reporting configuration within Jest. If a Python service exists outside the provided context and requires `pytest-cov`, that scope is marked TODO.

### user-management — Jest coverage configuration

| Component | Before | After | Breaking? |
|---|---|---|---|
| `jest.coverageReporters` | Not set (defaults to `["text", "lcov"]`) | Explicitly set to `["text", "lcov", "html", "json-summary"]` | N |
| `jest.coverageThreshold` | Not set (no enforcement) | Global thresholds added for lines, functions, branches, statements | N |
| `jest.coverageProvider` | Not set (defaults to `"babel"`) | Explicitly set to `"v8"` for accurate native coverage | N |
| `scripts.test` | `"jest --coverage"` | Unchanged — `--coverage` flag already present | N |
| `scripts.test:ci` | Not present | Added as a dedicated CI script variant (e.g., with `--ci` flag) | N |

### Python/pytest-cov scope

| Component | Before | After | Breaking? |
|---|---|---|---|
| Python test runner | TODO — no Python service identified in provided context | TODO | TODO |
| `pytest-cov` dependency | TODO | TODO | TODO |

---

## Compatibility & Breaking Changes

| Change | Impact | Migration Path |
|---|---|---|
| Adding `coverageThreshold` | Tests will fail in CI if coverage drops below the configured threshold | Thresholds must be set at or below current measured coverage levels on first introduction; teams must raise thresholds incrementally |
| Switching `coverageProvider` to `"v8"` | Coverage numbers may differ slightly from the previous Babel-instrumented output | Review coverage report after first run; adjust thresholds if needed; no source changes required |
| Adding `"json-summary"` reporter | Generates an additional `coverage/coverage-summary.json` artefact | Ensure `.gitignore` includes the `coverage/` directory (TODO: confirm current `.gitignore` state) |
| `pytest-cov` addition | TODO — Python service not identified in provided context | TODO |

---

## Acceptance Criteria

1. **Given** the `user-management` service with its existing test suite, **when** `npm test` is executed, **then** a `coverage/` directory is produced containing at minimum `lcov.info`, `index.html`, and `coverage-summary.json` files.

2. **Given** the Jest configuration with `coverageProvider` set to `"v8"`, **when** `npm test` is executed, **then** the terminal output displays a per-file coverage table covering all files matched by `collectCoverageFrom` (`src/**/*.js` excluding `src/__tests__/**`).

3. **Given** a `coverageThreshold` is configured with a global line-coverage minimum, **when** `npm test` is executed and the measured line coverage is below that threshold, **then** the Jest process exits with a non-zero exit code and prints a threshold-violation message.

4. **Given** the `coverageThreshold` is configured and the full test suite passes with coverage at or above the threshold, **when** `npm test` is executed in CI, **then** the process exits with code `0`.

5. **Given** the `lcov.info` artefact is produced in `coverage/`, **when** a CI step uploads it to a coverage reporting service (e.g., Codecov or GitHub Actions coverage summary), **then** the upload completes without error and a coverage percentage is reported against the pull request.

6. **Given** the `RecoverPassword` use case (`src/application/usecases/RecoverPassword.js`) is included in `collectCoverageFrom`, **when** `npm test` is executed, **then** the coverage report includes a row for `RecoverPassword.js` showing its current measured coverage (even if zero), confirming the file is not silently excluded.

7. **Given** the `pytest-cov` addition (Python scope — TODO), **when** the Python test suite is executed, **then** a coverage report is generated and the process exits non-zero if coverage falls below the configured threshold. *(Criterion pending Python service identification.)*

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | The task title specifies `pytest-cov` (a Python tool), but the entire codebase provided is Node.js and Java. Is there a Python service or component not included in the provided context that requires `pytest-cov`? | TODO | TODO |
| 2 | What are the target coverage thresholds (lines, branches, functions, statements) to enforce for the `user-management` service? Should they be set to current measured values initially? | TODO | TODO |
| 3 | Is the `coverage/` directory currently listed in `.gitignore`? The `.gitignore` file was not provided in the context. | TODO | TODO |
| 4 | Should the `payment-service` (Java/JUnit 5) also have coverage reporting improvements (e.g., JaCoCo configuration) as part of this effort, or is scope limited to the Node.js service? | TODO | TODO |
| 5 | Is there a CI workflow file (`.github/workflows/ci.yml` is referenced in `AGENTS.md`) that needs to be updated to upload the `lcov.info` artefact to a coverage service? The workflow file was not provided. | TODO | TODO |
| 6 | Should `coverageProvider` be set to `"v8"` (native) or remain as the default `"babel"` instrumentation? This affects accuracy and performance. | TODO | TODO |