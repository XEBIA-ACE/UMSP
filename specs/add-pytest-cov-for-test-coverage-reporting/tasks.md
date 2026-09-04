# Tasks: Add pytest-cov for Test Coverage Reporting

> **Scope:** `user-management` service only. The source code confirms this is a Node.js 20 / Jest project (`user-management/package.json`). `pytest-cov` is a Python tool; the actual requirement is **Jest coverage reporting**, which is already partially wired (`"test": "jest --coverage"` exists in `package.json`). All tasks below address completing and formalising Jest-based coverage reporting for the `user-management` service. The `payment-service` (Java/JUnit 5) is out of scope — no Python runtime is present in the provided tech analysis.

---

## Prerequisites

- [ ] [XS] Confirm Node.js 20 LTS is installed locally and matches the `user-management` runtime declared in `README.md`
- [ ] [XS] Confirm `jest@^29.7.0` is resolvable in `user-management/node_modules` by running `npm ls jest` in `user-management/`
- [ ] [XS] Verify write access to the `user-management/` directory and that `coverage/` is listed in `user-management/.gitignore`

---

## Phase 1 — Preparation

- [ ] [XS] Add `coverage/` to `.gitignore` in `user-management/.gitignore` to prevent generated coverage artefacts from being committed
- [ ] [S] Capture a pre-change test baseline by running `npm test` in `user-management/` and recording pass/fail counts and any existing coverage output to `user-management/coverage-baseline.txt`
- [ ] [XS] Confirm `collectCoverageFrom` in the `jest` block of `user-management/package.json` excludes test files via the existing `"!src/__tests__/**"` glob — no change needed if already correct

---

## Phase 2 — Core Upgrade

- [ ] [S] Add `@jest/coverage-provider` configuration and set `coverageProvider` to `"v8"` in the `jest` block of `user-management/package.json` to enable fast native V8 coverage collection
- [ ] [S] Add `coverageReporters` array to the `jest` block in `user-management/package.json` specifying `["text", "lcov", "html"]` to produce terminal summary, `lcov.info` for CI ingestion, and browsable HTML report under `user-management/coverage/`
- [ ] [XS] Add `coverageThresholds` block to the `jest` block in `user-management/package.json` setting `global` thresholds for `lines`, `functions`, `branches`, and `statements` at an initial value of `80` to enforce a coverage gate
- [ ] [XS] Verify the `"test"` script in `user-management/package.json` remains `"jest --coverage"` and add a separate `"test:ci"` script as `"jest --coverage --ci --forceExit"` for non-interactive CI runs

---

## Phase 3 — Testing & Validation

- [ ] [S] Run `npm test` in `user-management/` and confirm all four test files (`health.test.js`, `loginUser.test.js`, `registerUser.test.js`, and any others under `src/__tests__/`) pass with coverage output printed to the terminal
- [ ] [XS] Verify `user-management/coverage/lcov.info` is generated after the test run and is non-empty
- [ ] [XS] Verify `user-management/coverage/index.html` is generated and opens correctly in a browser showing per-file line/branch/function metrics
- [ ] [XS] Confirm coverage for `src/application/usecases/RecoverPassword.js` and `src/application/usecases/RegisterUser.js` is reported individually in the HTML output
- [ ] [XS] Confirm the `coverageThresholds` gate triggers a non-zero exit code when thresholds are not met by temporarily lowering a threshold below the actual value, then restore the correct value

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [M] Update `.github/workflows/ci.yml` to add an `Upload coverage` step after the `npm test` step for the `user-management` job, using `actions/upload-artifact@v4` to archive `user-management/coverage/lcov.info` as artefact `user-management-coverage`
- [ ] [S] Add an `npm run test:ci` invocation (using the new `test:ci` script) in `.github/workflows/ci.yml` for the `user-management` job in place of any bare `npm test` call, ensuring `--ci` flag prevents interactive prompts and `--forceExit` prevents Jest from hanging

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Update the `user-management` **Quick start** section in `README.md` to document that `npm test` produces a coverage report in `user-management/coverage/` and describe the three output formats (`text`, `lcov`, `html`)
- [ ] [XS] Add a `## Coverage` section to `README.md` under the `user-management` service entry documenting the enforced 80% threshold and how to view the HTML report locally