# TASKS — Migrate Legacy SQLAlchemy Query API Calls to 2.0 `select()` Style

> **Scope notice:** The provided codebase is a Java/Spring Boot + Node.js/Express monorepo with no Python or SQLAlchemy components present in any source file, configuration, dependency manifest, or AGENTS.md stack table. There are no SQLAlchemy Query API calls to migrate in this repository.
>
> The tasks below are therefore written as a **preparatory investigation and no-op confirmation workflow** — the only honest work that can be grounded in the provided context.

---

## Prerequisites

N/A — not applicable to this task.

No Python runtime, pip/poetry/uv tooling, or SQLAlchemy dependency is declared anywhere in the provided source context (`user-management/package.json`, `payment-service/pom.xml`, `AGENTS.md` stack table, `docker-compose.yml`). There are no environment or tooling prerequisites that can be specified without inventing scope absent from the analysis.

---

## Phase 1 — Preparation

- [ ] [XS] Audit all dependency manifests for SQLAlchemy references in `user-management/package.json` and `payment-service/pom.xml` to confirm no Python/SQLAlchemy dependency is present or transitively pulled in
- [ ] [XS] Search the entire repository for legacy Query API patterns (`session.query(`, `.filter(`, `.first(`, `.all(`) across all files in `user-management/src/` and `payment-service/src/` to confirm zero occurrences before declaring scope complete

---

## Phase 2 — Core Upgrade

N/A — not applicable to this task.

No SQLAlchemy models, session factories, repository classes, or Query API call sites exist in the provided source files (`InMemoryPaymentRepository.java`, `UserController.js`, `AuthController.js`, or any other listed module). No migration tasks can be generated without fabricating targets absent from the codebase.

---

## Phase 3 — Testing & Validation

N/A — not applicable to this task.

No SQLAlchemy-backed query paths exist to regression-test. Existing test suites (`PaymentApplicationServiceTest.java`, `PaymentControllerTest.java`, `HealthControllerTest.java`, `health.test.js`) cover Java/Spring and Node.js layers only and are unaffected by this migration goal.

---

## Phase 4 — CI/CD & Infrastructure

N/A — not applicable to this task.

No Python build steps, `pip install`, or SQLAlchemy version pins appear in `.github/workflows/ci.yml`, `docker-compose.yml`, or any Dockerfile referenced in the provided context.

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Update `AGENTS.md` stack table to explicitly document that no Python/SQLAlchemy layer exists in this repository, preventing future misrouted migration tickets

---

> **Recommendation:** Re-run tech analysis against the correct target repository that contains the Python service with SQLAlchemy usage. The current context contains zero SQLAlchemy call sites; generating migration tasks against it would produce entirely fabricated work.