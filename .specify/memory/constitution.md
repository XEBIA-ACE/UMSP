# CONSTITUTION — SQLAlchemy Query API → 2.0 `select()` Migration

## Project Identity

**Name:** SQLAlchemy 2.0 Query API Migration
**Purpose:** Eliminate all usage of the legacy SQLAlchemy `Query` API (1.x style: `session.query(...)`) and replace every call site with the SQLAlchemy 2.0 `select()` / `Session.execute()` style.
**High-level goal:** Achieve a codebase that runs cleanly under SQLAlchemy 2.0 with no legacy query patterns, no deprecation warnings, and no reliance on the removed `Query` object interface.

> **Note:** The source repository provided describes a Java/Node.js payment service with no Python or SQLAlchemy code visible. The migration target files are not present in the supplied context. All file-level specifics are marked TODO pending codebase access.

---

## Guiding Principles

1. **Prefer `select()` + `session.execute()` over `session.query()` everywhere** because the `Query` API is a legacy interface removed in SQLAlchemy 2.0 and continued use blocks the upgrade path.
2. **Prefer targeted, call-site-by-call-site rewrites over bulk automated replacement** because Query API semantics (e.g., `.first()`, `.one_or_none()`, `.all()`) do not map 1-to-1 to `execute()` result methods and incorrect substitution introduces silent data bugs.
3. **Prefer preserving existing test coverage as a regression harness over rewriting tests first** because the existing tests define the correct query behaviour and must stay green throughout the migration.
4. **Prefer explicit `scalars()` / `scalar_one_or_none()` / `mappings()` result accessors over raw `execute()` returns** because SQLAlchemy 2.0 `execute()` returns a `CursorResult` and callers must explicitly unwrap rows to avoid type errors.
5. **Prefer incremental module-by-module migration over a single large-bang change** because smaller changesets reduce review risk and allow CI to catch regressions at each step.
6. **Prefer removing `SQLALCHEMY_WARN_20` suppression flags as a completion gate** because the presence of that flag masks remaining legacy usage and its removal confirms full 2.0 compliance.

---

## Constraints

- **Timeline / effort:** TODO — person-days estimate not provided in the upgrade option ("moderate" option selected but details absent). Effort ceiling to be confirmed before work begins.
- **SQLAlchemy version mandate:** Target is SQLAlchemy ≥ 2.0.x. No code may use the `Query` object or any API gated behind `legacy_query_interface` after migration is complete.
- **Python runtime:** TODO — runtime version not specified in tech analysis. Must be confirmed; SQLAlchemy 2.0 requires Python ≥ 3.7.
- **No breaking changes to public interfaces:** Repository method signatures and return types visible to callers must remain behaviourally identical after migration.
- **Scope freeze:** This migration is limited to SQLAlchemy query-style changes only. ORM model definitions, schema changes, and Alembic/Flyway migrations are out of scope unless directly required by the query rewrite.
- **CI must stay green throughout:** No PR may be merged with a failing test suite.

---

## Quality Standards

- **Test coverage floor:** Line coverage on all repository/data-access modules must not decrease below its pre-migration baseline. TODO — establish baseline percentage before first PR.
- **Zero deprecation warnings:** `python -W error::DeprecationWarning` (or equivalent pytest flag) must produce no SQLAlchemy-related warnings in CI after each module is migrated.
- **Code review:** Every changed file requires at least one reviewer with SQLAlchemy 2.0 familiarity before merge.
- **Regression gate:** The full existing test suite (unit + integration) must pass on every PR. Integration tests must run against a real database (not mocks) to catch ORM-level query errors.
- **Migration completeness check:** A grep/AST scan for `session.query(` and `Query` imports must return zero results before the migration is declared done.
- **Documentation:** Each repository class touched must have its docstring updated to reflect 2.0-style usage.

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | Adopt SQLAlchemy 2.0 `select()` + `session.execute()` as the sole query pattern | Removes dependency on the removed `Query` API; aligns with upstream SQLAlchemy 2.0 design | Accepted |
| ADR-002 | Migrate module-by-module rather than in a single commit | Reduces blast radius; keeps CI green incrementally; easier to review | Accepted |
| ADR-003 | Use `SQLALCHEMY_WARN_20=1` during migration as a detection tool, then remove it at completion | Surfaces remaining legacy calls without breaking the build mid-migration | Accepted |
| ADR-004 | Keep ORM models and schema definitions unchanged | Scope is query-style only; model changes are a separate concern and out of scope | Accepted |
| ADR-005 | Python runtime version | TODO — must be confirmed before migration begins; SQLAlchemy 2.0 minimum is Python 3.7 | Proposed |