# Spec: Fix SQLAlchemy Session Lifecycle to Prevent Connection Leaks

## Summary

This spec covers the identification and remediation of SQLAlchemy session lifecycle mismanagement within the payment and user management services. The goal is to ensure that every database session is properly scoped, committed, rolled back on error, and closed after use — eliminating connection leaks that exhaust the connection pool under sustained load. The expected outcome is a service that maintains a stable, bounded number of active database connections across all payment and user operations.

## Motivation

**Note:** The provided tech analysis does not specify SQLAlchemy as a dependency of this codebase. The stack uses Spring Data JPA / Hibernate (Java 21, Spring Boot 3.x) backed by PostgreSQL 15, with an in-memory repository currently standing in for a production persistence adapter. Despite the task title referencing SQLAlchemy (a Python ORM), the actual connection-leak risk in this codebase is in the JPA/Hibernate session and connection lifecycle managed by Spring's transaction infrastructure.

| Driver | Detail |
|---|---|
| **Connection pool exhaustion** | Sessions not closed after use will hold connections from the HikariCP pool indefinitely, causing new requests to time out once the pool is saturated. |
| **In-memory repository replacement** | `InMemoryPaymentRepository` is explicitly marked for replacement with a JPA/database-backed adapter; the session lifecycle must be correct before that migration goes to production. |
| **Upgrade urgency** | Medium — no active CVE, but the risk of production outage under load is real once the JPA adapter is introduced. |
| **Tech debt** | The current `PaymentApplicationService` performs multi-step persistence operations (save → gateway call → update) with no explicit transaction boundary, meaning partial failures can leave the database in an inconsistent state and sessions may not be released. |

## Current State

### Persistence Layer

- **`InMemoryPaymentRepository`** (`com.payments.adapters.outbound.persistence`) implements `PaymentRepositoryPort` using a `ConcurrentHashMap`. No real database sessions are involved today, so no leak exists in the current adapter — but the replacement adapter will inherit the same call sites.
- **`PaymentEntity`** (`com.payments.adapters.outbound.persistence`) is a plain POJO with no JPA annotations. It is explicitly noted as a starting point for a JPA-backed entity.
- **`PaymentApplicationService`** (`com.payments.application.service`) calls `paymentRepository.save()`, then a gateway, then `paymentRepository.update()` — three distinct operations with no enclosing `@Transactional` boundary. If the gateway call or the update fails, the initial `save()` is not rolled back.
- **`PaymentRepositoryPort`** exposes `save`, `findById`, `findByUserId`, and `update` as discrete methods. There is no unit-of-work or session-scoping abstraction at the port level.

### Transaction Configuration

- No `@Transactional` annotations are present on `PaymentApplicationService` or any service method in the provided source.
- No explicit `DataSource`, `EntityManagerFactory`, or transaction manager configuration is visible in the provided source (a `SecurityConfig` is present but no `PersistenceConfig`).
- Spring Boot 3.x auto-configures HikariCP as the default connection pool; pool size and timeout settings are not shown in the provided source.

### Relevant Config Keys (TODO — not present in provided source)

- `spring.datasource.hikari.maximum-pool-size`
- `spring.datasource.hikari.connection-timeout`
- `spring.jpa.open-in-view` (must be `false` to prevent sessions being held for the duration of an HTTP request)

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| `PaymentApplicationService.process()` | No transaction boundary; `save` and `update` are separate uncommitted operations | Entire method wrapped in a single `@Transactional` boundary; gateway call occurs within the transaction scope | N |
| `PaymentApplicationService.refund()` | No transaction boundary (assumed, consistent with `process()`) | Wrapped in `@Transactional`; rollback on any unchecked exception | N |
| `PaymentApplicationService.getById()` | No transaction boundary | Annotated `@Transactional(readOnly = true)` | N |
| Future JPA `PaymentRepository` adapter | Does not exist yet | Must use Spring Data JPA repository or explicit `EntityManager` with session closed in a `finally` block / managed by `@Transactional` | N |
| `spring.jpa.open-in-view` config key | Not explicitly set (Spring Boot default is `true`, which holds a session open for the full HTTP request lifecycle) | Explicitly set to `false` in `application.properties` / `application.yml` | N — no API change; may surface lazy-loading issues that were previously hidden |
| HikariCP pool configuration | Not explicitly configured (Boot defaults) | Pool size, connection timeout, and idle timeout explicitly declared and validated | N |

**Removed:** Nothing is removed from the public API.

**Added:**
- `@Transactional` demarcation on all write methods in `PaymentApplicationService`.
- `@Transactional(readOnly = true)` on all read methods.
- Explicit `spring.jpa.open-in-view=false` configuration.
- Explicit HikariCP pool sizing configuration.

## Compatibility & Breaking Changes

| Change | Impact on Callers | Migration Path |
|---|---|---|
| `spring.jpa.open-in-view=false` | Any code that relies on lazy-loaded JPA associations being resolved outside a transaction (e.g. in a controller or serialiser) will throw `LazyInitializationException` | Ensure all required associations are fetched eagerly or within the service-layer transaction before the method returns |
| `@Transactional` on `PaymentApplicationService` | If callers currently catch and swallow exceptions after a partial `save`, the rollback behaviour will change — the `save` will now be rolled back too | Callers should not suppress exceptions from service methods; error handling in `PaymentController` already re-throws or returns error responses, so no change is expected |
| HikariCP explicit pool sizing | If `maximum-pool-size` is set lower than the current implicit default, requests may queue | TODO — validate against observed peak concurrency before setting a hard limit |
| Gateway call inside transaction | The Stripe/PayPal HTTP call will now occur within a database transaction, holding a connection for the duration of the network round-trip | TODO — evaluate whether the gateway call should be moved outside the transaction boundary to reduce connection hold time; this may require a two-phase approach (save PENDING outside transaction, update status inside a new transaction after gateway returns) |

## Acceptance Criteria

1. **Given** the payment service is running with a JPA-backed repository and a real PostgreSQL 15 database, **when** 50 concurrent `POST /api/payments` requests are submitted and all complete (success or failure), **then** the number of active connections in the HikariCP pool returns to the pre-request baseline within 5 seconds of the last response.

2. **Given** a `POST /api/payments` request where the gateway call succeeds but the subsequent `update` call throws a runtime exception, **when** the exception propagates, **then** no `PENDING` payment record is persisted in the database (the transaction is fully rolled back).

3. **Given** a `POST /api/payments` request that completes successfully, **when** the response is returned, **then** exactly one payment record with status `COMPLETED` exists in the database and no database session remains open for that request thread.

4. **Given** `spring.jpa.open-in-view` is set to `false`, **when** the application starts, **then** no `HibernateJpaDialect` open-session-in-view warning appears in the startup log.

5. **Given** a `GET /api/payments/{id}` request, **when** the handler method returns, **then** the database connection used for the read is returned to the pool (verified by pool metrics showing active count unchanged from baseline).

6. **Given** a `POST /api/payments/{id}/refund` request where the payment does not exist, **when** the service throws a not-found exception, **then** no database transaction is left open and the connection is returned to the pool.

7. **Given** the CI pipeline runs the Testcontainers-backed integration test suite, **when** all tests complete, **then** zero connection-leak warnings are emitted by HikariCP in the test output.

8. **Given** the application configuration, **when** the service starts, **then** `spring.jpa.open-in-view` is explicitly set to `false` and HikariCP `maximum-pool-size`, `connection-timeout`, and `idle-timeout` are all explicitly declared with documented values.

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | Should the payment gateway HTTP call (Stripe/PayPal) be moved outside the database transaction to avoid holding a connection during a network round-trip? This is the most significant architectural decision for this fix. | TODO | TODO |
| 2 | What is the target `maximum-pool-size` for HikariCP in production? This requires knowledge of the deployment topology (number of service instances, PostgreSQL `max_connections`). | TODO | TODO |
| 3 | The task title references SQLAlchemy (Python ORM) but the codebase uses Spring Data JPA / Hibernate. Is there a Python service not present in the provided source that also requires session lifecycle fixes? | TODO | TODO |
| 4 | Are there any existing `@Transactional` annotations on repository or service classes not shown in the provided source (e.g. in `UserService`, `AuthService`)? A full audit is needed before changes are applied. | TODO | TODO |
| 5 | Does the `user-service` (Spring Boot, `com.company.userservice`) have the same session lifecycle issue? The provided source shows `UserService` and `AuthService` exist but their implementations are not included. | TODO | TODO |
| 6 | What is the current HikariCP default pool size in use (Boot default is 10)? Has connection exhaustion been observed in production or staging metrics? | TODO | TODO |