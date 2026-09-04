# PLAN: Fix SQLAlchemy Session Lifecycle to Prevent Connection Leaks

> **Note on tech analysis gap:** The task title references SQLAlchemy (a Python ORM), but the provided codebase uses **Spring Data JPA / Hibernate** on Java 21 + Spring Boot 3.x with PostgreSQL 15. No Python or SQLAlchemy code is present in the context. This plan addresses the actual codebase: fixing JPA/Hibernate session and connection lifecycle issues in the Spring Boot services to prevent connection pool leaks. All decisions are grounded in the provided source files.

---

## Overview

**Strategy: Feature-flag gated / targeted in-place fix**

The connection leak risk is scoped to the persistence layer — specifically `InMemoryPaymentRepository`, `PaymentApplicationService`, and the Spring Data JPA configuration that will back the production repository. There is no need for a strangler-fig or big-bang rewrite. The fix is applied incrementally behind a Spring profile flag (`prod` vs `dev`) so the in-memory adapter continues to work in development/test while the JPA-backed adapter with correct session lifecycle is activated in production.

**Justification:** The upgrade option is rated `moderate` effort and `medium` urgency. The risk is contained to the outbound persistence adapter boundary (hexagonal architecture isolates the domain from the fix). A feature-flag / profile-gated approach allows the fix to be validated in staging before production activation with zero downtime rollback.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 — Audit & Reproduce | Identify all call sites that open JPA sessions/transactions without guaranteed closure; reproduce leak under load in a Testcontainers integration test | Existing test harness, Testcontainers, PostgreSQL 15 | 1 person-day |
| 2 — JPA Adapter Implementation | Implement `JpaPaymentRepository` (Spring Data JPA) replacing `InMemoryPaymentRepository`; add `@Transactional` boundaries on `PaymentApplicationService` methods | Phase 1 findings, `spring-boot-starter-data-jpa`, Flyway migration | 2 person-days |
| 3 — Session Lifecycle Hardening | Configure HikariCP pool with validated connection settings; add `@Transactional(readOnly=true)` on read paths; ensure `EntityManager` is never held across async boundaries | Phase 2 complete, `application.properties` / `application.yml` | 1 person-day |
| 4 — Integration & Regression Testing | Extend Testcontainers suite to assert no leaked connections after each use-case; add connection pool metrics assertions | Phase 3 complete, JUnit 5, Testcontainers, Micrometer | 1 person-day |
| 5 — Staging Validation & Rollout | Activate `prod` Spring profile in staging; monitor HikariCP pool metrics; promote to production | Phase 4 green CI gate | 0.5 person-days |

**Total estimated effort: ~5.5 person-days** (derived from `moderate` option baseline).

---

## Component Changes

### `InMemoryPaymentRepository`
**File:** `payment-service/src/main/java/com/payments/adapters/outbound/persistence/InMemoryPaymentRepository.java`

- **What changes:** This class is retained for `dev`/`test` Spring profiles only. A new `JpaPaymentRepository` adapter is introduced for `prod` profile. No structural changes to the in-memory class itself.
- **APIs modified:** None — it continues to implement `PaymentRepositoryPort`.

---

### New: `JpaPaymentRepositoryAdapter`
**File (new):** `payment-service/src/main/java/com/payments/adapters/outbound/persistence/JpaPaymentRepositoryAdapter.java`

- **What changes:** New `@Repository` class implementing `PaymentRepositoryPort`. Wraps a Spring Data `JpaRepository<PaymentEntity, String>` interface. All public methods delegate to the Spring Data interface; the adapter handles domain↔entity conversion via `PaymentEntity.fromDomain()` / `PaymentEntity.toDomain()`.
- **APIs modified:** `PaymentEntity` gains JPA annotations (`@Entity`, `@Table`, `@Id`, `@Column`, `@Enumerated`). The existing `fromDomain()` / `toDomain()` factory methods are preserved unchanged.

---

### New: `SpringDataPaymentJpaRepository`
**File (new):** `payment-service/src/main/java/com/payments/adapters/outbound/persistence/SpringDataPaymentJpaRepository.java`

- **What changes:** `interface SpringDataPaymentJpaRepository extends JpaRepository<PaymentEntity, String>` with a `findByUserId(String userId)` derived query method.
- **APIs modified:** N/A — new interface.

---

### `PaymentApplicationService`
**File:** `payment-service/src/main/java/com/payments/application/service/PaymentApplicationService.java`

- **What changes:**
  - `process()` method annotated `@Transactional` — ensures the pending save, gateway call result update, and final save share a single transaction boundary; session is closed on method exit.
  - `getById()` (from `GetPaymentUseCase`) annotated `@Transactional(readOnly = true)` — prevents unnecessary dirty-checking and releases connection promptly.
  - `refund()` (from `RefundPaymentUseCase`) annotated `@Transactional`.
  - **Important:** Gateway calls (`stripeGateway.charge()`, `payPalGateway.charge()`) are external I/O and must **not** hold a database connection. The pattern is: open transaction → save PENDING → **commit/flush** → call gateway (outside transaction) → open new transaction → update status. This requires splitting `process()` into two transactional segments using `TransactionTemplate` or `@Transactional(propagation = REQUIRES_NEW)` on a helper method.
- **APIs modified:** `process(ProcessPaymentRequest)`, `getById(String)`, `refund(RefundRequest)` — all gain `@Transactional` annotations.

---

### `PaymentEntity`
**File:** `payment-service/src/main/java/com/payments/adapters/outbound/persistence/PaymentEntity.java`

- **What changes:** Add JPA annotations for the `prod` profile adapter. Use `@Entity`, `@Table(name = "payments")`, `@Id` on `id`, `@Enumerated(EnumType.STRING)` on `status` and `method`, `@Column` mappings for all fields.
- **APIs modified:** No method signatures change; annotations are additive.

---

### New: Flyway Migration
**File (new):** `payment-service/src/main/resources/db/migration/V1__create_payments_table.sql`

- **What changes:** Creates the `payments` table matching `PaymentEntity` field mappings.
- **APIs modified:** N/A.

---

### New: `PersistenceConfig`
**File (new):** `payment-service/src/main/java/com/payments/infrastructure/config/PersistenceConfig.java`

- **What changes:** `@Configuration` class that conditionally registers either `InMemoryPaymentRepository` (profiles: `dev`, `test`) or `JpaPaymentRepositoryAdapter` (profile: `prod`) as the `PaymentRepositoryPort` bean. Uses `@Profile` annotations.
- **APIs modified:** N/A — new class.

---

### `application.yml` / `application.properties`
**File:** `payment-service/src/main/resources/application.yml` (TODO: confirm exact filename from project)

- **What changes:** Add HikariCP pool configuration:
  ```yaml
  spring:
    datasource:
      hikari:
        maximum-pool-size: 10
        minimum-idle: 2
        connection-timeout: 30000
        idle-timeout: 600000
        max-lifetime: 1800000
        leak-detection-threshold: 60000   # key: surfaces unreturned connections
    jpa:
      open-in-view: false                 # key: prevents OSIV from holding connections across HTTP lifecycle
      hibernate:
        ddl-auto: validate
    flyway:
      enabled: true
  ```
- **Config keys modified:** `spring.jpa.open-in-view`, `spring.datasource.hikari.*`, `spring.flyway.enabled`.

---

## Dependency Upgrade Plan

The provided tech analysis does not supply explicit version numbers for the dependencies involved. The stack is Spring Boot 3.x on Java 21 with PostgreSQL 15. The following table reflects what is derivable from context:

| Dependency | Current Version | Target Version | Breaking Changes | Migration Notes |
|---|---|---|---|---|
| `spring-boot-starter-data-jpa` | Not present in context (in-memory repo used) | Same Spring Boot 3.x BOM version as existing starters | None — additive | Add to `pom.xml`; BOM manages version |
| `postgresql` JDBC driver | TODO — not specified in context | TODO — match PostgreSQL 15 compatible driver from Spring Boot 3.x BOM | None expected | Add `org.postgresql:postgresql` to `pom.xml` under BOM management |
| `flyway-core` | TODO — not specified in context | TODO — Flyway version from Spring Boot 3.x BOM | None expected | Add `org.flywaydb:flyway-core`; configure `spring.flyway.*` |
| HikariCP | Bundled with Spring Boot 3.x | No change — already default pool | N/A | Configure via `application.yml` only |

> **Note:** All version numbers are marked TODO because the tech analysis states versions as unknown and the `pom.xml` is not included in the provided context. Do not pin versions manually — rely on the Spring Boot 3.x BOM.

---

## Infrastructure Changes

### Docker
- **`payment-service/Dockerfile`:** No base image change required. Java 21 image already in use per AGENTS.md. Ensure `SPRING_PROFILES_ACTIVE=prod` is set as an environment variable in the production Docker image run command or `docker-compose.yml`.

### Docker Compose
- **`docker-compose.yml`:** Add `SPRING_PROFILES_ACTIVE=prod` to the `payment-service` environment block. Confirm `postgres` service is defined and `payment-service` has a `depends_on: postgres` entry.
- **`docker-compose.test.yml`:** Set `SPRING_PROFILES_ACTIVE=test` to keep in-memory adapter active for isolated test runs.

### CI/CD — GitHub Actions
- **`.github/workflows/ci.yml`:** Add a step to run Testcontainers-based integration tests with `SPRING_PROFILES_ACTIVE=test`. Add a connection-leak assertion step (see Testing Strategy). No pipeline structural changes required.

### Kubernetes / IaC
- TODO — no Kubernetes manifests or IaC files are present in the provided context.

---

## Rollback Strategy

### Phase 1 Rollback
- No code changes shipped. Rollback = close the audit branch. No action required in production.

### Phase 2 Rollback
- `JpaPaymentRepositoryAdapter` and `SpringDataPaymentJpaRepository` are new files behind the `prod` Spring profile. Rollback: set `SPRING_PROFILES_ACTIVE=dev` (or remove the `prod` profile activation) in the deployment environment. The `InMemoryPaymentRepository` bean re-activates automatically. No database schema changes are applied until Phase 2 is promoted to an environment running Flyway against a real PostgreSQL instance.
- Flyway migration `V1__create_payments_table.sql`: if already applied, rollback requires a manual `DROP TABLE payments;` or a Flyway undo migration (`V1.1__drop_payments_table.sql`). **Gate Phase 2 promotion behind a staging environment to avoid applying Flyway to production prematurely.**

### Phase 3 Rollback
- HikariCP and JPA config changes are in `application.yml`. Rollback: revert the config file commit and redeploy. The `leak-detection-threshold` and `open-in-view` settings are non-destructive to revert.
- `@Transactional` annotations on `PaymentApplicationService`: revert the commit. Spring Boot will redeploy without transactional proxies.

### Phase 4 Rollback
- Test-only changes. Rollback: revert test files. No production impact.

### Phase 5 Rollback
- If production metrics show pool exhaustion after `prod` profile activation: set `SPRING_PROFILES_ACTIVE=dev` in the deployment and redeploy. Service reverts to in-memory store. **Note:** any payments persisted to PostgreSQL during the `prod` window will not be visible in the in-memory store — coordinate with operations on data continuity before rollback.

---

## Testing Strategy

### Unit Tests
- **Tool:** JUnit 5 + Mockito (already in stack per AGENTS.md)
- **Scope:** `PaymentApplicationService` — mock `PaymentRepositoryPort`, `StripeGatewayPort`, `PayPalGatewayPort`, `NotificationPort`. Assert that `save()` is called before gateway invocation and `update()` is called after. Assert `@Transactional` boundary does not hold a connection during the gateway call (verify via mock interaction order).
- **Coverage target:** 90% line coverage on `PaymentApplicationService`.
- **Files:** `payment-service/src/test/java/com/payments/application/service/PaymentApplicationServiceTest.java`

### Integration Tests
- **Tool:** JUnit 5 + Testcontainers (PostgreSQL 15 container) — already in stack per AGENTS.md
- **Scope:**
  - `JpaPaymentRepositoryAdapter` — assert `save()`, `findById()`, `findByUserId()`, `update()` against a real PostgreSQL 15 container.
  - `PaymentApplicationService` with real JPA adapter — assert no open sessions after `process()`, `getById()`, `refund()` complete.
  - HikariCP leak detection — assert `HikariPoolMXBean.getActiveConnections() == 0` after each use-case call completes.
- **Coverage target:** All four `PaymentRepositoryPort` methods covered by at least one integration test.
- **Files:** `payment-service/src/test/java/com/payments/adapters/outbound/persistence/JpaPaymentRepositoryAdapterIT.java`

### Regression Tests
- **Tool:** Supertest (Node.js gateway) + Spring MockMvc / `@SpringBootTest` with `WebEnvironment.RANDOM_PORT`
- **Scope:** Existing `PaymentController` endpoint contracts (`POST /api/payments`, `GET /api/payments/{id}`, `POST /api/payments/{id}/refund`) must return identical HTTP status codes and response shapes before and after the persistence layer swap.
- **CI gate:** Regression suite must pass before the `prod` profile is activated in staging.

### Performance / Connection Pool Tests
- **Tool:** TODO — no load testing tool is specified in context. Recommend adding a simple JMeter or Gatling script (TODO: confirm tooling availability).
- **Scope:** Sustained 50 concurrent requests to `POST /api/payments` for 60 seconds. Assert `HikariPoolMXBean.getActiveConnections()` returns to 0 within 5 seconds of load stopping. Assert no `Connection is not available, request timed out` exceptions in logs.
- **CI gate:** Run as a nightly job in GitHub Actions (`.github/workflows/ci.yml`) against the Testcontainers environment; fail the build if leaked connections are detected.

### CI Gates Summary
| Gate | Phase | Condition |
|---|---|---|
| Unit test coverage ≥ 90% on `PaymentApplicationService` | Phase 2 | Block merge |
| All integration tests green (Testcontainers) | Phase 3 | Block merge |
| Zero active HikariCP connections post-request assertion | Phase 3 | Block merge |
| Regression suite green | Phase 4 | Block staging promotion |
| Performance test: no leak under 50 concurrent users | Phase 5 | Block production promotion |

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| Audit complete; leak reproduction test committed | Phase 1 | End of Day 1 | TODO |
| `JpaPaymentRepositoryAdapter` + `PaymentEntity` JPA annotations + Flyway V1 migration merged | Phase 2 | End of Day 3 | TODO |
| `@Transactional` boundaries on `PaymentApplicationService`; HikariCP + `open-in-view=false` config merged | Phase 3 | End of Day 4 | TODO |
| Integration + regression + connection-pool CI tests green | Phase 4 | End of Day 5 | TODO |
| Staging validation complete; production rollout approved | Phase 5 | End of Day 5 (afternoon) | TODO |

> Effort derived from the `moderate` upgrade option (~5.5 person-days total). All owners marked TODO — assign during sprint planning.