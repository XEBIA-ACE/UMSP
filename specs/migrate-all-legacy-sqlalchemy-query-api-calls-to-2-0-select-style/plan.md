# Plan: Migrate Legacy SQLAlchemy Query API Calls to 2.0 `select()` Style

## Overview

**Migration Strategy: Big-Bang (scoped)**

The task is to migrate all legacy SQLAlchemy Query API calls to the SQLAlchemy 2.0 `select()` style. Based on the provided codebase context, the project is a Java/Spring Boot + Node.js monorepo. **No SQLAlchemy usage is present anywhere in the provided source code.** The persistence layer in the payment service uses an in-memory `ConcurrentHashMap` (`InMemoryPaymentRepository.java`), and the user-management service is Node.js-based with no Python ORM in sight.

Because no SQLAlchemy code has been identified in the provided context, a big-bang approach is appropriate for any files that are discovered during a full repository scan — the scope is bounded, the risk is low-to-medium (per the upgrade option), and a strangler-fig approach would add unnecessary coordination overhead for an ORM query style migration.

> **⚠️ Critical Finding:** The tech analysis states language/runtime/build tool as "unknown" and no SQLAlchemy files were present in the provided code context. All phases below assume SQLAlchemy files exist elsewhere in the repository (not provided). A full repository scan **must** be performed as the first step before any migration work begins.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 | **Discovery & Audit** — Scan the full repository for all files using SQLAlchemy Query API patterns (`session.query(...)`, `.filter()`, `.first()`, `.all()`, `.one()`, `.one_or_none()`, `.get()`, etc.). Produce an inventory of affected files, classes, and call sites. | Access to full repository source | TODO (derive from actual file count once discovered) |
| 2 | **Dependency Version Verification** — Confirm the installed SQLAlchemy version supports 2.0-style `select()`. Enable `SQLALCHEMY_WARN_20=1` (for 1.4.x) to surface all legacy call sites via deprecation warnings. | Phase 1 complete | TODO |
| 3 | **Core Query Migration** — Rewrite all `session.query(Model).filter(...).all()` patterns to `session.execute(select(Model).where(...)).scalars().all()`. Migrate scalar fetches, `.first()`, `.one()`, `.one_or_none()`, and `.get()` equivalents. | Phase 2 complete | TODO (moderate estimate — details not provided) |
| 4 | **Relationship & Joined Query Migration** — Migrate any joined loads, subqueries, or relationship-traversal queries that use the legacy Query API. | Phase 3 complete | TODO |
| 5 | **Test Suite Update & Validation** — Update any unit/integration tests that mock or assert against `session.query()` call patterns. Run full test suite with `SQLALCHEMY_WARN_20=1` to confirm zero legacy warnings. | Phase 3–4 complete | TODO |
| 6 | **Final Cleanup & Documentation** — Remove `SQLALCHEMY_WARN_20` flag, remove any legacy compatibility shims, update internal developer documentation. | Phase 5 complete | TODO |

> **Note:** Effort values are marked TODO because the upgrade option details were not provided and no SQLAlchemy source files were present in the context to estimate line-count or complexity.

---

## Component Changes

### Discovery Required

No SQLAlchemy components were identified in the provided source files. The following describes the **expected** change pattern for any Python files found during Phase 1.

#### Pattern: Simple Model Fetch

**Files affected:** TODO — identify during Phase 1 audit.

**Before (legacy Query API):**
```python
# session.query() style
user = session.query(User).filter(User.id == user_id).first()
users = session.query(User).filter(User.active == True).all()
user = session.query(User).get(user_id)
```

**After (2.0 `select()` style):**
```python
from sqlalchemy import select

# select() style
user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
users = session.execute(select(User).where(User.active == True)).scalars().all()
user = session.get(User, user_id)  # session.get() is retained in 2.0
```

#### Pattern: Count Query

**Before:**
```python
count = session.query(User).filter(User.active == True).count()
```

**After:**
```python
from sqlalchemy import select, func

count = session.execute(select(func.count()).select_from(User).where(User.active == True)).scalar_one()
```

#### Pattern: Joined / Relationship Query

**Before:**
```python
results = session.query(Order).join(User).filter(User.id == user_id).all()
```

**After:**
```python
results = session.execute(select(Order).join(User).where(User.id == user_id)).scalars().all()
```

#### Pattern: Update / Delete

**Before:**
```python
session.query(User).filter(User.id == user_id).update({"active": False})
session.query(User).filter(User.id == user_id).delete()
```

**After:**
```python
from sqlalchemy import update, delete

session.execute(update(User).where(User.id == user_id).values(active=False))
session.execute(delete(User).where(User.id == user_id))
```

#### APIs Modified

| Legacy API | 2.0 Replacement | Notes |
|---|---|---|
| `session.query(Model)` | `select(Model)` + `session.execute()` | Core replacement |
| `.filter(...)` | `.where(...)` | Direct rename |
| `.all()` | `.scalars().all()` | Unwrap `ScalarResult` |
| `.first()` | `.scalars().first()` | Unwrap `ScalarResult` |
| `.one()` | `.scalar_one()` | Raises if not exactly one |
| `.one_or_none()` | `.scalar_one_or_none()` | Returns `None` if absent |
| `.get(pk)` | `session.get(Model, pk)` | `session.get()` is 2.0-compatible |
| `.count()` | `select(func.count()).select_from(Model)` | Explicit aggregate |
| `.update({})` | `session.execute(update(Model).values(...))` | Bulk update |
| `.delete()` | `session.execute(delete(Model))` | Bulk delete |

---

## Dependency Upgrade Plan

| Dependency | Current Version | Target Version | Breaking Changes | Migration Notes |
|---|---|---|---|---|
| SQLAlchemy | TODO — not determinable from provided context | TODO — not determinable from provided context | Legacy `Query` API removed in 2.0 final; deprecated in 1.4 | Set `SQLALCHEMY_WARN_20=1` on SQLAlchemy 1.4.x to surface all call sites before upgrading. If already on 2.x, `session.query()` raises `AttributeError` unless `future=True` was set. |

> **All version numbers are marked TODO** because the tech analysis explicitly states the language/runtime/build tool is unknown and no `requirements.txt`, `pyproject.toml`, `setup.cfg`, or `pom.xml` with SQLAlchemy was present in the provided context. Version numbers must be sourced from the actual project dependency manifest — not from training data.

---

## Infrastructure Changes

N/A — not applicable to this task. The migration is a source-code-level ORM query style change. No Docker base image changes, Kubernetes manifests, CI/CD pipeline changes, or IaC updates are required solely for this migration.

> **TODO:** If a CI pipeline runs Python linting or type-checking (e.g. `mypy`, `pylint` with SQLAlchemy plugin), verify that the plugin version is compatible with the target SQLAlchemy version after migration.

---

## Rollback Strategy

| Phase | Rollback Action |
|---|---|
| Phase 1 (Discovery) | No code changes made; nothing to roll back. Delete the audit inventory document if desired. |
| Phase 2 (Dependency Verification) | Remove `SQLALCHEMY_WARN_20=1` from environment/config if it was added. No code changes. |
| Phase 3 (Core Query Migration) | Revert via `git revert` or `git checkout` on the specific files migrated. Each file should be committed individually or in small logical batches to enable targeted revert. |
| Phase 4 (Relationship & Joined Query Migration) | Same as Phase 3 — revert the specific commits covering joined query files. |
| Phase 5 (Test Suite Update) | Revert test file changes alongside the corresponding source file reverts from Phase 3/4. |
| Phase 6 (Final Cleanup) | Restore any removed compatibility shims from git history. Re-add `SQLALCHEMY_WARN_20=1` if needed for re-diagnosis. |

**General rollback principle:** Each phase's changes must be committed to a dedicated branch (e.g. `migration/sqlalchemy-2-phase-3`) and merged via pull request. This ensures any phase can be reverted independently without affecting other phases.

---

## Testing Strategy

> **Note:** The test stack identified in the provided context is JUnit 5 + Mockito (Java) and Jest + Supertest (Node.js). No Python test framework is referenced. The following targets the expected Python/SQLAlchemy layer — **TODO: confirm actual test framework from repository**.

### Test Pyramid

| Layer | Tooling | Coverage Target | CI Gate |
|---|---|---|---|
| **Unit** | TODO (likely `pytest` + `unittest.mock` for session mocking) | ≥ 80% line coverage on all migrated repository/query files | Fail build if coverage drops below baseline |
| **Integration** | TODO (likely `pytest` + real DB or `testcontainers-python`) | All repository methods exercised against a real database dialect | Fail build on any integration test failure |
| **Regression** | Full existing test suite re-run post-migration with `SQLALCHEMY_WARN_20=1` (if on 1.4.x) | Zero SQLAlchemy legacy deprecation warnings emitted | Fail build if any `LegacyAPIWarning` is detected |
| **Performance** | TODO — baseline query performance before migration, compare after | No regression > 5% on p95 query latency | Advisory gate (non-blocking initially) |

### Specific Validation Steps

1. **Before migration:** Run `grep -rn "session\.query\(" --include="*.py" .` to establish a complete baseline count of legacy call sites.
2. **After each phase:** Re-run the grep; count must decrease monotonically toward zero.
3. **Final validation:** Zero matches for `session\.query\(` across the entire codebase.
4. **Warning sweep:** Run the test suite with `SQLALCHEMY_WARN_20=1` (SQLAlchemy 1.4) or observe `RemovedIn20Warning`; zero warnings must be emitted.
5. **TODO:** Confirm CI pipeline file (`.github/workflows/ci.yml` is present per AGENTS.md) includes a Python test step and add the warning-as-error flag: `python -W error::sqlalchemy.exc.RemovedIn20Warning -m pytest`.

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| Repository audit complete; all SQLAlchemy call sites inventoried | Phase 1 | TODO | TODO |
| Dependency versions confirmed; deprecation warnings enabled | Phase 2 | TODO | TODO |
| All simple `session.query()` fetch patterns migrated | Phase 3 | TODO | TODO |
| All joined/relationship queries migrated | Phase 4 | TODO | TODO |
| Test suite updated; zero legacy warnings in CI | Phase 5 | TODO | TODO |
| Cleanup complete; migration merged to main | Phase 6 | TODO | TODO |

> **All timeline estimates are marked TODO.** The upgrade option effort estimate was stated as "details not provided" and no SQLAlchemy source files were present in the context to derive a line-count-based estimate. Timelines must be set after Phase 1 discovery establishes the actual scope of affected files and call sites.