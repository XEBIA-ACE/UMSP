# Plan: Add pytest-cov for Test Coverage Reporting

## Overview

**Migration strategy: Big-bang (single-phase, low-risk addition)**

The task is a narrow, additive change: introduce `pytest-cov` as a development dependency in the `user-management` Node.js service's test toolchain. No existing code is modified, no APIs change, and no infrastructure is restructured.

However, a critical observation from the code context must be stated upfront: **the `user-management` service uses Jest (not pytest)**. `pytest-cov` is a Python tool; it has no applicability to a Node.js/Jest project. The existing `package.json` already configures Jest with `--coverage` and a `coverageDirectory`/`collectCoverageFrom` block, meaning **coverage reporting is already functional via `jest --coverage`**.

This plan therefore covers two interpretations:
1. **Literal interpretation**: Add `pytest-cov` — not applicable to this stack; documented as a no-op with rationale.
2. **Intent interpretation**: Improve/formalise Jest-based coverage reporting in `user-management` — the actionable path, scoped to what the existing codebase supports.

The risk score is low and effort is minimal (< 1 person-day). A big-bang approach (single PR, no feature flag, no parallel run) is appropriate.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|-------|-------------|--------------|-----------------|
| 1 | Verify existing Jest coverage config in `user-management/package.json` and confirm it is complete | None | 0.1 person-days |
| 2 | Add `@jest/coverage-provider` or `jest-coverage-thresholds` config if coverage gates are absent; update `package.json` jest config block | Phase 1 complete | 0.2 person-days |
| 3 | Update CI pipeline to fail on coverage below threshold and publish coverage artifact | Phase 2 complete | 0.2 person-days |
| 4 | Update `README.md` to document coverage command and threshold | Phase 3 complete | 0.1 person-days |

> **Note on `pytest-cov`**: This package is a pytest plugin for Python projects. The `user-management` service is Node.js 20 / Jest 29. The `payment-service` is Java 17 / Spring Boot with JUnit 5 — also not Python. There is no Python runtime, `requirements.txt`, `setup.py`, `pyproject.toml`, or `pytest` configuration anywhere in the provided context. Installing `pytest-cov` would have no effect on either service. If a Python service exists outside the provided context, mark its location as TODO and apply this plan there instead.

---

## Component Changes

### `user-management/package.json`

**What changes**: The `jest` configuration block already contains `"coverageDirectory": "coverage"` and `"collectCoverageFrom"`. The following additions formalise coverage enforcement:

- Add `coverageThreshold` to the `jest` config key to enforce minimum coverage gates.
- Add `coverageReporters` to emit both human-readable (`text`, `lcov`) and machine-readable (`json-summary`) formats for CI consumption.
- No new runtime dependencies are required; `jest --coverage` uses V8 or Babel coverage built into Jest 29.

**Current `jest` block** (from `user-management/package.json`):
```json
"jest": {
  "testEnvironment": "node",
  "testMatch": ["**/src/__tests__/**/*.test.js"],
  "coverageDirectory": "coverage",
  "collectCoverageFrom": [
    "src/**/*.js",
    "!src/__tests__/**"
  ]
}
```

**Target `jest` block**:
```json
"jest": {
  "testEnvironment": "node",
  "testMatch": ["**/src/__tests__/**/*.test.js"],
  "coverageDirectory": "coverage",
  "collectCoverageFrom": [
    "src/**/*.js",
    "!src/__tests__/**"
  ],
  "coverageReporters": ["text", "lcov", "json-summary"],
  "coverageThreshold": {
    "global": {
      "lines": 80,
      "functions": 80,
      "branches": 70,
      "statements": 80
    }
  }
}
```

**Files affected**:
- `user-management/package.json` — `jest` config block only

**APIs modified**: None. The `npm test` script (`jest --coverage`) is unchanged.

---

### `user-management` — No source file changes

No changes to:
- `src/application/usecases/RecoverPassword.js`
- `src/application/usecases/RegisterUser.js`
- `src/adapters/inbound/http/controllers/AuthController.js`
- `src/adapters/outbound/persistence/InMemoryUserRepository.js`
- `src/adapters/outbound/auth/JwtAuthAdapter.js`
- Any `src/__tests__/*.test.js` file

---

### `payment-service` — No changes

The `payment-service` is Java/Spring Boot with JUnit 5 and Mockito. Coverage is handled by JaCoCo (standard for Maven/Spring Boot projects). `pytest-cov` does not apply. No changes to any file under `payment-service/`.

---

## Dependency Upgrade Plan

| Dependency | Current Version | Target Version | Breaking Changes | Migration Notes |
|------------|----------------|----------------|-----------------|-----------------|
| `jest` (devDependency) | `^29.7.0` | `^29.7.0` (no change) | None | Coverage is built into Jest 29 via `--coverage` flag; no additional package needed |
| `pytest-cov` | N/A (not present) | N/A | N/A | **Not applicable** — no Python runtime exists in this codebase. Do not install. |

> All version numbers sourced from `user-management/package.json` as provided in context. No training-data version guesses used.

---

## Infrastructure Changes

### CI/CD Pipeline (`.github/workflows/ci.yml`)

The `AGENTS.md` references a `.github/workflows/ci.yml` file. Its contents are not provided in context.

**Required change** (add to the Node.js test step):
- Ensure the `npm test` step in the `user-management` job runs `jest --coverage` (already the case per `package.json` `"test"` script).
- Add a step to upload the `user-management/coverage/lcov.info` artifact for downstream reporting (e.g., Codecov, Coveralls, or GitHub Actions artifact upload).
- The CI gate will automatically fail if `coverageThreshold` is not met, because Jest exits with a non-zero code.

**Example addition to CI workflow** (exact YAML keys depend on existing `ci.yml` structure — TODO: verify step names):
```yaml
- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: user-management-coverage
    path: user-management/coverage/lcov.info
```

**Docker**: No changes. Coverage is a dev/CI concern only; the `Dockerfile` for `user-management` does not run tests.

**Kubernetes manifests**: N/A — not applicable to this task.

**IaC**: TODO — no IaC files provided in context.

---

## Rollback Strategy

### Phase 1 (Verification)
- No changes made; nothing to roll back.

### Phase 2 (`package.json` jest config update)
- Revert `user-management/package.json` to remove `coverageReporters` and `coverageThreshold` keys from the `jest` block.
- Run `npm test` to confirm tests pass without threshold enforcement.
- This is a single-file, single-key revert; independently reversible via `git revert` or manual edit.

### Phase 3 (CI pipeline update)
- Remove the `upload-artifact` step from `.github/workflows/ci.yml`.
- If a coverage gate step was added, remove it.
- Push the revert commit; CI will return to its prior behaviour.

### Phase 4 (README update)
- Revert documentation changes to `README.md` via `git revert` or manual edit.
- No functional impact.

---

## Testing Strategy

### Unit tests (existing — no change required)
- **Tool**: Jest 29 (`jest ^29.7.0`)
- **Files**: `user-management/src/__tests__/loginUser.test.js`, `registerUser.test.js`
- **Coverage target**: ≥ 80% lines/functions/statements, ≥ 70% branches (enforced via `coverageThreshold`)
- **Run**: `npm test` (executes `jest --coverage`)

### Integration tests (existing — no change required)
- **Tool**: Jest 29 + Supertest (`supertest ^6.3.3`)
- **Files**: `user-management/src/__tests__/health.test.js`
- **Coverage target**: Included in the global threshold above via `collectCoverageFrom: ["src/**/*.js"]`

### Regression
- The existing test suite serves as the regression baseline.
- No new test files are required for this task.
- CI gate: `npm test` must exit 0 (Jest fails the process if thresholds are not met).

### Performance
- N/A — coverage instrumentation adds negligible overhead to a small Node.js test suite of this size.

### CI gate summary
| Gate | Tool | Pass Condition |
|------|------|---------------|
| Unit + integration tests pass | Jest 29 | Exit code 0 |
| Line coverage ≥ 80% | Jest `coverageThreshold` | Enforced by Jest; non-zero exit on failure |
| Branch coverage ≥ 70% | Jest `coverageThreshold` | Enforced by Jest; non-zero exit on failure |
| Coverage artifact uploaded | GitHub Actions | `lcov.info` present in artifact store |

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|-----------|-------|---------------------|-------|
| Confirm Jest coverage already functional; document pytest-cov inapplicability | Phase 1 | Day 1 | TODO |
| Update `user-management/package.json` jest config with thresholds and reporters | Phase 2 | Day 1 | TODO |
| Update `.github/workflows/ci.yml` to upload coverage artifact | Phase 3 | Day 1 | TODO |
| Update `README.md` with coverage documentation | Phase 4 | Day 1 | TODO |

> Total estimated effort: ~0.5–0.6 person-days. All phases can be completed in a single working session and delivered as one pull request.