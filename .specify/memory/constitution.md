# CONSTITUTION — pytest-cov Integration for Test Coverage Reporting

## Project Identity

**Name:** pytest-cov Coverage Reporting Integration
**Purpose:** Add `pytest-cov` to the `user-management` Node.js service's test toolchain to enable structured test coverage reporting.
**High-level goal:** Instrument the existing Jest-based test suite in `user-management` with coverage reporting tooling, ensuring coverage results are generated consistently on every test run and visible in CI.

> **Note:** The source code is a Node.js / Jest project. `pytest-cov` is a Python tool. The task as stated targets a Python context, but no Python service exists in this codebase. This constitution governs the intent — adding a coverage reporting plugin to the test runner — applied to the actual stack (Jest + `--coverage`). **TODO: Confirm with project owner whether a Python service is in scope or whether this task targets Jest coverage configuration.**

---

## Guiding Principles

1. **Prefer extending the existing Jest `--coverage` flag over introducing a new test runner** because `package.json` already declares `"test": "jest --coverage"` and adding a second coverage tool would create conflicting reports.
2. **Prefer configuration-as-code over ad-hoc CLI flags** because `collectCoverageFrom` and `coverageDirectory` are already declared in `package.json`'s `jest` block — all coverage settings must live there, not in scattered scripts.
3. **Prefer coverage enforcement at CI gate over developer-local enforcement** because the upgrade urgency is medium and blocking local development workflows is disproportionate to the risk.
4. **Prefer additive changes over rewrites** because the existing test suite (health, loginUser, registerUser) is already passing; coverage tooling must not alter test behaviour or test output format.

---

## Constraints

- **Effort ceiling:** Moderate option — changes must be completable in a small number of person-days (exact figure not provided; **TODO: confirm person-days from project manager**).
- **Runtime mandate:** Node.js 20 LTS (per `README.md` and `AGENTS.md`); no runtime version changes permitted.
- **Scope freeze:** Only the `user-management` service is in scope. The `payment-service` (Java 17 / Spring Boot) uses JUnit 5 + JaCoCo conventions and is **out of scope**.
- **No new test framework:** Jest 29 is the mandated test runner; switching to a different runner is not permitted.
- **No production dependency changes:** Coverage tooling must be added to `devDependencies` only.

---

## Quality Standards

- **Coverage floor:** Line coverage must reach ≥ 80% across `src/**/*.js` (excluding `src/__tests__/**`) before the task is considered complete.
- **Coverage report formats:** At minimum, `text` (console summary) and `lcov` (for CI upload) reporters must be configured.
- **CI gate:** The `npm test` command must exit non-zero if coverage thresholds are not met; this must be verified in the GitHub Actions workflow (`ci.yml`).
- **No test regressions:** All pre-existing tests must continue to pass after configuration changes; a red test suite blocks merge.
- **Documentation:** `README.md` `npm test` description must reflect the coverage threshold and report output location (`coverage/`).
- **Code review:** All changes to `package.json` and CI configuration require at least one peer review approval before merge.

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | Use Jest's built-in `--coverage` (via `jest-circus` + V8/Istanbul) rather than adding `pytest-cov` | No Python runtime exists in this repository; Jest already ships coverage support; adding `pytest-cov` would require a Python toolchain with no benefit | Accepted |
| ADR-002 | Coverage thresholds declared in `package.json` `jest.coverageThreshold` block | Keeps all test configuration co-located; consistent with existing `collectCoverageFrom` and `coverageDirectory` settings already present | Accepted |
| ADR-003 | `lcov` + `text` reporters selected as minimum set | `lcov` enables CI coverage upload (e.g. Codecov/Coveralls); `text` provides immediate console feedback | Accepted |
| ADR-004 | Python service scope — **TODO** | No Python service identified in codebase; task may be misrouted or a Python service may be planned but not yet present | Proposed |