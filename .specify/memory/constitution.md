# CONSTITUTION — Replace unittest with pytest and Add Fixture-Based DB Isolation

## Project Identity

**Name:** user-management-service — Test Framework Migration  
**Purpose:** Migrate the `user-management` Node.js service's test suite from its current setup to pytest with fixture-based database isolation.  
**High-level goal:** Replace the existing Jest/unittest-style test patterns with pytest conventions and introduce fixture-based DB isolation so that each test runs against a clean, isolated data state — eliminating inter-test contamination and improving reliability.

> **Note:** The source code shows a Node.js service using Jest (`jest@^29.7.0`) and a Java service using JUnit 5. The task references "unittest → pytest", which implies a Python context. However, no Python runtime, files, or dependencies are present in the provided codebase. The most defensible interpretation is that this migration targets the **Node.js `user-management` service**, replacing Jest-based patterns with a more structured fixture/isolation approach. If a Python service exists outside the provided context, **TODO: identify the target Python service and its current test files before proceeding.**

---

## Guiding Principles

1. **Prefer fixture-scoped DB state over shared mutable state** because the current `InMemoryUserRepository` is instantiated once and bleeds state across tests, causing order-dependent failures.
2. **Prefer explicit setup/teardown fixtures over `beforeEach` imperative blocks** because scattered setup logic in test files makes isolation guarantees implicit and fragile.
3. **Prefer migrating tests incrementally (file by file) over a big-bang rewrite** because the upgrade option is "moderate" effort — partial coverage is safer than a broken suite mid-migration.
4. **Prefer keeping domain and application logic untouched** because this task is scoped to the test layer only; no production code changes are in scope.
5. **Prefer in-process DB fakes (e.g. `InMemoryUserRepository` reset per fixture) over live DB containers for unit tests** because the service currently has no real DB adapter wired — introducing Testcontainers is out of scope unless explicitly added to the upgrade option.

---

## Constraints

- **Effort ceiling:** Moderate (exact person-days not specified — TODO: confirm with project lead before sprint planning).
- **Scope freeze:** Production source code (`src/` outside `__tests__`) must not be modified as part of this migration.
- **Runtime mandate:** Node.js 20 LTS (as declared in `README.md` and `AGENTS.md`); no runtime upgrade is in scope.
- **Dependency constraint:** TODO — if target is Node.js/Jest, confirm whether "pytest" is a metaphor for a Jest fixture pattern or whether a Python service is the actual target. Do not add Python tooling to the Node.js service.
- **No new external services:** DB isolation must be achieved via fixture resets of existing in-memory adapters or test doubles — no new infrastructure (e.g. Docker, Postgres) unless the upgrade option explicitly funds it.
- **CI must remain green:** The GitHub Actions pipeline (`ci.yml`) must pass after migration; no regression in existing passing tests is acceptable.

---

## Quality Standards

- **Coverage floor:** Test coverage must not drop below the pre-migration baseline. The existing `jest --coverage` gate must be preserved (or its equivalent in the target framework).
- **Isolation gate:** Every test that touches repository state must use a fixture that resets the store; no test may rely on state created by a prior test. Verified by running tests in randomised order and confirming no failures.
- **Code review:** All fixture definitions must be reviewed by at least one other contributor before merge.
- **Documentation:** A `TESTING.md` (or equivalent section in `README.md`) must document how to run the suite, what fixtures are available, and how to add a new fixture-isolated test.
- **No skipped tests:** Tests may not be marked skip/pending as a migration shortcut; any test that cannot be migrated must be documented with a TODO and a tracking issue.
- **Deployment gate:** Migration PR must pass CI (lint + full test suite) before merge to `main`.

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | Fixture-based DB isolation via per-test repository reset | `InMemoryUserRepository` uses a `Map` that persists across tests; resetting it in a fixture is the lowest-risk isolation strategy given no real DB is wired | Accepted |
| ADR-002 | Production code is out of scope for this migration | Task description explicitly limits changes to the test framework layer | Accepted |
| ADR-003 | Target runtime remains Node.js 20 / Jest ecosystem (pending Python service confirmation) | No Python files or runtime are present in the provided codebase; TODO: confirm if a Python service is the actual target | Proposed |
| ADR-004 | Incremental file-by-file migration over big-bang rewrite | Moderate effort ceiling requires a safe, reviewable rollout that keeps CI green throughout | Accepted |