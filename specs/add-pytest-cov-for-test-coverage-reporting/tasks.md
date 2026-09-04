# Tasks: Add pytest-cov for Test Coverage Reporting

> **Scope:** `user-management` service only. The source code confirms this is a Node.js 20 / Jest project (`user-management/package.json`). `pytest-cov` is a Python tool; the actual requirement is **Jest coverage reporting**, which is already partially configured in `package.json` (`"test": "jest --coverage"`, `coverageDirectory`, `collectCoverageFrom`). Tasks below complete and harden that coverage setup. The `payment-service` (Java/JUnit 5) is out of scope — no Python runtime is present in the provided context.

---

## Prerequisites

- [ ] [XS] Confirm Node.js 20 LTS is installed and `node --version` returns `v20.x` in `user-management/`
- [ ] [XS] Confirm Jest 29.7.0 is resolvable by running `npx jest --version` in `user-management/`
- [ ] [XS] Verify write access to `user-management/package.json` and the `user-management/coverage/` output directory

---

## Phase 1 — Preparation

- [ ] [XS] Create a feature branch `feat/jest-coverage-reporting` from `main` in the repository root
- [ ] [S] Audit existing Jest coverage configuration in `user-management/package.json` under the `"jest"` key — document current `coverageDirectory`, `collectCoverageFrom`, and any missing `coverageReporters` or `coverageThresholds` fields
- [ ] [XS] Run `npm test` in `user-management/` and capture the baseline coverage summary (lines, branches, functions, statements) for `src/**/*.js` excluding `src/__tests__/**` as the pre-change reference

---

## Phase 2 — Core Upgrade

- [ ] [S] Add `coverageReporters` array (`["text", "lcov", "html", "json-summary"]`) to the `"jest"` config block in `user-management/package.json` so that `lcov.info`, `index.html`, and `coverage-summary.json` are all emitted under `user-management/coverage/`
- [ ] [XS] Add `@jest/coverage-provider` option `"v8"` as `coverageProvider` in the `"jest"` config block in `user-management/package.json` to use the V8 native coverage engine available in Node.js 20
- [ ] [XS] Add a `"test:coverage"` script entry in `user-management/package.json` set to `"jest --coverage --forceExit"` to provide an explicit coverage-only invocation distinct from the plain `"test"` script
- [ ] [S] Add `coverageThresholds` block to the `"jest"` config in `user-management/package.json` with initial thresholds derived from the Phase 1 baseline (set `global` thresholds for `lines`, `branches`, `functions`, `statements` at the observed baseline percentage, rounded down to the nearest 5 to avoid immediate failures)
- [ ] [XS] Add `user-management/coverage/` to `user-management/.gitignore` (create the file if absent) to prevent generated coverage artefacts from being committed

---

## Phase 3 — Testing & Validation

- [ ] [S] Run `npm run test:coverage` in `user-management/` and verify all four report formats are written: `coverage/lcov.info`, `coverage/index.html`, `coverage/coverage-summary.json`, and console `text` table
- [ ] [XS] Confirm coverage is collected from `src/application/usecases/RecoverPassword.js`, `src/application/usecases/RegisterUser.js`, `src/adapters/outbound/persistence/InMemoryUserRepository.js`, and `src/adapters/inbound/http/controllers/AuthController.js` by inspecting the `text` table output
- [ ] [XS] Confirm `src/__tests__/` files are excluded from the coverage report by verifying no test files appear in the `coverage-summary.json` output
- [ ] [XS] Intentionally lower one threshold value in `user-management/package.json` below the actual coverage to confirm Jest exits with a non-zero code, then restore the correct value

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [M] Update `.github/workflows/ci.yml` to add a coverage step in the `user-management` job: run `npm run test:coverage`, then upload `user-management/coverage/lcov.info` as a build artefact using `actions/upload-artifact@v4`
- [ ] [XS] Add `coverage/` to the `user-management` service's `.dockerignore` (create if absent) so the `coverage/` directory is excluded from the Docker build context referenced in `README.md`

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Update the `user-management` **Quick start** section in `README.md` to document the `npm run test:coverage` script and note that HTML reports are written to `user-management/coverage/index.html`
- [ ] [XS] Add a `## Coverage` section to `AGENTS.md` under the Jest + Supertest row describing the `coverageReporters`, `coverageProvider`, and threshold enforcement now in place in `user-management/package.json`