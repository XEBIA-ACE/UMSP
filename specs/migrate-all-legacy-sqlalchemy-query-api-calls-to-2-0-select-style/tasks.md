# TASKS — Migrate Legacy SQLAlchemy Query API Calls to 2.0 `select()` Style

> **Scope notice:** The provided codebase is a Java/Spring Boot + Node.js/Express monorepo with no Python or SQLAlchemy components present. The tech analysis summary describes the migration goal as a SQLAlchemy 2.0 modernisation, but no SQLAlchemy source files, Python runtime, or related dependencies appear anywhere in the supplied context. The tasks below are therefore scoped strictly to what *can* be grounded in the provided source — which means this document records the investigation and remediation steps that would be required if SQLAlchemy code were discovered, and flags the mismatch as a prerequisite blocker.

---

## Prerequisites

- [ ] [XS] Confirm the target repository for this migration by searching the monorepo root (`user-payment-service/`) for any Python source files (`*.py`) or `requirements.txt` / `pyproject.toml` / `setup.cfg` files — none are present in the supplied context; work cannot proceed until the correct repository is identified
- [ ] [XS] Verify SQLAlchemy is a declared dependency by locating a `requirements.txt`, `pyproject.toml`, or `setup.cfg` that lists `sqlalchemy` — no such file exists in the provided source tree; this is a hard blocker
- [ ] [XS] Confirm the installed SQLAlchemy version is ≥ 1.4 (the minimum that ships the 2.0-style `select()` API alongside the legacy `Query` API) by running `pip show sqlalchemy` in the target environment
- [ ] [XS] Ensure Python runtime version is ≥ 3.8 (required by SQLAlchemy 2.x) by running `python --version` in the target environment
- [ ] [XS] Confirm read/write access to the repository branch containing the Python service and that a feature branch can be created from `main`

---

## Phase 1 — Preparation

N/A — not applicable to this task until the correct Python/SQLAlchemy repository is identified (see Prerequisites blockers above).

> Once the repository is confirmed, the following preparation tasks apply:

- [ ] [XS] Create feature branch `migrate/sqlalchemy-2-select-style` from `main` in the target Python service repository
- [ ] [S] Run `grep -rn "\.query\b\|session\.query" --include="*.py" .` across the entire Python service source tree to produce a complete inventory of legacy `Query` API call sites and record results in `migration-inventory.md`
- [ ] [XS] Capture the current test suite pass/fail baseline by running the existing test command (e.g. `pytest --tb=short -q`) and saving output to `baseline-test-results.txt`
- [ ] [XS] Record current test coverage baseline by running `pytest --cov --cov-report=term-missing -q` and saving output to `baseline-coverage.txt`
- [ ] [XS] Enable SQLAlchemy 2.0 deprecation warnings as errors in the test configuration (e.g. set `SQLALCHEMY_WARN_20=1` environment variable or add `filterwarnings = error::sqlalchemy.exc.RemovedIn20Warning` to `pytest.ini` / `pyproject.toml [tool.pytest.ini_options]`) so that any remaining legacy calls surface as test failures

---

## Phase 2 — Core Upgrade

N/A — not applicable to this task: no Python source files, SQLAlchemy models, repository classes, or session-management code are present in the provided context. The Java persistence layer uses Spring Data JPA / Hibernate (`InMemoryPaymentRepository.java`) and the Node.js layer uses no ORM. No SQLAlchemy `Query` API call sites exist in the supplied source tree to migrate.

> Once the correct repository is confirmed and the call-site inventory from Phase 1 is complete, tasks of the following form apply per affected module:
>
> - [ ] [M] Replace all `session.query(Model).filter(...).all()` calls with `session.execute(select(Model).where(...)).scalars().all()` in `<repository_module>.py`
> - [ ] [M] Replace all `session.query(Model).filter(...).first()` calls with `session.execute(select(Model).where(...)).scalars().first()` in `<repository_module>.py`
> - [ ] [S] Replace all `session.query(Model).get(pk)` calls with `session.get(Model, pk)` (the 2.0-native form) in `<repository_module>.py`
> - [ ] [S] Remove any `Query`-chained `.options()`, `.join()`, `.outerjoin()`, `.order_by()`, `.limit()`, `.offset()` calls and rewrite as equivalent `select()` clause methods in `<repository_module>.py`
> - [ ] [XS] Remove any remaining imports of `sqlalchemy.orm.Query` that are no longer referenced after migration in all affected modules

---

## Phase 3 — Testing & Validation

N/A — not applicable to this task: no test files targeting SQLAlchemy repository classes exist in the provided context (`PaymentApplicationServiceTest.java`, `PaymentControllerTest.java`, `HealthControllerTest.java`, and `health.test.js` are all unrelated to SQLAlchemy).

> Once the correct repository is confirmed, the following validation tasks apply:

- [ ] [S] Run the full test suite with `SQLALCHEMY_WARN_20=1 pytest --tb=short -q` and confirm zero `RemovedIn20Warning` deprecation errors remain
- [ ] [XS] Compare test results against `baseline-test-results.txt` and confirm no regressions in pass/fail counts
- [ ] [XS] Compare coverage report against `baseline-coverage.txt` and confirm coverage has not decreased for any migrated module
- [ ] [S] Execute any integration or end-to-end tests that exercise database query paths and confirm all pass against the target database (PostgreSQL 15 per AGENTS.md stack table, if applicable to the Python service)

---

## Phase 4 — CI/CD & Infrastructure

N/A — not applicable to this task: the CI/CD pipeline defined in `.github/workflows/ci.yml` and `security-scan.yml` targets the Java and Node.js services only. No Python build steps, linting, or test stages are present in the provided pipeline context.

> Once the correct repository is confirmed, the following CI task applies:

- [ ] [XS] Add `SQLALCHEMY_WARN_20=1` as a CI environment variable in the relevant `.github/workflows/` job step that runs the Python test suite, so the deprecation-as-error gate is enforced on every pull request

---

## Phase 5 — Documentation & Rollout

N/A — not applicable to this task: no Python service `CHANGELOG`, runbook, or deployment documentation is present in the provided context (`README.md` and `AGENTS.md` cover only the Java and Node.js services).

> Once the correct repository is confirmed, the following documentation tasks apply:

- [ ] [XS] Add a `CHANGELOG` entry in the Python service documenting the SQLAlchemy Query API → 2.0 `select()` migration, referencing the affected modules identified in `migration-inventory.md`
- [ ] [XS] Remove the `SQLALCHEMY_WARN_20=1` environment variable and `filterwarnings` entry added during preparation (Phase 1) once SQLAlchemy is fully upgraded to 2.x and the legacy warning filter is no longer needed

---

> **Action required before any coding begins:** The task as specified cannot be executed against the provided codebase. The repository supplied contains no Python files, no SQLAlchemy dependency declarations, and no ORM query code of any kind. The engineering lead or task requester must supply the correct Python service repository path before this task document can be fully populated.