# Plan: Add pytest-cov for Test Coverage Reporting

## Overview

**Migration strategy: Big-bang (single-phase, low-risk addition)**

The task is a narrow, additive change: introduce `pytest-cov` as a development dependency in the `user-management` Node.js service's test toolchain. No existing code is deleted, no APIs are modified, and no runtime behaviour changes.

However, a critical observation from the code context must be stated upfront: **the `user-management` service uses Jest (not pytest)**. `pytest-cov` is a Python tool; it has no applicability to a Node.js/Jest project. The existing `package.json` already configures Jest with `--coverage` and a `coverageDirectory` of `coverage`, meaning **coverage reporting is already functional via Jest's built-in V8/Istanbul coverage**.

Given the stated goal is "add pytest-cov for test coverage reporting" and the only test-bearing service with a visible package manifest is the Node.js `user-management` service (which uses Jest), this plan covers:

1. Confirming and formalising the existing Jest coverage configuration.
2. Adding `@jest/coverage-provider` or `jest-coverage-thresholds` if stricter enforcement is needed — the closest Jest-native equivalent to what `pytest-cov` provides in Python projects.

If a Python service exists in this monorepo but is absent from the provided context, the infrastructure for it is marked **TODO**.

Risk score: **Low**. Effort estimate: **< 1 person-day**.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|-------|-------------|--------------|-----------------|
| 1 | Audit existing Jest coverage config in `user-management/package.json`; confirm `--coverage` flag is present in `test` script | None | 0.1 person-days |
| 2 | Add coverage thresholds to `jest` config block in `package.json`; add `coverageReporters` for lcov + text-summary output | Phase 1 complete | 0.2 person-days |
| 3 | Update CI pipeline to fail on coverage gate and publish HTML/lcov report as artifact | Phase 2 complete | 0.2 person-days |
| 4 | TODO — If a Python service is identified in the monorepo, install `pytest-cov` there and configure `pytest.ini` / `pyproject.toml` | Python service context required | TODO |

---

## Component Changes

### `user-management/package.json`

**What changes:** The `jest` configuration block gains `coverageThreshold` and an explicit `coverageReporters` list. No structural changes to source files.

**Current state (from context):**
```json
"scripts": {
  "test": "jest --coverage"
},
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

**Target state:**
```json
"scripts": {
  "test": "jest --coverage"
},
"jest": {
  "testEnvironment": "node",
  "testMatch": ["**/src/__tests__/**/*.test.js"],
  "coverageDirectory": "coverage",
  "collectCoverageFrom": [
    "src/**/*.js",
    "!src/__tests__/**"
  ],
  "coverageReporters": ["text-summary", "lcov", "html"],
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "functions": 80,
      "lines": 80,
      "statements": 80
    }
  }
}
```

**Files affected:**
- `user-management/package.json` — `jest` config block only

**APIs/methods affected:** None. The following test files are already covered by `collectCoverageFrom` and require no changes:
- `user-management/src/__tests__/health.test.js`
- `user-management/src/__tests__/loginUser.test.js`
- `user-management/src/__tests__/registerUser.test.js`

Source files instrumented (no changes needed):
- `user-management/src/application/usecases/RecoverPassword.js`
- `user-management/src/application/usecases/RegisterUser.js`
- `user-management/src/adapters/inbound/http/controllers/AuthController.js`
- `user-management/src/adapters/inbound/http/routes/authRoutes.js`
- `user-management/src/adapters/outbound/auth/JwtAuthAdapter.js`
- `user-management/src/adapters/outbound/persistence/InMemoryUserRepository.js`

### Python service (if present)

**TODO** — No Python service, `requirements.txt`, `pyproject.toml`, or `pytest.ini` is present in the provided context. If a Python service exists, the following changes would apply:

- Add `pytest-cov` to `requirements-dev.txt` or `pyproject.toml` `[dev-dependencies]`
- Add `pytest.ini` or `[tool.pytest.ini_options]` section with `--cov` flags
- TODO: identify service root directory

---

## Dependency Upgrade Plan

| Dependency | Current Version | Target Version | Breaking Changes | Migration Notes |
|------------|----------------|----------------|-----------------|-----------------|
| `jest` (devDependency) | `^29.7.0` | `^29.7.0` (no change) | None | Already installed; coverage is built-in via `jest --coverage` |
| `pytest-cov` | N/A (not present) | TODO — version not determinable from provided tech analysis | N/A | Only applicable if a Python service exists in this monorepo; not present in provided context |

> **Note:** The tech analysis does not specify a `pytest-cov` version. No version number is invented here per the rules. If a Python service is confirmed, the target version must be sourced from a fresh `pip install pytest-cov` resolution against the Python runtime version in use.

---

## Infrastructure Changes

### CI/CD Pipeline (`.github/workflows/ci.yml`)

The `AGENTS.md` confirms a GitHub Actions CI pipeline exists at `.github/workflows/ci.yml`. The file content is not provided, so changes are described by intent:

**Add to the `user-management` test job:**
```yaml
- name: Run tests with coverage
  working-directory: user-management
  run: npm test

- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: user-management-coverage
    path: user-management/coverage/
```

The `coverageThreshold` block in `package.json` will cause `jest --coverage` to exit non-zero if thresholds are not met, automatically failing the CI job — no additional CI gate configuration is required.

**Docker base image:** No change. Coverage reporting is a dev/CI-only concern; the `Dockerfile` for `user-management` is not affected.

**Kubernetes manifests:** N/A — not applicable to this task.

**IaC:** TODO — no IaC files are present in the provided context.

---

## Rollback Strategy

### Phase 1 (Audit) — Rollback
- No changes made; nothing to roll back.

### Phase 2 (Jest config changes) — Rollback
- Revert `user-management/package.json` to remove the `coverageThreshold` and `coverageReporters` keys added to the `jest` block.
- The `test` script (`jest --coverage`) remains unchanged and continues to work.
- Single-command rollback: `git revert <commit-sha>` targeting only `user-management/package.json`.

### Phase 3 (CI pipeline changes) — Rollback
- Remove the `Upload coverage report` step from `.github/workflows/ci.yml`.
- The test job continues to run; it simply will not upload the artifact.
- Single-command rollback: `git revert <commit-sha>` targeting only `.github/workflows/ci.yml`.

### Phase 4 (Python service — TODO)
- TODO — rollback steps depend on the Python service structure, which is absent from context.

---

## Testing Strategy

### Unit tests
- **Tool:** Jest `^29.7.0` (already installed)
- **Scope:** All files matching `user-management/src/__tests__/**/*.test.js`
- **Current tests confirmed in context:** `loginUser.test.js`, `registerUser.test.js`, `health.test.js`
- **Coverage target:** 80% lines / branches / functions / statements (enforced via `coverageThreshold`)
- **Run:** `npm test` from `user-management/`

### Integration tests
- **Tool:** Jest + Supertest `^6.3.3` (already installed)
- **Scope:** `health.test.js` exercises `createApp()` end-to-end via HTTP
- **Coverage contribution:** Covers `AuthController`, route wiring, and `createApp` infrastructure path

### Regression tests
- Existing test suite acts as regression suite. No new test files are required for this task.
- CI gate: `jest --coverage` exit code non-zero on threshold breach blocks merge.

### Performance tests
- N/A — not applicable to this task. Coverage instrumentation adds negligible overhead to a Jest run.

### CI gate summary
| Gate | Tool | Threshold | Blocks merge? |
|------|------|-----------|---------------|
| Unit + integration pass | Jest | 0 failures | Yes |
| Line coverage | Jest `coverageThreshold` | ≥ 80% | Yes |
| Branch coverage | Jest `coverageThreshold` | ≥ 80% | Yes |
| Coverage artifact upload | GitHub Actions `upload-artifact` | N/A | No (informational) |

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|-----------|-------|---------------------|-------|
| Audit existing Jest coverage config | Phase 1 | Day 1 (0.1 pd) | TODO |
| Add `coverageThreshold` + `coverageReporters` to `package.json` | Phase 2 | Day 1 (0.3 pd total) | TODO |
| Update `.github/workflows/ci.yml` to upload coverage artifact | Phase 3 | Day 1 (0.5 pd total) | TODO |
| Python service `pytest-cov` integration (if applicable) | Phase 4 | TODO — blocked on Python service context | TODO |