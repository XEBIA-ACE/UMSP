# Tasks: Fix SQLAlchemy Session Lifecycle to Prevent Connection Leaks

> **Scope note:** The provided codebase is a Java 21 / Spring Boot 3.x + Node.js 20 / Express 4.x monorepo. There is **no SQLAlchemy** (a Python ORM) present anywhere in the source tree, AGENTS.md, package.json, or any pom.xml shown. The persistence layer uses **Spring Data JPA / Hibernate** (Java) and an **in-memory ConcurrentHashMap** repository (`InMemoryPaymentRepository`). No Python runtime, no SQLAlchemy dependency, and no session/connection-pool configuration for SQLAlchemy exists in the provided context.

---

## Prerequisites

N/A — not applicable to this task.

> There are no SQLAlchemy components, Python runtimes, or related tooling in the provided tech analysis or source code. No prerequisites can be grounded in the available context.

---

## Phase 1 — Preparation

N/A — not applicable to this task.

> No SQLAlchemy session configuration, `Session`, `scoped_session`, or engine setup files are present in the provided source tree. No audit or baseline tasks can be scoped without fabricating components absent from the context.

---

## Phase 2 — Core Upgrade

N/A — not applicable to this task.

> The codebase contains no SQLAlchemy usage. The Java persistence layer uses Spring Data JPA / Hibernate managed by Spring Boot's `EntityManagerFactory` and `@Transactional` infrastructure. The in-memory adapter (`InMemoryPaymentRepository.java`) uses a `ConcurrentHashMap` with no connection pool. No SQLAlchemy migration tasks exist.

---

## Phase 3 — Testing & Validation

N/A — not applicable to this task.

---

## Phase 4 — CI/CD & Infrastructure

N/A — not applicable to this task.

---

## Phase 5 — Documentation & Rollout

N/A — not applicable to this task.

---

## ⚠️ Mismatch Notice

| Claimed component | Present in codebase? | Actual persistence technology |
|---|---|---|
| SQLAlchemy (Python ORM) | **No** | Spring Data JPA / Hibernate (Java) |
| Python runtime | **No** | Java 21 + Node.js 20 |
| `Session` / `scoped_session` | **No** | Spring `@Transactional` / `EntityManager` |
| Connection pool config | **No SQLAlchemy pool** | HikariCP (Spring Boot default) |

**Recommended action:** Clarify whether the intended task is:

1. **Fix Spring Data JPA / Hibernate session lifecycle** in `PaymentApplicationService.java` and `InMemoryPaymentRepository.java` (replace the in-memory store with a JPA-backed adapter and ensure `@Transactional` boundaries are correct), **or**
2. **Fix HikariCP connection pool exhaustion** in the Spring Boot service's `application.properties` / `application.yml`, **or**
3. A task targeting a **different repository** that actually contains SQLAlchemy.

Once the correct technology is confirmed, a fully grounded task list can be generated.