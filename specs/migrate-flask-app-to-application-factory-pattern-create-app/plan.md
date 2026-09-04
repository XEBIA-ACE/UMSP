# Plan: Migrate Flask App to Application Factory Pattern (`create_app()`)

## Overview

**Migration Strategy: Big-Bang (single-branch refactor)**

The task is to introduce the Flask application factory pattern (`create_app()`) to the Node.js/Express `user-management` service. The evidence from the provided source code shows that `user-management/src/__tests__/health.test.js` already imports `{ createApp }` from `../infrastructure/app`, meaning the test layer is written against the factory pattern but the factory itself may not yet be correctly structured or may not exist at the expected path.

The scope is narrow and self-contained: one module (`app.js`) must export a `createApp()` function, and the entry-point (`server.js`) must call it rather than instantiating the app inline. No database migrations, no API contract changes, and no cross-service coordination are required.

A big-bang approach is justified because:
- The change surface is small (2–3 files in `user-management/src/infrastructure/`).
- The existing test suite already asserts the factory interface, providing an immediate regression gate.
- Risk score is low; the upgrade urgency is rated **medium** with no breaking framework changes involved.
- A strangler-fig or parallel-run would add unnecessary complexity for a single-module refactor.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|-------|-------------|--------------|-----------------|
| 1 | Audit existing `app.js` and `server.js` to confirm current structure; document what is inline vs. factory | None | 0.25 person-days |
| 2 | Refactor `app.js` to export `createApp()` factory function; move all middleware and route registration inside the factory | Phase 1 complete | 0.5 person-days |
| 3 | Update `server.js` to call `createApp()` and invoke `app.listen()` separately | Phase 2 complete | 0.25 person-days |
| 4 | Verify all existing tests pass against the new factory; add any missing unit tests for `createApp()` | Phase 3 complete | 0.5 person-days |
| 5 | Code review, merge, and CI gate validation | Phase 4 complete | 0.25 person-days |

**Total estimated effort: ~1.75 person-days** (derived from the "moderate" option estimate for a low-risk, single-service refactor).

---

## Component Changes

### `user-management/src/infrastructure/app.js`

**What changes:**
- The Express app instantiation (`express()`) moves inside a new exported function `createApp()`.
- All middleware registration (authentication, rate limiting, request logging, error handling, schema validation) moves inside `createApp()`.
- All route mounting (via `routes/index.js`) moves inside `createApp()`.
- The function returns the configured `app` instance without calling `app.listen()`.
- The module's top-level scope retains only `require` statements and constants.

**Files affected:**
- `user-management/src/infrastructure/app.js` — primary change target

**API modified:**
- **Before:** `module.exports = app` (or equivalent direct export of an Express instance)
- **After:** `module.exports = { createApp }` — named export of the factory function

**Structural skeleton (target state):**
```js
'use strict';

const express = require('express');
// ... other requires ...

function createApp() {
  const app = express();

  // Middleware registration
  app.use(/* requestLogger */);
  app.use(/* rateLimiter */);
  app.use(express.json());
  // ... other middleware ...

  // Route mounting
  app.use('/api', require('../routes/index'));

  // Error handler (must be last)
  app.use(/* errorHandler */);

  return app;
}

module.exports = { createApp };
```

---

### `user-management/src/infrastructure/server.js` (or `gateway/src/server.js`)

**What changes:**
- Remove any inline `express()` instantiation if it exists here.
- Import `createApp` from `./app`.
- Call `createApp()` to obtain the app instance.
- Call `app.listen(port, callback)` here — this file remains the sole place where the server binds to a port.

**Files affected:**
- `user-management/src/infrastructure/server.js` (path inferred from `AGENTS.md` project structure: `gateway/src/server.js` is the documented entry point; confirm actual path for `user-management`)

**API modified:**
- No public API change; this is an internal structural separation of concerns.

---

### `user-management/src/__tests__/health.test.js`

**What changes:**
- **No changes required.** The test already imports `{ createApp }` from `../infrastructure/app` and calls `createApp()` in `beforeAll`. This file is the acceptance criterion for Phase 4.

**Files affected:** None (read-only reference).

---

### `user-management/src/routes/index.js`, middleware files

**What changes:**
- No structural changes to route or middleware files themselves.
- Confirm that none of these files import the `app` instance directly (which would create a circular dependency). If any do, refactor them to accept `app` as a parameter or use a router pattern.

**Files affected:** Audit only; changes conditional on circular dependency findings.

---

## Dependency Upgrade Plan

N/A — not applicable to this task. No dependency version changes are required. The migration is a structural code refactor within the existing Express 4.x stack. All version numbers remain as documented in `AGENTS.md` (Node.js 20 LTS, Express 4.x).

---

## Infrastructure Changes

N/A — not applicable to this task. The factory pattern refactor is purely a source-code change. No Docker base image changes, Kubernetes manifest changes, CI/CD pipeline changes, or IaC updates are required. The existing `gateway/Dockerfile` and GitHub Actions `ci.yml` pipeline continue to function without modification, as the entry point (`server.js`) and its invocation remain unchanged from the container's perspective.

---

## Rollback Strategy

Each phase is independently reversible because all changes are confined to `app.js` and `server.js`.

| Phase | Rollback Step |
|-------|--------------|
| Phase 1 (audit) | No code changes made; nothing to roll back. |
| Phase 2 (`app.js` refactor) | `git revert` or `git checkout HEAD -- user-management/src/infrastructure/app.js` to restore the previous module export. The server will continue to function if `server.js` has not yet been updated. |
| Phase 3 (`server.js` update) | `git revert` or `git checkout HEAD -- user-management/src/infrastructure/server.js` to restore direct app instantiation. Revert Phase 2 simultaneously to restore a consistent state. |
| Phase 4 (tests) | Remove any newly added test files; existing tests are non-destructive. |
| Phase 5 (merge) | Revert the merge commit on the main branch: `git revert -m 1 <merge-commit-sha>`. CI will re-run against the reverted state. |

**Key invariant:** Because `server.js` is the only file that calls `app.listen()`, rolling back `server.js` alone is sufficient to restore the running service to its previous behaviour without touching routes, middleware, or tests.

---

## Testing Strategy

### Unit Tests
- **Tool:** Jest (as documented in `AGENTS.md`)
- **Target:** `createApp()` in `app.js`
- **What to test:**
  - `createApp()` returns an Express application instance (duck-type check: `typeof app.listen === 'function'`).
  - Calling `createApp()` twice returns two independent instances (factory isolation).
  - The returned app has the expected routes mounted (check `app._router` stack or use Supertest without `listen()`).
- **Coverage target:** 100% of lines in `app.js`.

### Integration Tests
- **Tool:** Jest + Supertest (existing setup)
- **Existing tests that must pass without modification:**
  - `user-management/src/__tests__/health.test.js` — all three test cases (`200 status`, `ISO timestamp`, `Content-Type`) serve as the primary acceptance gate.
- **Additional integration tests to add:**
  - Verify that middleware (e.g., `errorHandler`) is active on the app returned by `createApp()` by triggering a known error route.
  - Verify that routes registered in `routes/index.js` are reachable on the factory-produced app.

### Regression Tests
- **Tool:** Jest with `--runInBand` flag to prevent port conflicts when multiple `createApp()` instances are used in parallel test files.
- **Scope:** Full existing test suite under `user-management/src/__tests__/` and `gateway/tests/`.
- **Gate:** Zero regressions permitted; all pre-existing tests must pass.

### Performance Tests
- N/A for this refactor. The factory pattern adds negligible overhead (one additional function call at startup). No load testing is warranted.

### CI Gate (GitHub Actions `ci.yml`)
- The existing CI pipeline runs `jest` on the `user-management` service.
- **Add/confirm** the following gate in `.github/workflows/ci.yml`:
  ```yaml
  - name: Run user-management tests
    run: npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'
    working-directory: user-management
  ```
- The pipeline must block merge if any test fails or if coverage on `app.js` drops below the target.

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|-----------|-------|---------------------|-------|
| Audit complete; current `app.js` structure documented | Phase 1 | Day 1 — morning | TODO |
| `app.js` exports `createApp()`; all middleware/routes inside factory | Phase 2 | Day 1 — afternoon | TODO |
| `server.js` updated to call `createApp()` + `listen()` | Phase 3 | Day 2 — morning | TODO |
| All existing and new tests passing; coverage gate met | Phase 4 | Day 2 — afternoon | TODO |
| PR reviewed, CI green, merged to main | Phase 5 | Day 3 — morning | TODO |