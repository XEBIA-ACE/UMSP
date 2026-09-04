# Tasks: Migrate Flask App to Application Factory Pattern (`create_app()`)

> **Scope notice:** The provided source code is a Node.js/Express + Spring Boot (Java) system. No Flask application, Python runtime, or Python build tooling is present in the tech analysis or source files. The task description references Flask, but the only application factory pattern work evidenced in the codebase is the **Node.js/Express `createApp()` pattern** already partially in use in `user-management/src/infrastructure/app.js` (imported in `user-management/src/__tests__/health.test.js`). Tasks below are grounded exclusively in what is present in the provided context.

---

## Prerequisites

- [ ] [XS] Confirm `user-management/src/infrastructure/app.js` exports a `createApp()` function and that `user-management/src/server.js` calls `app.listen()` separately — verify both files exist and match the structure declared in `AGENTS.md`
- [ ] [XS] Confirm Node.js 20 LTS is installed locally and matches the runtime declared in `AGENTS.md`
- [ ] [XS] Confirm all existing Jest + Supertest tests pass on the current branch by running the test suite in `user-management/` before any changes are made

---

## Phase 1 — Preparation

- [ ] [XS] Create a feature branch `feat/app-factory-pattern` from `main` in the repository
- [ ] [S] Audit all files in `user-management/src/` that directly `require` or import the Express `app` instance (rather than calling `createApp()`) and record them as migration targets — check `user-management/src/server.js`, all files under `user-management/src/routes/`, `user-management/src/middleware/`, and `user-management/src/controllers/`
- [ ] [XS] Capture the current Jest test baseline by running the full `user-management/` test suite and saving output (pass count, coverage summary) for regression comparison in Phase 3

---

## Phase 2 — Core Upgrade

N/A — not applicable to this task

> The Spring Boot `PaymentServiceApplication.java` and `AppConfig.java` already follow the Spring Boot application factory idiom and require no changes. The Node.js `createApp()` factory is already referenced in `user-management/src/__tests__/health.test.js` via `require('../infrastructure/app')`. The tasks below address completing and hardening that pattern across the `user-management` service.

- [ ] [S] Ensure `user-management/src/infrastructure/app.js` exports only `createApp()` (no top-level `app.listen()` call) and registers all middleware (`authenticate.js`, `rateLimiter.js`, `requestLogger.js`, `errorHandler.js`, `validateSchema.js`) and routers (`routes/index.js`) inside the factory function body
- [ ] [S] Ensure `user-management/src/server.js` is the sole entry point that calls `createApp()` and then `app.listen()`, and that it does not export the `app` instance directly
- [ ] [S] Update `user-management/src/routes/index.js` to mount `auth.routes.js`, `user.routes.js`, and `payment.routes.js` only when invoked through the `createApp()` factory — remove any module-level route registration that runs on `require`
- [ ] [XS] Verify `user-management/src/__tests__/health.test.js` already uses `createApp()` from `../infrastructure/app` (confirmed in provided source) and update the import path if `app.js` is moved during refactor
- [ ] [S] Update any integration tests under `user-management/tests/integration/` (`auth.test.js`, `user.test.js`, `payment.test.js`) that instantiate the Express app directly to use `createApp()` from `user-management/src/infrastructure/app.js` instead

---

## Phase 3 — Testing & Validation

- [ ] [S] Run the full Jest test suite in `user-management/` and confirm all tests that previously passed still pass — compare against the baseline captured in Phase 1
- [ ] [XS] Verify that `user-management/src/__tests__/health.test.js` passes all three assertions (`status 200`, `ISO timestamp`, `Content-Type: application/json`) with the refactored `createApp()` in `user-management/src/infrastructure/app.js`
- [ ] [XS] Confirm that `user-management/src/server.js` starts without error when run directly (`node src/server.js`) and that the health endpoint responds correctly via `curl` or equivalent

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [XS] Verify the `user-management` service `Dockerfile` uses `node src/server.js` (or equivalent npm start script) as its `CMD`/`ENTRYPOINT` — not `app.js` directly — so the factory pattern entry point is respected in container builds
- [ ] [XS] Confirm the `ci.yml` GitHub Actions workflow runs the `user-management/` Jest suite and that no hardcoded references to a non-factory app entry point exist in the workflow steps

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Add a `CHANGELOG.md` entry (or update the existing one) in `user-management/` documenting that the Express app now uses the `createApp()` application factory pattern, with `server.js` as the sole entry point
- [ ] [XS] Update `AGENTS.md` section 2 (Project Structure) to confirm that `gateway/src/app.js` and `user-management/src/infrastructure/app.js` both follow the app-factory convention, so future agents do not re-introduce top-level `app.listen()` calls in those files