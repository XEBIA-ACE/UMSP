# Plan: Migrate Flask App to Application Factory Pattern (`create_app()`)

## Overview

**Migration Strategy: Big-Bang (single-branch refactor)**

The task is a structural refactoring of a Node.js/Express application to adopt the application factory pattern — specifically introducing a `create_app()` equivalent (`createApp()`) in the Express gateway layer. Evidence from the provided source code confirms this pattern is **already partially in place**: `user-management/src/__tests__/health.test.js` imports `{ createApp }` from `../infrastructure/app`, and `AGENTS.md` documents `gateway/src/app.js` as "Express app factory (no listen() here)" with `gateway/src/server.js` as the entry point that calls `app.listen()`.

The migration is therefore a **consolidation and verification effort** — ensuring all modules consistently use the factory, removing any direct `app` exports or inline `listen()` calls that bypass the factory, and hardening the pattern across both the `gateway/` and `user-management/` service trees.

A big-bang approach is justified because:
- The risk score is **medium** (upgrade urgency: medium; no runtime or framework version changes required).
- The codebase is small and self-contained within two Node.js service directories.
- The factory pattern is already partially implemented, reducing the blast radius of the change.
- No database migrations, infrastructure changes, or API contract changes are involved.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|-------|-------------|--------------|-----------------|
| 1 | Audit & inventory — identify every file that imports the Express `app` directly, calls `app.listen()`, or exports a bare `app` instance instead of a factory function | None | 0.5 person-days |
| 2 | Implement / harden `createApp()` factory in `user-management/src/infrastructure/app.js` — ensure all middleware, routes, and config are wired inside the factory; no side-effects at module load time | Phase 1 complete | 1 person-day |
| 3 | Implement / harden `createApp()` factory in `gateway/src/app.js` — same constraints; verify `gateway/src/server.js` is the sole caller of `app.listen()` | Phase 1 complete | 1 person-day |
| 4 | Update all test files to instantiate the app via `createApp()` — remove any direct `require('./app')` that returns a live app | Phases 2 & 3 complete | 0.5 person-days |
| 5 | Regression & CI gate — run full test suite, confirm no `listen()` calls outside `server.js` files, merge | Phase 4 complete | 0.5 person-days |

**Total estimated effort: ~3.5 person-days** (derived from the "moderate" option estimate applied to a medium-urgency, low-risk structural refactor).

---

## Component Changes

### `user-management/src/infrastructure/app.js`

**What changes:**
- Must export a named `createApp()` function (not a bare `app` instance).
- All `app.use(...)` middleware registrations, route mounts, and error handler registrations must live **inside** the factory function body.
- No `app.listen()` call inside this file.
- Config/env reads may happen at module scope only if they are side-effect-free (e.g., reading `process.env`); stateful setup (DB connections, Redis clients) must be passed in as arguments or initialised inside the factory.

**Files affected:**
- `user-management/src/infrastructure/app.js` — primary change target
- `user-management/src/__tests__/health.test.js` — already uses `createApp()`; verify import path remains `../infrastructure/app` and no changes needed
- Any other test files under `user-management/src/__tests__/` that import `app` directly — update to use `createApp()`

**API modified:**
- Export signature changes from `module.exports = app` → `module.exports = { createApp }`
- Call sites: `const app = createApp()` replaces `const app = require('./app')`

---

### `gateway/src/app.js`

**What changes:**
- Must export a named `createApp()` function consistent with the pattern documented in `AGENTS.md`.
- Middleware stack (from `gateway/src/middleware/`: `authenticate.js`, `rateLimiter.js`, `requestLogger.js`, `errorHandler.js`, `validateSchema.js`) must be registered inside the factory.
- Route mounting (from `gateway/src/routes/index.js`) must occur inside the factory.
- No `app.listen()` call.

**Files affected:**
- `gateway/src/app.js` — primary change target
- `gateway/src/server.js` — must be the **only** file calling `app.listen()`; verify it calls `createApp()` then `.listen()`
- `gateway/tests/integration/auth.test.js`, `gateway/tests/integration/user.test.js`, `gateway/tests/integration/payment.test.js` — update to import `{ createApp }` and instantiate per test suite

**API modified:**
- Export signature: `module.exports = { createApp }` (or ES module `export { createApp }`)
- `gateway/src/server.js` entry point pattern:
  ```js
  const { createApp } = require('./app');
  const app = createApp();
  app.listen(port, () => { ... });
  ```

---

### `gateway/src/server.js`

**What changes:**
- Must import `createApp` from `./app`.
- Must call `createApp()` to obtain the app instance before calling `.listen()`.
- Must not register any middleware or routes directly.

**Files affected:**
- `gateway/src/server.js`

---

### Test Files (both services)

**What changes:**
- All integration and unit tests that need an Express app instance must call `createApp()` rather than importing a pre-configured singleton.
- `beforeAll` / `beforeEach` hooks instantiate a fresh app per suite, enabling test isolation.

**Files affected:**
- `user-management/src/__tests__/health.test.js` — already correct; verify only
- `gateway/tests/integration/auth.test.js`
- `gateway/tests/integration/user.test.js`
- `gateway/tests/integration/payment.test.js`
- Any unit tests under `gateway/tests/unit/middleware/` and `gateway/tests/unit/controllers/` that import `app`

---

## Dependency Upgrade Plan

N/A — not applicable to this task. This migration involves no dependency version changes. The factory pattern refactor is a structural code change only; Express 4.x, Node.js 20 LTS, and all other dependencies remain at their current versions as documented in `AGENTS.md`.

---

## Infrastructure Changes

N/A — not applicable to this task. No Docker base image changes, Kubernetes manifest changes, CI/CD pipeline changes, or IaC updates are required. The application factory pattern is a source-code-only change. The existing `gateway/Dockerfile` start command (which should invoke `server.js`, not `app.js`) should be verified but not modified unless it currently points to `app.js` directly — TODO: confirm `CMD` in `gateway/Dockerfile` references `server.js`.

---

## Rollback Strategy

Each phase produces an independently revertible Git commit.

| Phase | Rollback Action |
|-------|----------------|
| Phase 1 (audit) | No code changes; discard notes. No rollback needed. |
| Phase 2 (`user-management/src/infrastructure/app.js`) | `git revert <commit>` restoring the previous `module.exports = app` export. Re-run test suite to confirm green. |
| Phase 3 (`gateway/src/app.js` + `server.js`) | `git revert <commit>` restoring the previous export and `server.js` wiring. Re-run test suite to confirm green. |
| Phase 4 (test file updates) | `git revert <commit>` restoring direct `require('./app')` imports in test files. Tests will pass against the reverted Phase 2/3 code. |
| Phase 5 (merge) | Revert the merge commit on the target branch: `git revert -m 1 <merge-commit>`. CI will re-run against the reverted state. |

**Key invariant:** Because `user-management/src/__tests__/health.test.js` already uses `createApp()`, Phase 2 rollback must restore a state where that import still resolves — either keep the factory export or temporarily add a compatibility shim `module.exports.createApp = () => app`.

---

## Testing Strategy

### Unit Tests
- **Tool:** Jest (as documented in `AGENTS.md`)
- **Scope:** Test that `createApp()` returns an Express application instance (`expect(app).toBeDefined()`, `expect(typeof app.listen).toBe('function')`).
- **Scope:** Test that calling `createApp()` twice returns two independent instances (no shared mutable state).
- **Coverage target:** 100% of lines in `app.js` and `server.js` for both services.
- **Location:** `user-management/src/__tests__/`, `gateway/tests/unit/`

### Integration Tests
- **Tool:** Jest + Supertest (as documented in `AGENTS.md`)
- **Scope:** All existing integration tests (`health.test.js`, `auth.test.js`, `user.test.js`, `payment.test.js`) must pass without modification to their assertion logic — only the app instantiation call changes.
- **Pattern:**
  ```js
  const { createApp } = require('../infrastructure/app');
  let app;
  beforeAll(() => { app = createApp(); });
  ```
- **Coverage target:** All existing integration test cases must remain green (zero regression).

### Regression Tests
- **Tool:** Jest with `--ci` flag in GitHub Actions (`ci.yml`)
- **Gate:** PR merge blocked if any test fails or coverage drops below pre-migration baseline.
- **Specific check:** Add a lint/grep CI step that fails if `app.listen` appears in any file other than `gateway/src/server.js` or `user-management/src/infrastructure/server.js`:
  ```bash
  grep -rn "\.listen(" src/ --include="*.js" | grep -v "server.js" && exit 1 || exit 0
  ```

### Performance Tests
N/A — not applicable to this task. The factory pattern introduces no latency-sensitive changes. App startup time is not a CI gate for this refactor.

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|-----------|-------|---------------------|-------|
| Audit complete — all non-factory `app` usages catalogued | Phase 1 | Day 1 | TODO |
| `user-management` factory hardened and tests green | Phase 2 | Day 2 | TODO |
| `gateway` factory hardened, `server.js` verified, tests green | Phase 3 | Day 3 | TODO |
| All test files updated to use `createApp()` | Phase 4 | Day 3 (afternoon) | TODO |
| CI gate passes, no `listen()` outside `server.js`, PR merged | Phase 5 | Day 4 | TODO |