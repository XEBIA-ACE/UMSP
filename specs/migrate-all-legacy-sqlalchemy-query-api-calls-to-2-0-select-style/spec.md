# Spec: Migrate Legacy SQLAlchemy Query API Calls to 2.0 `select()` Style

## Summary

This spec covers the migration of all legacy SQLAlchemy Query API (`session.query(...)`) call sites to the SQLAlchemy 2.0 `select()`-based Core/ORM style. The expected outcome is that no `session.query()` usage remains in the codebase, all data-access operations use the 2.0-compatible `select()`, `insert()`, `update()`, and `delete()` constructs executed via `session.execute()`, and the codebase is fully compatible with SQLAlchemy 2.0's strict mode with legacy query emission disabled.

## Motivation

- **SQLAlchemy 2.0 Legacy Query API removal:** The `Session.query()` interface was formally deprecated in SQLAlchemy 1.4 and removed in SQLAlchemy 2.0. Continued use of the legacy API blocks any upgrade to SQLAlchemy 2.0+.
- **Upgrade urgency:** Medium — the legacy API is not receiving new features or bug fixes; remaining on SQLAlchemy 1.x exposes the project to unpatched vulnerabilities as the 1.x line approaches end-of-active-maintenance.
- **Tech debt:** The legacy Query API is tightly coupled to the ORM session in ways that make query composition, async support, and unit-of-work patterns harder to reason about. The 2.0 `select()` style aligns with the Core expression language, enabling consistent patterns across ORM and Core queries.
- **Future-proofing:** Adopting 2.0-style queries is a prerequisite for any future migration to async SQLAlchemy (`AsyncSession`) or SQLAlchemy 2.x minor upgrades.

> **Note:** The provided source context describes a Java/Spring Boot + Node.js/Express codebase. No Python or SQLAlchemy source files were included. All interface, class, and schema references below are marked TODO pending access to the actual Python data-access layer.

## Current State

N/A — not applicable to this task in the provided source context. The repository described in the context (Java 21 / Spring Boot 3.x / Spring Data JPA / Node.js 20 / Express 4.x) contains no SQLAlchemy or Python components. The specific classes, repository methods, query call sites, and ORM model definitions subject to this migration are absent from the provided code.

| Artefact | Description | Status |
|---|---|---|
| Repository classes | Python classes using `session.query(Model)` | TODO — not in provided context |
| ORM model definitions | SQLAlchemy `DeclarativeBase` / `Base` subclasses | TODO — not in provided context |
| Session factory / config | `sessionmaker` / `scoped_session` setup | TODO — not in provided context |
| Filter/order call sites | `.filter()`, `.filter_by()`, `.order_by()`, `.first()`, `.all()` | TODO — not in provided context |
| Scalar/aggregate queries | `.count()`, `.scalar()` via legacy Query | TODO — not in provided context |

## Proposed Changes

For each repository or data-access module containing `session.query()` calls, the following transformation applies:

| Component | Before | After | Breaking? |
|---|---|---|---|
| All repository `find_*` methods | `session.query(Model).filter(...)` | `session.execute(select(Model).where(...))` | N |
| Single-row fetch | `.first()` / `.one()` on Query | `.scalars().first()` / `.scalar_one()` on `Result` | N |
| Multi-row fetch | `.all()` on Query | `.scalars().all()` on `Result` | N |
| Count queries | `session.query(func.count(...))` | `session.execute(select(func.count(...)))` | N |
| Existence checks | `session.query(Model).filter(...).first() is not None` | `session.execute(select(Model).where(...)).scalar_one_or_none() is not None` | N |
| Bulk update/delete | `session.query(Model).filter(...).update(...)` / `.delete(...)` | `session.execute(update(Model).where(...).values(...))` / `session.execute(delete(Model).where(...))` | N |
| Session import surface | `from sqlalchemy.orm import Query` (implicit) | `from sqlalchemy import select, update, delete, insert` | N |
| SQLAlchemy version pin | TODO — current version unknown | TODO — target version unknown (≥ 2.0 recommended) | TODO |

> All component names, file paths, and method signatures are TODO pending access to the actual Python source files.

## Compatibility & Breaking Changes

| Change | Impact on Callers | Migration Path |
|---|---|---|
| `.all()` returns `list[Row]` instead of `list[Model]` when using `select(Model)` without `.scalars()` | Callers accessing row attributes directly may break | Ensure `.scalars().all()` is used when a `list[Model]` is expected; update callers that unpack `Row` tuples |
| `.first()` on `Result` vs Query | `Result.first()` returns a `Row` or `None`; `Result.scalars().first()` returns a model instance or `None` | Replace `.first()` with `.scalars().first()` at all ORM entity fetch sites |
| `Query.count()` removed | Any caller invoking `.count()` on a Query object | Replace with `session.execute(select(func.count()).select_from(Model).where(...)).scalar()` |
| `Query.update()` / `Query.delete()` removed | Bulk mutation callers | Replace with `session.execute(update(Model).where(...).values(...))` and `session.execute(delete(Model).where(...))` |
| `session.query(Model, OtherModel)` multi-entity joins | Callers unpacking tuples from joined queries | Replace with explicit `select(Model, OtherModel).join(...)` and unpack `Row` results accordingly |
| SQLAlchemy version upgrade (if applicable) | All ORM-dependent code | TODO — confirm current pinned version and target version; run full test suite under 2.0 with `SQLALCHEMY_WARN_20=1` flag first |
| `relationship` lazy loading behaviour | May differ under 2.0 strict mode | TODO — audit all `relationship()` definitions for `lazy=` setting; enable `lazy="raise"` in tests to surface implicit loads |

## Acceptance Criteria

1. **Given** the codebase is scanned for legacy Query API usage, **when** a static analysis check (e.g. `grep` for `session.query(` or a custom AST lint rule) is run in CI, **then** zero occurrences of `session.query(` are reported across all Python source files.

2. **Given** the SQLAlchemy version is set to 2.0 or later (or 1.4 with `future=True` on the engine), **when** the full unit and integration test suite is executed, **then** all tests pass with no `LegacyAPIWarning` or `RemovedIn20Warning` warnings emitted.

3. **Given** a repository method previously implemented with `session.query(Model).filter_by(id=x).first()`, **when** the migrated method is called with a valid `id`, **then** it returns the same model instance as the legacy implementation returned, verified by an existing or new unit test comparing the returned object's attributes.

4. **Given** a repository method previously implemented with `session.query(Model).filter_by(id=x).first()`, **when** the migrated method is called with an `id` that does not exist, **then** it returns `None`, verified by an existing or new unit test.

5. **Given** a bulk-update call site previously using `session.query(Model).filter(...).update({...})`, **when** the migrated `session.execute(update(Model).where(...).values(...))` is executed, **then** the same rows are mutated in the database, verified by a before/after query in an integration test.

6. **Given** a count query previously using `session.query(Model).filter(...).count()`, **when** the migrated `select(func.count())` form is executed, **then** it returns the same integer count, verified by a parameterised integration test with a known dataset.

7. **Given** the engine is configured with `future=True` (SQLAlchemy 1.4) or upgraded to 2.0, **when** the application starts and processes a representative set of read and write operations, **then** no `SAWarning` deprecation warnings related to the Query API appear in the application logs.

8. **Given** the CI pipeline runs, **when** the test stage completes, **then** code coverage for all data-access/repository modules remains at or above the coverage level recorded before the migration (baseline to be recorded prior to starting migration work).

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | What is the current pinned SQLAlchemy version in the project's dependency manifest (`requirements.txt`, `pyproject.toml`, or `setup.cfg`)? | TODO | TODO |
| 2 | What is the target SQLAlchemy version — 1.4 with `future=True` as an intermediate step, or a direct jump to 2.0+? | TODO | TODO |
| 3 | Which Python files/modules contain `session.query()` call sites? A full inventory is needed before migration begins. | TODO | TODO |
| 4 | Are there any `relationship()` definitions using implicit lazy loading that will raise errors under SQLAlchemy 2.0 strict mode? | TODO | TODO |
| 5 | Is there an async data-access layer (`AsyncSession`) in scope, or is this migration limited to synchronous `Session` usage? | TODO | TODO |
| 6 | Are there any raw SQL strings or `text()` constructs mixed with legacy Query API calls that also need to be reviewed? | TODO | TODO |
| 7 | Does the CI pipeline currently enforce a `SQLALCHEMY_WARN_20=1` flag or equivalent to surface deprecation warnings as errors? | TODO | TODO |
| 8 | Are there external libraries or plugins (e.g. Flask-SQLAlchemy, SQLAlchemy-Utils) that themselves use the legacy Query API and would need separate upgrades? | TODO | TODO |