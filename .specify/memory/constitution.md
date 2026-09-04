# CONSTITUTION — SQLAlchemy Query API → 2.0 `select()` Migration

## Project Identity

**Name:** SQLAlchemy 2.0 Query API Migration
**Purpose:** Eliminate all usage of the legacy SQLAlchemy `Query` API (1.x style: `session.query(...)`) and replace every call site with the SQLAlchemy 2.0 `select()` / `Session.execute()` style.
**High-level goal:** Achieve a codebase that is fully compatible with SQLAlchemy 2.0's new query interface, removing reliance on the legacy API that is removed in 2.0, thereby eliminating the associated deprecation warnings and future EOL risk.

> **Note:** The source code provided is a Java/Node.js payment service with no Python or SQLAlchemy present. The migration target (SQLAlchemy call sites) is not visible in the supplied files. All SQLAlchemy-specific constraints below apply to the Python codebase that contains the legacy Query API calls. TODO: Identify and link the actual Python source files containing `session.query()` usage before work begins.

---

## Guiding Principles

1. **Prefer `select()` + `session.execute()` over `session.query()` because** the legacy `Query` API is a compatibility shim in SQLAlchemy 1.4 and is fully removed in 2.0; retaining it blocks any future upgrade to 2.0+.
2. **Prefer mechanical, call-site-by-call-site replacement over architectural refactoring because** the task scope is a targeted API migration, not a redesign; unrelated changes increase risk and review burden.
3. **Prefer running the existing test suite as the primary correctness gate over writing new tests because** the migration must not change observable behaviour; passing tests confirm semantic equivalence.
4. **Prefer explicit `scalars()` / `scalar_one()` / `all()` result unwrapping over implicit row access because** SQLAlchemy 2.0 `execute()` returns `CursorResult` rows, not ORM objects directly; incorrect unwrapping is the most common migration defect.
5. **Prefer a single-pass, file-by-file migration over a feature-flag or dual-path approach because** the legacy and 2.0 APIs cannot safely coexist in the same session context once `future=True` is set.

---

## Constraints

- **Effort ceiling:** The upgrade option is described as "moderate" with no explicit person-days figure. TODO: Confirm effort ceiling with project lead before sprint planning.
- **SQLAlchemy version target:** All migrated code must be compatible with SQLAlchemy 2.0.x. The `future=True` engine flag (1.4 compatibility bridge) must be enabled during migration and removed upon completion.
- **No ORM model changes:** Entity/model class definitions (`Base`, `Column`, `relationship`) are out of scope. Only query call sites are in scope.
- **No database schema changes:** Flyway migrations or schema alterations are strictly out of scope.
- **Python runtime:** TODO — confirm Python version in use (3.8+ required for SQLAlchemy 2.0).
- **Zero breaking changes to public interfaces:** All repository method signatures and return types must remain identical after migration.
- **CI must stay green throughout:** No PR may be merged if the existing test suite regresses.

---

## Quality Standards

- **Test coverage floor:** Line coverage on all modified repository/query files must not drop below its pre-migration baseline. TODO: Record baseline before first change.
- **Deprecation-warning-free:** After migration, running the test suite with `SQLALCHEMY_WARN_20=1` must produce zero SQLAlchemy legacy-API deprecation warnings.
- **Code review:** Every changed file requires at least one reviewer who has read the [SQLAlchemy 2.0 migration guide](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html).
- **Automated lint gate:** A `grep`-based CI check (or `pylint` rule) must be added to the pipeline that fails the build if `session.query(` appears in any `.py` file under the source root.
- **Documentation:** Each PR description must include a before/after diff excerpt for at least one representative query change.

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | Migrate all `session.query()` calls to `select()` + `session.execute()` | Legacy `Query` API removed in SQLAlchemy 2.0; migration is required to eliminate EOL risk | Accepted |
| ADR-002 | Enable `future=True` on the SQLAlchemy engine as the first step | Activates 2.0-style behaviour and surfaces all remaining legacy usages as warnings in 1.4, enabling incremental migration | Accepted |
| ADR-003 | Add a CI grep gate blocking re-introduction of `session.query(` | Prevents regression once migration is complete | Accepted |
| ADR-004 | Keep ORM model definitions unchanged | Model layer is not the source of the legacy API usage; changing it is out of scope and increases risk | Accepted |
| ADR-005 | Python runtime version | TODO — confirm minimum Python version before migration begins | Proposed |