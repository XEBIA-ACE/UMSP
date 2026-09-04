# Spec: Migrate Flask App to Application Factory Pattern (`create_app()`)

## Summary

This spec covers the migration of the Node.js/Express user-management service's application bootstrap from a direct, module-level app instantiation pattern to an explicit application factory function (`createApp()`). The expected outcome is that the Express application object is constructed and configured inside a dedicated factory function, while the entry-point module (`server.js`) is solely responsible for calling `app.listen()`. This separation enables test suites to instantiate isolated application instances without side effects and aligns the gateway layer with the factory pattern already in use in `user-management/src/infrastructure/app.js` (as evidenced by the existing test imports of `createApp`).

---

## Motivation

- **Testability debt (medium urgency):** The existing test file `user-management/src/__tests__/health.test.js` already imports `createApp` from `src/infrastructure/app.js`, indicating that the factory pattern is partially expected but may not be consistently enforced across the codebase. Any module that instantiates the Express app at import time (i.e., outside a factory function) causes the HTTP server to bind or middleware to register as a side effect of `require()`, making isolated unit and integration testing unreliable.
- **Separation of concerns:** Mixing application construction with server startup in a single module prevents reuse of the configured app object across test runners, multiple server instances, or future serverless adapters.
- **Consistency with established patterns:** The `AGENTS.md` project structure explicitly lists `gateway/src/app.js` as an "Express app factory (no listen() here)" and `gateway/src/server.js` as the "Entry point — calls app.listen()". The user-management service must conform to the same structural contract.
- **No EOL or CVE driver identified** in the provided tech analysis for this specific change; the urgency is classified as **medium** based on tech debt.

---

## Current State

Based on the provided source context, the following elements are relevant:

| Element | Location | Current Behaviour |
|---|---|---|
| `createApp()` factory | `user-management/src/infrastructure/app.js` | Already imported by `health.test.js`; actual implementation not provided in context — TODO: confirm whether factory is fully implemented or partially stubbed |
| Health test bootstrap | `user-management/src/__tests__/health.test.js` | Calls `createApp()` in `beforeAll` and passes the result to `supertest` — confirms the factory interface is the expected contract |
| Entry point | `user-management/src/server.js` (referenced in `AGENTS.md`) | Expected to call `app.listen()`; actual implementation not provided in context — TODO: confirm whether `listen()` is currently co-located with app construction |
| Middleware registration | `user-management/src/` (authenticate, rateLimiter, requestLogger, errorHandler, validateSchema per `AGENTS.md`) | Currently registered somewhere during app startup; must be registered inside `createApp()` after migration |
| Route mounting | `user-management/src/routes/index.js` (per `AGENTS.md`) | Mounts auth, user, and payment routers; must be mounted inside `createApp()` after migration |

**Key interfaces consumed by callers:**

- `createApp()` → returns a configured Express `app` object (no `listen()` call).
- `server.js` → calls `app.listen(port, callback)` using the value returned by `createApp()`.
- Test files → call `createApp()` directly and pass the result to `supertest(app)`.

---

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| `user-management/src/infrastructure/app.js` | App construction behaviour unknown / potentially mixed with side effects | Exports a single `createApp()` function that constructs, configures, and returns the Express app without calling `listen()` | N — interface already expected by tests |
| `user-management/src/server.js` | Entry point; current relationship to `app.js` unknown (TODO) | Imports `createApp()`, invokes it, then calls `app.listen()` on the returned instance | N — internal restructuring only |
| Middleware registration (authenticate, rateLimiter, requestLogger, errorHandler, validateSchema) | Registered at module load time or in an unknown location | Registered inside `createApp()` body, in the correct order, before routes are mounted | N |
| Route mounting (`routes/index.js`) | Mounted at module load time or in an unknown location | Mounted inside `createApp()` after middleware registration | N |
| Test files (`health.test.js` and any future integration tests) | Already call `createApp()` in `beforeAll` | No change required to test structure; tests continue to call `createApp()` | N |

**What is removed:**
- Any top-level, module-scope Express app instantiation outside of `createApp()`.
- Any `app.listen()` call inside `app.js` or any non-entry-point module.

**What is added:**
- A clearly defined, exported `createApp()` function in `user-management/src/infrastructure/app.js`.
- Optional: acceptance of a configuration object parameter in `createApp(config)` to support environment-specific overrides in tests (TODO: confirm whether this is required).

---

## Compatibility & Breaking Changes

| Change | Impact on Callers | Migration Path |
|---|---|---|
| `createApp()` becomes the sole export of `app.js` | Any caller that previously imported the app instance directly (e.g., `const app = require('./app')`) will receive `undefined` or a function instead of an app object | Update all such import sites to call `createApp()` and use the returned value |
| `listen()` removed from `app.js` | Any process that relied on `require('./app')` to start the server as a side effect will no longer bind a port | Ensure `server.js` is the sole entry point used to start the HTTP server |
| Middleware/route registration moved inside factory | No external callers are affected; this is an internal restructuring | N/A — no migration required for external callers |
| TODO: If `app.js` currently exports the app instance directly | Callers in other test files not yet identified in context | TODO — audit all `require`/`import` references to `app.js` across the repository before migration |

---

## Acceptance Criteria

1. **Given** the `user-management` service source, **when** `app.js` is imported as a module, **then** the module's default export is a callable function named `createApp` and no Express server is bound to any port as a side effect of the import.

2. **Given** a call to `createApp()` with no arguments, **when** the function returns, **then** the returned value is a configured Express application object with all middleware (authentication, rate limiter, request logger, error handler, schema validation) and all routes (`/auth/*`, `/users/*`, `/payments/*`, `/api/health`) registered and ready to handle requests.

3. **Given** the existing `health.test.js` test suite, **when** the full Jest test run executes, **then** all three health endpoint tests (`200 status`, `valid ISO timestamp`, `Content-Type application/json`) pass without modification to the test file.

4. **Given** `server.js` is executed as the application entry point, **when** the process starts, **then** `createApp()` is called exactly once and `app.listen()` is called on the returned instance, binding the server to the configured port.

5. **Given** two sequential calls to `createApp()` within the same test process, **when** both returned app instances are passed to `supertest`, **then** each instance handles requests independently without shared mutable state between them (i.e., middleware or route registration on one instance does not affect the other).

6. **Given** the CI pipeline runs the full test suite, **when** all tests complete, **then** zero tests fail and no test produces an `EADDRINUSE` error caused by the app binding a port during module import.

7. **Given** `app.js` is imported in a test environment, **when** no `listen()` is called, **then** no open handle warning is reported by Jest's `--detectOpenHandles` flag.

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | Does `user-management/src/infrastructure/app.js` currently export a `createApp` function, or does it export a bare app instance? The test already imports `createApp`, but the implementation file was not provided in context. | TODO | TODO |
| 2 | Does `user-management/src/server.js` currently call `app.listen()` separately from `app.js`, or are construction and startup co-located in one file? | TODO | TODO |
| 3 | Should `createApp()` accept a configuration parameter (e.g., for injecting test-specific config overrides such as a mock Redis client or disabled rate limiting)? | TODO | TODO |
| 4 | Are there any other files in the repository (outside the provided context) that import the Express app object directly from `app.js` and would be broken by changing the export to a factory function? A full import audit is required before implementation. | TODO | TODO |
| 5 | The task title references "Flask" but the codebase is Node.js/Express. Should this spec apply to a Python Flask service not present in the provided context, or is the title a mislabelling? | TODO | TODO |