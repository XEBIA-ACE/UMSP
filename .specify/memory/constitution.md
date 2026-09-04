# CONSTITUTION — pytest-cov Integration for Test Coverage Reporting

## Project Identity

**Name:** pytest-cov Coverage Reporting Integration
**Purpose:** Add `pytest-cov` to the `user-management` Node.js service's test toolchain to enable structured test coverage reporting.
**High-level goal:** Instrument the existing Jest-based test suite in `user-management` with coverage reporting tooling, ensuring coverage results are generated consistently on every test run and visible in CI.

> **Note:** The source code shows a Node.js/Jest project (`user-management`) and a Java/JUnit5 project (`payment-service`). `pytest-cov` is a Python tool. The task as stated cannot be applied literally to either service. This constitution governs the closest valid interpretation: **adding or formalising coverage reporting for the `user-management` service using its native toolchain (Jest `--coverage` / `jest-cov` equivalent)**. If a Python service exists elsewhere in the monorepo, that scope is a TODO.

---

## Guiding Principles

1. **Prefer native Jest coverage over introducing foreign tooling** because the `user-management` service is Node.js 20/Jest 29 — adding a Python tool (`pytest-cov`) would introduce an unrelated runtime dependency with no benefit.
2. **Prefer extending the existing `jest --coverage` configuration over adding new test runners** because `package.json` already declares `"test": "jest --coverage"` and a `coverageDirectory`/`collectCoverageFrom` config — the infrastructure is already partially in place.
3. **Prefer explicit `collectCoverageFrom` globs over implicit collection** because implicit collection risks missing new source files or including test files, producing misleading metrics.
4. **Prefer CI-enforced coverage thresholds over advisory-only reporting** because coverage gates without enforcement degrade silently over time.
5. **Prefer a single authoritative coverage report format (lcov + text-summary)** over multiple redundant formats to keep CI output readable and tooling integrations simple.

---

## Constraints

- **Timeline/effort:** Upgrade option is "moderate" with no explicit person-days figure. Treat as a small, bounded task — **TODO: confirm effort ceiling with project lead.**
- **Runtime mandate:** Node.js 20 LTS (`user-management`); Java 17/21 (`payment-service`). No Python runtime may be introduced unless a Python service is confirmed to exist — **TODO: confirm whether a Python service is in scope.**
- **Scope freeze:** Changes are limited to `user-management/` test configuration and CI pipeline. No production source changes are permitted.
- **No new test framework:** Jest 29 remains the sole test runner for `user-management`. No migration to Vitest, Mocha, or any other runner is in scope.
- **Budget:** No additional paid tooling or SaaS coverage services are in scope unless explicitly approved — **TODO: confirm if Codecov/Coveralls integration is desired.**

---

## Quality Standards

| Standard | Measurable Bar |
|---|---|
| Coverage floor — statements | ≥ 80% statement coverage on `src/**/*.js` (excluding `src/__tests__/**`) |
| Coverage floor — branches | ≥ 75% branch coverage |
| CI gate | `npm test` must exit 0; a non-zero exit from a coverage threshold failure blocks merge |
| Report artifacts | `coverage/lcov.info` and `coverage/coverage-summary.json` must be produced on every CI run |
| PR review | Coverage diff must be reviewed; PRs that drop coverage below threshold are blocked |
| Documentation | `README.md` must include a "Test Coverage" section describing how to run and interpret reports |

---

## Decision Log

| ID | Decision | Rationale | Status |
|---|---|---|---|
| ADR-001 | Use Jest's built-in `--coverage` (via V8/Istanbul) rather than `pytest-cov` | Project runtime is Node.js 20; `pytest-cov` is Python-only and inapplicable | Accepted |
| ADR-002 | Retain `jest --coverage` in the `"test"` npm script | Already present in `package.json`; no migration cost | Accepted |
| ADR-003 | Enforce coverage thresholds via Jest `coverageThreshold` config | Prevents silent regression; native to Jest 29 with zero extra dependencies | Accepted |
| ADR-004 | Scope limited to `user-management/`; `payment-service` uses JaCoCo (Maven) | Each service uses its own ecosystem tooling; cross-service changes are out of scope | Accepted |
| ADR-005 | Python service scope | No Python service identified in source analysis; `pytest-cov` applicability is **TODO** pending confirmation | Proposed |