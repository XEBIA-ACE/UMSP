# Tasks: Migrate Flask App to Application Factory Pattern (`create_app()`)

> **Scope notice:** The provided source code is a Node.js/Express + Spring Boot (Java) system. No Flask application, Python runtime, or Python build tooling is present in the tech analysis or source files. The task description references Flask, but the only application factory pattern work evidenced in the codebase is the **Node.js `user-management` service**, which already partially implements a `createApp()` factory in `user-management/src/infrastructure/app.js` (referenced by `health.test.js`). Tasks below are scoped strictly to what is present in the provided context.

---

## Prerequisites

- [ ] [XS] Confirm Node.js version in use matches `Node.js 20 LTS` as declared in `AGENTS.md` by running `node --version` in the `user-management/` directory
- [ ] [XS] Confirm all existing `user-management` dependencies are installed and `npm ci` completes cleanly against `user-management/package.json`
- [ ] [XS] Verify Jest test runner is available and `jest.config.js` is present in `user-management/` (referenced in `AGENTS.md`)

---

## Phase 1 — Preparation

- [ ] [XS] Create a feature branch `feat/app-factory-pattern` from `main` in the repository root
- [ ] [S] Run the existing `user-management` test suite (`npm test` in `user-management/`) and record the baseline pass/fail counts and coverage output as `user-management/test-baseline.txt`
- [ ] [XS] Audit `user-management/src/infrastructure/app.js` to document its current structure — confirm whether `createApp()` is exported, whether `app.listen()` is called inside it, and whether a separate entry point (`server.js`) exists, recording findings in a code comment at the top of the file

---

## Phase 2 — Core Upgrade

- [ ] [M] Refactor `user-management/src/infrastructure/app.js` to export a `createApp()` factory function that registers all middleware and routes but contains no `app.listen()` call — ensure the function accepts an optional `config` parameter sourced from `user-management/src/config/index.js`
- [ ] [S] Create (or verify) `user-management/src/server.js` as the sole entry point that calls `createApp()` and then `app.listen()`, importing config from `user-management/src/config/index.js`
- [ ] [S] Update `user-management/src/routes/index.js` to be mounted inside `createApp()` rather than at module load time, ensuring `auth.routes.js`, `user.routes.js`, and `payment.routes.js` are all registered within the factory
- [ ] [S] Update `user-management/src/middleware/errorHandler.js`, `rateLimiter.js`, `requestLogger.js`, and `authenticate.js` to be applied inside `createApp()` in the correct middleware order (logger → rateLimiter → routes → errorHandler)
- [ ] [XS] Update the `main` field (or `start` script) in `user-management/package.json` to point to `src/server.js` instead of any previous entry point

---

## Phase 3 — Testing & Validation

- [ ] [XS] Verify `user-management/src/__tests__/health.test.js` imports `createApp` from `../infrastructure/app` and that the import path resolves correctly after the refactor
- [ ] [S] Run the full `user-management` test suite and confirm all tests that previously passed still pass, comparing against `user-management/test-baseline.txt`
- [ ] [S] Add or update integration tests in `user-management/src/__tests__/` to assert that calling `createApp()` twice produces two independent Express app instances (isolation guarantee of the factory pattern)
- [ ] [XS] Confirm no test file directly requires the old app module path in a way that bypasses `createApp()` — search for bare `require('../infrastructure/app')` calls that do not destructure `createApp`

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [XS] Update the `test` job in `.github/workflows/ci.yml` to ensure the `user-management` test step invokes `npm test` from the `user-management/` working directory and fails the build on any test regression
- [ ] [XS] Verify the `user-management/Dockerfile` `CMD` or `ENTRYPOINT` references `src/server.js` (the new entry point) and not a path that previously called `app.listen()` directly

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Add a `## Application Factory Pattern` section to `AGENTS.md` under the `user-management` project structure notes, documenting that `app.js` exports `createApp()` and `server.js` is the sole process entry point
- [ ] [XS] Update `user-management/.env.example` if any new config keys are required by the `createApp(config)` signature, ensuring all keys are documented with example values and no secrets are committed
- [ ] [XS] Verify `tasks.md` in the repository root is updated to mark this migration task complete after all phases pass CI

---

> **Out of scope:** No Flask, Python, `requirements.txt`, `wsgi.py`, `__init__.py`, or any Python-related tasks are generated because no such files or runtime are present in the provided tech analysis or source code.