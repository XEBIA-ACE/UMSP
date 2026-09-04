# Spec: Migrate Flask App to Application Factory Pattern (`create_app()`)

## Summary

This spec covers the migration of the Node.js/Express user-management service's application bootstrap from a direct, module-level app instantiation pattern to an explicit application factory function (`createApp()`). The expected outcome is that the Express `app` object is no longer created at module import time; instead, it is produced on demand by calling `createApp()`, enabling isolated test instances, multiple environment configurations, and clean separation between app construction and server startup.

## Motivation

**Technical drivers:**

- The existing test suite (`user-management/src/__tests__/health.test.js`) already imports and calls `createApp()` from `src/infrastructure/app`, indicating that the factory pattern is the intended contract but may not be consistently implemented or enforced across the codebase.
- Module-level app instantiation causes side effects at `require()` time (middleware registration, route mounting, database connections), making unit and integration tests fragile and order-dependent.
- Without a factory, it is impossible to create multiple isolated app instances in the same process — a requirement for parallel test suites and multi-tenant or multi-config scenarios.
- The `gateway/src/app.js` file in the project structure is already documented as "Express app factory (no `listen()` here)", confirming the architectural intent that app construction and server binding must be separated. The user-management service must be brought into alignment with this established pattern.

**Upgrade urgency:** Medium — the test infrastructure already depends on `createApp()`, so any divergence between the expected and actual export creates test failures and blocks CI.

## Current State

Based on the provided source context, the following elements are relevant to the current bootstrap behaviour:

- **`user-management/src/__tests__/health.test.js`** imports `createApp` from `'../infrastructure/app'` and calls it in `beforeAll`. This is the canonical consumer of the factory and defines the required export contract.
- **`gateway/src/app.js`** (referenced in `AGENTS.md`) is documented as the Express app factory with no `listen()` call; `gateway/src/server.js` is the entry point that calls `app.listen()`. This is the reference architecture the user-management service must match.
- The user-management service's equivalent of `app.js` and `server.js` are not provided in full source context; their exact current implementation is **TODO** (not supplied).
- Use cases (`RegisterUser`, `LoginUser`, `RecoverPassword`, `VerifyAccount`) are constructed with dependency injection via plain constructors — they have no framework coupling and are unaffected by the factory migration.
- The `AGENTS.md` project structure lists `gateway/src/app.js` and `gateway/src/server.js` as the separation point for the gateway service; the equivalent files for `user-management` are not explicitly listed, suggesting they may be absent or non-conformant.

**Key behaviours affected:**

| Element | Current Behaviour |
|---|---|
| `user-management/src/infrastructure/app.js` | TODO — exact export shape not confirmed in provided context |
| `user-management/src/server.js` (or equivalent) | TODO — whether `listen()` is called inside `app.js` or a separate entry point is not confirmed |
| Test bootstrap (`health.test.js`) | Calls `createApp()` — this is the required interface |

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| `user-management/src/infrastructure/app.js` | App may be instantiated at module load time and exported as a configured instance | Exports a named `createApp()` function that constructs and returns a fully configured Express app without calling `listen()` | Y — callers that import the app instance directly must switch to calling `createApp()` |
| `user-management/src/server.js` (entry point) | May call `app.listen()` inside `app.js` or lack a dedicated entry point | Imports `createApp()`, calls it to obtain the app instance, then calls `app.listen()` with the configured port | N — internal change to entry point only |
| Middleware registration | Registered at module load time as a side effect of `require()` | Registered inside `createApp()` body, executed only when the factory is called | N — behaviour is identical; timing is deferred |
| Route mounting | Mounted at module load time | Mounted inside `createApp()` | N — behaviour is identical |
| Test files (`health.test.js` and any others) | Already call `createApp()` — no change required if the factory is correctly implemented | No change required | N |

**What is removed:**
- Any top-level, module-scope `const app = express()` statement in `app.js` that causes side effects on `require()`.
- Any `app.listen()` call inside `app.js`.

**What is added:**
- A named export `createApp()` (or `module.exports = { createApp }`) in `user-management/src/infrastructure/app.js`.
- A dedicated `server.js` (or equivalent entry point) that calls `createApp()` and then `listen()`.

## Compatibility & Breaking Changes

| Breaking Change | Affected Callers | Migration Path |
|---|---|---|
| `app.js` no longer exports a pre-built app instance | Any module that does `require('./infrastructure/app')` and uses the result directly as an Express app | Update the import to destructure or call `createApp()`: replace direct usage of the exported object with the return value of `createApp()` |
| `listen()` removed from `app.js` | The process entry point (e.g. `index.js` or `server.js`) | Move the `app.listen(port, callback)` call into the dedicated server entry point file |
| Any global state initialised at `require()` time (e.g. middleware with shared mutable state) | Integration tests that rely on shared state between test cases | Each test suite must call `createApp()` independently to obtain a fresh instance; shared state must be passed as configuration parameters to `createApp()` |
| TODO: Whether `user-management` currently exports a singleton app instance | TODO — confirm by inspecting actual `app.js` source | TODO |

## Acceptance Criteria

1. **Given** the `user-management/src/infrastructure/app.js` module is loaded via `require()`, **when** no call to `createApp()` is made, **then** no Express middleware is registered, no routes are mounted, and no side effects occur (verified by asserting that the module export is a function, not an Express app instance).

2. **Given** `createApp()` is called, **when** the returned value is inspected, **then** it is a valid Express application object (i.e. it is a function with `listen`, `use`, and `get` properties).

3. **Given** `createApp()` is called twice in the same process, **when** both returned app instances are used independently, **then** middleware or route changes applied to one instance do not affect the other (verified by mounting a test-only route on one instance and asserting it returns 404 on the other).

4. **Given** the health test suite in `user-management/src/__tests__/health.test.js` is executed, **when** `createApp()` is called in `beforeAll`, **then** `GET /api/health` returns HTTP 200 with `{ status: "ok", service: "user-management" }` and a valid ISO timestamp, and all three existing health tests pass without modification.

5. **Given** the server entry point (`server.js` or equivalent) is started, **when** the process launches, **then** `createApp()` is called exactly once and `app.listen()` is called on the returned instance using the configured port from environment or config.

6. **Given** `createApp()` is called, **when** a `POST /api/auth/register` request is submitted with a valid body, **then** the response status is not 404 (confirming that all routes are mounted inside the factory and are reachable on a freshly created instance).

7. **Given** the CI pipeline runs, **when** the full Jest test suite for `user-management` executes, **then** all tests pass with zero failures attributable to app instantiation order or shared state between test files.

8. **Given** `createApp()` is called without any arguments, **when** the app handles a request to an unregistered route, **then** it returns HTTP 404 (confirming that the default Express not-found behaviour is intact and no unintended catch-all route is registered).

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | What is the exact current export shape of `user-management/src/infrastructure/app.js`? Is it already a factory, a singleton instance, or absent? | TODO | TODO |
| 2 | Does a dedicated `server.js` entry point already exist for the user-management service, or does `app.js` currently call `listen()`? | TODO | TODO |
| 3 | Are there any callers outside of test files that import the app object directly (e.g. `docker-compose` health check scripts, other services)? | TODO | TODO |
| 4 | Should `createApp()` accept a configuration object parameter (e.g. for injecting test doubles for repositories and services), or should it always read from the environment? | TODO | TODO |
| 5 | Are there any other test files in `user-management/src/__tests__/` beyond `health.test.js` that bootstrap the app and would be affected by this change? | TODO | TODO |
| 6 | The task title references "Flask" but the codebase is Node.js/Express. Should this spec apply to a Flask service not present in the provided context, or is the title a mislabelling? | TODO | TODO |