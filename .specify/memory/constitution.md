# CONSTITUTION
## Fix SQLAlchemy Session Lifecycle to Prevent Connection Leaks

---

## Project Identity

**Name:** SQLAlchemy Session Lifecycle Fix
**Service context:** User Management and Payment Service (Java 21 / Spring Boot 3.x + Node.js 20 / Express 4.x monorepo)
**Purpose:** Eliminate database connection leaks caused by improper SQLAlchemy session lifecycle management.
**High-level goal:** Ensure every database session is deterministically opened, used, and closed — preventing connection pool exhaustion under production load.

> **Note:** The source code provided uses Spring Data JPA / Hibernate (Java), not SQLAlchemy (Python). The current persistence layer uses an `InMemoryPaymentRepository`; no SQLAlchemy code is visible in the provided sources. Findings below are scoped to what is derivable from the provided context. SQLAlchemy-specific implementation details are marked **TODO**.

---

## Guiding Principles

1. **Prefer explicit session/transaction boundaries over implicit ones** because unbounded sessions are the primary cause of connection leaks under concurrent load.
2. **Prefer scoped, request-bound sessions over long-lived sessions** because long-lived sessions hold connections across idle time, exhausting the pool.
3. **Prefer `try/finally` or context-manager patterns over bare session usage** because exceptions that bypass `session.close()` silently leak connections.
4. **Prefer connection pool monitoring in CI over discovering leaks in production** because connection exhaustion manifests as latency spikes and cascading failures that are hard to diagnose post-hoc.
5. **Prefer no change to the domain model or API contracts** because the fix is purely infrastructural — the `Payment` domain object and all inbound ports must remain untouched.
6. **Prefer the existing hexagonal architecture boundary** (outbound persistence adapters only) because session lifecycle belongs exclusively to the infrastructure layer, not the application or domain layers.

---

## Constraints

| Category | Constraint |
|---|---|
| **Effort ceiling** | Moderate option — TODO: exact person-days not provided; treat as a focused, single-concern fix with no feature additions |
| **Scope freeze** | Changes are limited to the persistence adapter layer; domain model, application service, and API contracts are out of scope |
| **Runtime** | Java 21 LTS (Spring Boot 3.x) and/or the SQLAlchemy host runtime — TODO: confirm target runtime if SQLAlchemy is in a separate service not shown in sources |
| **Database** | PostgreSQL 15 — connection pool settings must remain compatible |
| **No downtime** | Fix must be deployable without service interruption; connection pool configuration changes must be backward-compatible |
| **Test environment** | Testcontainers (PostgreSQL) must be used to validate the fix; no mocking of the database layer in leak-detection tests |

---

## Quality Standards

| Standard | Measurable Bar |
|---|---|
| **Leak regression test** | At least 1 integration test must verify that repeated repository operations do not increase active connection count beyond pool `maximumPoolSize` |
| **Test coverage** | Persistence adapter classes must maintain ≥ 80% line coverage after the fix |
| **Code review** | All changes to session/transaction management require review by at least 1 engineer before merge |
| **CI gate** | GitHub Actions CI pipeline (`ci.yml`) must pass — including Testcontainers integration tests — before merge to main |
| **No new warnings** | Zero new resource-leak warnings introduced as reported by the SAST scan (`security-scan.yml`) |
| **Documentation** | The fix must include an inline comment at each session boundary explaining the lifecycle contract (open, use, close) |

---

## Decision Log

| ID | Decision | Rationale | Status |
|---|---|---|---|
| ADR-001 | Scope fix to outbound persistence adapter layer only | Hexagonal architecture mandates infrastructure concerns stay at the adapter boundary; domain and application layers must not be modified | Accepted |
| ADR-002 | Use Testcontainers with real PostgreSQL 15 for leak validation | In-memory repository (`InMemoryPaymentRepository`) cannot reproduce connection pool exhaustion; real DB required | Accepted |
| ADR-003 | Replace `InMemoryPaymentRepository` with a JPA/database-backed adapter as part of this fix | The current in-memory adapter has no connection lifecycle; a real adapter is required before session lifecycle can be fixed | Proposed |
| ADR-004 | Target SQLAlchemy runtime and version — TODO | No SQLAlchemy code is present in provided sources; target service must be identified before implementation begins | Proposed |