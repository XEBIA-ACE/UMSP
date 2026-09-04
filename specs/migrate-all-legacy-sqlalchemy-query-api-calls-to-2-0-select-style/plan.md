# Plan: Migrate Legacy SQLAlchemy Query API Calls to 2.0 `select()` Style

## Overview

**Migration Strategy: Big-Bang (scoped)**

The task is to migrate all legacy SQLAlchemy Query API calls to the SQLAlchemy 2.0 `select()` style. Based on the provided codebase context, the project is a Java/Spring Boot + Node.js monorepo. **No SQLAlchemy usage is present anywhere in the provided source code.** The persistence layer in the payment service uses an in-memory `ConcurrentHashMap` (`InMemoryPaymentRepository.java`), and the user-management service is Node.js-based with no Python ORM in sight.

Because no SQLAlchemy code has been identified in the provided context, a big-bang approach is appropriate for the scope that *can* be acted upon: a targeted audit and migration of any SQLAlchemy call sites once they are located. The risk score is low-to-medium (upgrade urgency: medium per tech analysis) and the effort estimate is moderate, making a single-phase sweep preferable to a strangler-fig approach.

> **Critical Note:** The tech analysis lists the language as "unknown" and no SQLAlchemy dependency appears in `package.json` (Node.js) or any Java `pom.xml` provided. All plan sections below are written against the task goal; sections that cannot be grounded in the provided context are marked **TODO**.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 | **Audit** — Locate every file containing legacy `session.query(Model)`, `.filter()`, `.first()`, `.all()`, `.one()`, `.one_or_none()`, `.get()` call chains across the repository | Access to full source tree (TODO: Python service not present in provided context) | TODO (derive from moderate option once scope is confirmed) |
| 2 | **Dependency Upgrade** — Bump SQLAlchemy to the target version and enable `SQLALCHEMY_WARN_20` / future-mode flag to surface remaining legacy calls | Phase 1 complete; target version confirmed from tech analysis | TODO |
| 3 | **Query Migration** — Replace all legacy `Query` API call sites with `select()` + `Session.execute()` style, file by file | Phase 2 complete | TODO (moderate estimate; person-days not provided in upgrade option) |
| 4 | **Test & Validation** — Run full test suite, confirm no regressions, remove `SQLALCHEMY_WARN_20` flag | Phase 3 complete | TODO |

> Effort values are marked TODO because the upgrade option states "details not provided" and no person-days figure was supplied.

---

## Component Changes

### Persistence / Repository Layer

**What changes:** Every call site using the legacy `Session.query()` API must be rewritten to use `select()` from `sqlalchemy` combined with `Session.execute()` or `Session.scalars()`.

**Pattern mapping:**

| Legacy (1.x Query API) | Modern (2.0 `select()` style) |
|---|---|
| `session.query(User).filter(User.id == id).first()` | `session.execute(select(User).where(User.id == id)).scalar_one_or_none()` |
| `session.query(User).filter_by(email=email).one()` | `session.execute(select(User).where(User.email == email)).scalar_one()` |
| `session.query(User).all()` | `session.execute(select(User)).scalars().all()` |
| `session.query(User).get(pk)` | `session.get(User, pk)` *(2.0 preferred)* |
| `session.query(User).filter(...).delete()` | `session.execute(delete(User).where(...))` |
| `session.query(User).filter(...).update({...})` | `session.execute(update(User).where(...).values(...))` |

**Files affected:** TODO — no Python source files are present in the provided context. Once the Python service directory is identified, all files matching `*repository*.py`, `*dao*.py`, `*query*.py`, or any file importing `from sqlalchemy.orm import Session` should be audited.

**APIs modified:**
- Remove all imports of `Query` if explicitly imported.
- Add imports: `from sqlalchemy import select, update, delete` at each affected module.
- `Session.execute()` returns a `CursorResult`; callers must use `.scalar_one()`, `.scalar_one_or_none()`, `.scalars().all()`, etc. — return-type handling at call sites must be verified.

### Application / Service Layer

**What changes:** Any service class that unwraps query results (e.g., checks for `None`, iterates lists) may need minor adjustments if the return type changes from a `Query` object to a plain list or scalar. No lazy-evaluation of `Query` objects will be possible after migration.

**Files affected:** TODO — dependent on locating the Python service.

### Configuration

**What changes:**
- During Phase 2, add `SQLALCHEMY_WARN_20 = True` (SQLAlchemy < 2.0) or enable `future=True` on the `create_engine()` call to surface all remaining legacy patterns before cutting over.
- After Phase 4, remove the warning flag.

**Config keys affected:** `create_engine(..., future=True)` — exact file path TODO.

---

## Dependency Upgrade Plan

| Dependency | Current Version | Target Version | Breaking Changes | Migration Notes |
|---|---|---|---|---|
| SQLAlchemy | TODO — not listed in provided tech analysis | TODO — not listed in provided tech analysis | `Session.query()` removed in 2.0; `Query` object no longer available; `Engine.execute()` removed; implicit autocommit removed | Enable `future=True` on engine and `SQLALCHEMY_WARN_20=True` as a transitional step; all version numbers must be confirmed from actual tech analysis once provided |

> **All version numbers are marked TODO** because the tech analysis explicitly states "Top upgrade targets: (none listed)" and no SQLAlchemy version appears anywhere in the provided source files or `package.json`. Do not source versions from training data.

---

## Infrastructure Changes

N/A — not applicable to this task. No Docker base image changes, Kubernetes manifest changes, or CI/CD pipeline changes are required solely for a SQLAlchemy Query API migration. TODO: If the Python service runs in a Docker container, confirm the base image supports the target SQLAlchemy version's Python requirement.

---

## Rollback Strategy

### Phase 1 (Audit)
- Read-only phase; no code changes. Rollback is not required.

### Phase 2 (Dependency Upgrade)
- Revert the dependency version pin in `requirements.txt` / `pyproject.toml` / `setup.cfg` (file path TODO) to the previous version.
- Re-run `pip install -r requirements.txt` (or equivalent) in the affected service container.
- Remove `SQLALCHEMY_WARN_20 = True` and `future=True` from engine configuration.
- Redeploy the previous Docker image tag (TODO: confirm image registry and tag strategy).

### Phase 3 (Query Migration)
- Each file migration should be committed atomically (one commit per module/file).
- To roll back a specific file: `git revert <commit-sha>` for that file's migration commit, or `git checkout <previous-sha> -- path/to/file.py`.
- The `future=True` engine flag can be removed temporarily to re-enable legacy `Query` API while partial rollback is in progress.

### Phase 4 (Test & Validation)
- If regressions are found post-merge, revert the Phase 3 migration commits via `git revert` on the merge commit.
- Re-enable `SQLALCHEMY_WARN_20 = True` to identify remaining issues before re-attempting.

---

## Testing Strategy

### Unit Tests
- **Tool:** TODO (Python test framework not identified in provided context — likely `pytest` given SQLAlchemy usage, but not confirmed).
- For each migrated repository method, verify return types: `scalar_one_or_none()` returns `None` vs. raises `NoResultFound` — assert the correct exception/null behaviour.
- Mock `Session` using `unittest.mock.MagicMock` or `pytest-mock`; assert that `session.execute(select(...))` is called rather than `session.query(...)`.
- **Coverage target:** 100% of migrated call sites must have a corresponding unit test.

### Integration Tests
- **Tool:** TODO (confirm test DB setup — likely `pytest` + `SQLAlchemy` test fixtures against a real or in-memory DB such as SQLite or a Testcontainers PostgreSQL instance, consistent with the PostgreSQL 15 stack noted in `AGENTS.md`).
- Run existing integration tests unchanged after migration; they must all pass without modification.
- Add integration tests for any query that uses `update()` or `delete()` DML, as these have the most behavioural differences in 2.0 (explicit `session.commit()` required; no implicit flush).

### Regression Tests
- Execute the full existing test suite before and after each Phase 3 commit.
- Diff query result sets for critical read paths (user lookup by ID, payment lookup by user) using a shadow-run if possible.

### Performance Tests
- TODO — no performance test tooling is identified in the provided context for a Python service.
- Baseline query latency for high-frequency paths (e.g., `findById`, `findByUserId` equivalents) before Phase 3; re-measure after Phase 4.

### CI Gates
- The existing GitHub Actions pipeline (`.github/workflows/ci.yml`) must be extended to:
  1. Run `grep -r "session\.query(" --include="*.py"` and fail the build if any matches are found post-migration (zero-tolerance lint gate).
  2. Run the full test suite with `SQLALCHEMY_WARN_20=True` during Phase 2 and assert zero warnings.
  3. Enforce the coverage target on migrated modules.

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| Full audit of SQLAlchemy call sites complete; count of legacy `session.query()` usages documented | Phase 1 | TODO | TODO |
| SQLAlchemy dependency bumped; `future=True` enabled; zero new legacy calls introduced | Phase 2 | TODO | TODO |
| All legacy `Query` API call sites replaced with `select()` style | Phase 3 | TODO | TODO |
| Full test suite green; `SQLALCHEMY_WARN_20` flag removed; migration merged to main | Phase 4 | TODO | TODO |

> All timeline estimates are marked TODO because the upgrade option's person-days figure was not provided ("details not provided") and the scope of SQLAlchemy call sites cannot be determined from the provided source context.