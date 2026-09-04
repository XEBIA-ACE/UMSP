# Spec: Migrate Legacy SQLAlchemy Query API Calls to 2.0 `select()` Style

## Summary

This spec covers the migration of all legacy SQLAlchemy 1.x `Query` API calls to the SQLAlchemy 2.0 `select()` style within the persistence layer of this codebase. The expected outcome is that all database query patterns use the 2.0-compatible `select()` construct, eliminating reliance on the legacy `Session.query()` interface, which is removed in SQLAlchemy 2.0. Upon completion, the persistence layer will be fully compatible with SQLAlchemy 2.0 and free of legacy query patterns.

## Motivation

N/A — not applicable to this task.

> **Note:** The provided tech analysis does not specify SQLAlchemy version numbers, CVE identifiers, EOL dates, or urgency ratings for this dependency. The source code context shows a Java/Spring Boot + Node.js stack with no Python or SQLAlchemy files present. The migration goal is stated as **medium urgency** in the tech analysis. All version-specific motivation details are marked TODO below.

| Driver | Detail |
|---|---|
| Legacy API removal | SQLAlchemy 2.0 removes the `Session.query()` API entirely; code using it will raise errors at runtime under SQLAlchemy 2.0. |
| Upgrade urgency | Medium (per tech analysis). |
| SQLAlchemy 1.x version in use | TODO — exact current version not present in provided context. |
| SQLAlchemy 2.0 target version | TODO — exact target version not present in provided context. |
| EOL / CVE references | TODO — not provided in tech analysis. |

## Current State

The provided source code context contains a Java/Spring Boot payment service and a Node.js user-management service. **No Python source files or SQLAlchemy usage are present in the provided context.** The following describes the expected current state based on the migration goal; specific class names, file paths, and query patterns are marked TODO pending access to the relevant Python source files.

| Element | Description |
|---|---|
| ORM framework | SQLAlchemy (version TODO) |
| Query interface in use | Legacy `Session.query(Model)` API (SQLAlchemy 1.x style) |
| Affected repository/data-access classes | TODO — specific class names not present in provided context |
| Affected query patterns | `session.query(Model).filter(...)`, `.filter_by(...)`, `.first()`, `.all()`, `.one()`, `.one_or_none()`, `.count()`, `.get(id)` |
| Session management | TODO — session factory / scoped session configuration not present in provided context |
| Config keys | TODO — database URL and engine configuration keys not present in provided context |
| Schema / model definitions | TODO — SQLAlchemy `Base` subclasses and mapped column definitions not present in provided context |

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| Row/object retrieval by primary key | `session.query(Model).get(pk)` | `session.get(Model, pk)` | N |
| Single-row fetch | `session.query(Model).filter(...).first()` | `session.execute(select(Model).where(...)).scalars().first()` | N |
| All-rows fetch | `session.query(Model).filter(...).all()` | `session.execute(select(Model).where(...)).scalars().all()` | N |
| Exactly-one-row fetch | `session.query(Model).filter(...).one()` | `session.execute(select(Model).where(...)).scalars().one()` | N |
| Optional single-row fetch | `session.query(Model).filter(...).one_or_none()` | `session.execute(select(Model).where(...)).scalars().one_or_none()` | N |
| Keyword-filter shorthand | `session.query(Model).filter_by(field=value)` | `session.execute(select(Model).where(Model.field == value)).scalars()...` | N |
| Count queries | `session.query(Model).filter(...).count()` | `session.execute(select(func.count()).select_from(select(Model).where(...).subquery()))` | N |
| `Query` object passed as return type or parameter | Any function accepting or returning a `Query` object | Replaced with `Select` construct or result set | Y |
| Import of `Query` class | `from sqlalchemy.orm import Query` | Removed; `from sqlalchemy import select` added | N |
| `Session.query()` call sites | All occurrences across data-access layer | Replaced with `session.execute(select(...))` pattern | Y — callers receiving `Query` objects must be updated |

**Removed:** All direct calls to `Session.query()`. The `Query` class is no longer used.

**Added:** `select()` construct imported from `sqlalchemy`; `scalars()` result-processing calls on `Session.execute()` return values.

## Compatibility & Breaking Changes

| Breaking Change | Affected Callers | Migration Path |
|---|---|---|
| `Session.query()` removed | Any code calling `session.query(Model)` directly | Replace with `session.execute(select(Model))` and call `.scalars()` on the result before iterating or fetching. |
| Functions returning a `Query` object | Callers that chain additional `.filter()`, `.order_by()`, or `.limit()` calls onto a returned `Query` | Refactor to return a `Select` construct, or resolve the query inside the repository method and return a plain list/optional. |
| `.get(pk)` on `Query` | `session.query(Model).get(pk)` call sites | Replace with `session.get(Model, pk)` (available in SQLAlchemy 1.4+ and 2.0). |
| `Query.count()` | Call sites using `.count()` on a `Query` chain | Replace with `select(func.count())` pattern (see Proposed Changes table). |
| `filter_by()` keyword syntax | Call sites using `.filter_by(field=value)` | Replace with explicit `.where(Model.field == value)` clause on the `select()` construct. |
| Lazy-evaluated `Query` iteration | Code that iterates a `Query` object directly (e.g. `for row in session.query(...)`) | Replace with `session.execute(select(...)).scalars()` and iterate the result. |
| `Query` used in type annotations | Any `Query`-typed parameters or return types in function signatures | Update type annotations to `Select` (for unexecuted constructs) or the appropriate result type (`list[Model]`, `Model | None`, etc.). |
| Specific affected classes and methods | TODO — not determinable from provided context | TODO |

## Acceptance Criteria

1. Given the codebase is scanned for `session.query(`, when the scan is run after migration, then zero occurrences of `session.query(` are found across all Python source files.

2. Given the codebase is scanned for `from sqlalchemy.orm import Query` or `import Query`, when the scan is run after migration, then zero occurrences of `Query` being imported for use as a query-builder are found.

3. Given a repository method that previously used `session.query(Model).filter(...).all()`, when the method is called with a valid filter condition, then it returns the same list of domain objects as the pre-migration implementation, verified by an existing or new integration test against a test database.

4. Given a repository method that previously used `session.query(Model).get(pk)`, when called with an existing primary key, then it returns the correct domain object; when called with a non-existent primary key, then it returns `None`.

5. Given a repository method that previously used `.one()`, when called and exactly one matching row exists, then it returns that row; when zero or multiple rows exist, then it raises the appropriate SQLAlchemy exception (`NoResultFound` or `MultipleResultsFound`).

6. Given a repository method that previously used `.one_or_none()`, when called and no matching row exists, then it returns `None` without raising an exception.

7. Given the full test suite is executed after migration, when all tests run, then the pass rate is equal to or greater than the pre-migration pass rate (no regressions introduced).

8. Given the application is started with SQLAlchemy 2.0 installed (version TODO), when any data-access operation is performed, then no `LegacyAPIWarning` or `RemovedIn20Warning` deprecation warnings are emitted.

9. Given a CI pipeline run after migration, when the pipeline executes, then all lint, unit, and integration test stages pass without SQLAlchemy-related errors or warnings.

10. Given the migration is complete, when the SQLAlchemy version is upgraded to 2.0 (version TODO) in the dependency manifest, then the application starts and all acceptance criteria above continue to pass.

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | What is the exact current version of SQLAlchemy in use? The provided source context contains no Python files or dependency manifests. | TODO | TODO |
| 2 | What is the exact target SQLAlchemy version (e.g. 2.0.x)? | TODO | TODO |
| 3 | Which Python source files and repository/data-access classes contain `Session.query()` call sites? None are present in the provided context. | TODO | TODO |
| 4 | Are there any functions or public interfaces that return a `Query` object to callers outside the data-access layer (e.g. service layer, use cases)? | TODO | TODO |
| 5 | Is SQLAlchemy used with the ORM (mapped classes) only, or also with Core `Table`/`Column` constructs that may require separate migration steps? | TODO | TODO |
| 6 | Are async sessions (`AsyncSession`) in use? If so, the `await session.execute(select(...))` pattern applies and must be verified separately. | TODO | TODO |
| 7 | Is `scoped_session` or a custom session factory in use that may affect how `session.execute()` is called? | TODO | TODO |
| 8 | Are there any third-party libraries (e.g. Flask-SQLAlchemy, FastAPI integrations) that wrap the `Query` API and require their own upgrade path? | TODO | TODO |
| 9 | What is the test database setup for integration tests validating repository behaviour (e.g. SQLite in-memory, Testcontainers PostgreSQL)? | TODO | TODO |