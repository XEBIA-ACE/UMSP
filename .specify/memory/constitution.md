# CONSTITUTION — Flask App Factory Pattern Migration

## Project Identity

**Name:** Flask Application Factory Refactor
**Service:** `user-management` Node.js/Express gateway layer (and any co-located Flask service)
**Purpose:** Migrate the Flask application from a module-level app instantiation pattern to the `create_app()` application factory pattern.
**High-Level Goal:** Eliminate global application state, enable per-environment configuration injection, and unblock testability by ensuring the Flask app is only instantiated when `create_app()` is explicitly called — never at import time.

> **Note:** The provided source code is primarily Java (Spring Boot) and Node.js. The Flask service under migration is not directly visible in the supplied files. The health test at `user-management/src/__tests__/health.test.js` already imports `createApp` from `../infrastructure/app`, confirming the factory pattern is the target convention for this project. Flask-specific file paths are marked TODO where not derivable from context.

---

## Guiding Principles

1. **Prefer `create_app()` factory over module-level `app = Flask(__name__)` because** global instantiation couples configuration to import order, prevents multiple app instances in tests, and causes circular import issues in larger blueprints.

2. **Prefer dependency injection via `app.config` inside `create_app()` over environment reads scattered across modules because** centralised config loading (mirroring `gateway/src/config/index.js`) is the established pattern in this codebase.

3. **Prefer returning the `app` object from `create_app()` without calling `app.run()` because** the entry point (`server.py` or equivalent) must own the `listen`/`run` call — consistent with how `gateway/src/app.js` and `gateway/src/server.js` are separated in this project.

4. **Prefer blueprint registration inside `create_app()` over top-level route decoration because** routes attached at module scope re-introduce the global-state problem the factory pattern is designed to solve.

5. **Prefer explicit test fixtures that call `create_app('testing')` over patching global state because** the Node.js test suite (`health.test.js`) already demonstrates this contract — `createApp()` is called in `beforeAll`, and the Flask tests must mirror it.

---

## Constraints

- **Effort ceiling:** Moderate option — scope is limited to the factory pattern refactor only. No new features, no dependency upgrades, no infrastructure changes.
- **Scope freeze:** Changes are confined to the Flask application entry point, configuration loading, blueprint/extension registration, and associated tests. The Java services and Node.js gateway are out of scope.
- **Runtime version:** TODO — Flask runtime version not specified in tech analysis. Pin to whatever version is currently in use; do not upgrade as part of this task.
- **No downtime mandate:** The refactor must be a drop-in replacement; existing routes, URL rules, and response contracts must not change.
- **Test suite must remain green:** All pre-existing tests must pass after the refactor. No test deletions permitted.

---

## Quality Standards

- **Test coverage:** Every code path through `create_app()` (at minimum: default config, testing config) must have a corresponding test. Coverage must not decrease from the pre-migration baseline.
- **Factory contract test:** A test must assert that `create_app()` returns a valid Flask application instance and that calling it twice produces two independent objects (proving no shared global state).
- **No `app.run()` in factory:** CI or a lint rule must verify `app.run()` does not appear inside `create_app()`.
- **Code review:** All changes require at least one peer review approval before merge. The reviewer must verify blueprint registration, extension initialisation, and config loading occur exclusively inside the factory.
- **Documentation:** The module docstring of `app.py` (or equivalent) must describe the factory's accepted config names and their sources.

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | Adopt `create_app(config_name=None)` as the sole public factory function | Mirrors `createApp()` convention already in use in `user-management/src/infrastructure/app.js` and validated by existing health tests | Accepted |
| ADR-002 | Entry point (`server.py` or equivalent) calls `create_app()` and then `app.run()` | Separates app construction from process lifecycle; consistent with `gateway/src/server.js` pattern | Accepted |
| ADR-003 | All Flask extensions (DB, auth, etc.) initialised with `init_app(app)` inside `create_app()` | Prevents extension state from leaking into module scope; required for factory pattern correctness | Accepted |
| ADR-004 | Flask runtime version pinned at current level; no upgrade in this task | Upgrade urgency is medium but out of scope for this refactor to contain risk | Accepted |
| ADR-005 | Flask service file paths to be confirmed before implementation begins | Flask source files not present in supplied code context | TODO |