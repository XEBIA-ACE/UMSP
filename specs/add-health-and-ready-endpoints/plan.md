# Plan: Add /health and /ready Endpoints

## Overview

**Migration strategy: Feature-flag gated / incremental addition**

The `/health` endpoint already exists in both services (`payment-service` at `GET /api/health` and `user-management` at `GET /api/health`). The primary gap is the absence of a dedicated `/ready` (readiness) endpoint in either service. The work is additive — no existing code is removed or restructured — making a simple incremental delivery appropriate.

Risk is low: the existing liveness endpoint pattern is already proven in both codebases, security bypass rules are already in place (`SecurityConfig.java` permits `/api/health/**`; the Node.js service has no auth on health routes), and the test harness is established. The moderate effort estimate from the upgrade option reflects the need to add readiness logic (dependency checks) alongside the trivial liveness path.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 | Audit existing `/health` endpoints; confirm they are reachable and tests pass as-is | None | 0.5 person-days |
| 2 | Add `GET /api/ready` to `payment-service` (Spring Boot) with dependency checks | Phase 1 complete | 1 person-day |
| 3 | Add `GET /api/ready` to `user-management` (Node.js/Express) with dependency checks | Phase 1 complete | 1 person-day |
| 4 | Update security config, route registration, and README endpoint tables | Phases 2 & 3 | 0.5 person-days |
| 5 | Write and run tests; update CI gates | Phases 2, 3 & 4 | 1 person-day |

**Total: ~4 person-days**

---

## Component Changes

### `payment-service` — `HealthController.java`

**File:** `payment-service/src/main/java/com/payments/adapters/inbound/rest/HealthController.java`

- **Current state:** Single `@GetMapping` on `/api/health` returning `{ status, service, timestamp }`.
- **Change:** Add a second handler method `ready()` mapped to `@GetMapping("/ready")` at the path `/api/health/ready` (consistent with the existing `@RequestMapping("/api/health")` base path and the wildcard permit in `SecurityConfig`).
- **Readiness logic:** The readiness check should verify that downstream dependencies (e.g., the payment repository, any gateway clients) are reachable. At minimum, inject a dependency indicator (e.g., a simple `ApplicationContext` health flag or a dedicated `ReadinessChecker` component) and return `503 Service Unavailable` when not ready.
- **New method signature:**

```java
@GetMapping("/ready")
public ResponseEntity<Map<String, String>> ready() { ... }
```

- **Return `200 OK`** with `{ "status": "ready", "service": "payment-service", "timestamp": "..." }` when ready.
- **Return `503 Service Unavailable`** with `{ "status": "not_ready", ... }` when dependencies are unavailable.

### `payment-service` — `SecurityConfig.java`

**File:** `payment-service/src/main/java/com/payments/infrastructure/config/SecurityConfig.java`

- **No change required.** The existing rule `.requestMatchers("/api/health/**").permitAll()` already covers `/api/health/ready` via the `**` wildcard.

### `user-management` — `HealthController.js`

**File:** `user-management/src/adapters/inbound/http/controllers/HealthController.js`

- **Current state:** Single `check()` method returning `{ status, service, timestamp }`.
- **Change:** Add a `ready()` method that performs a lightweight dependency check (e.g., verifying the in-memory store is accessible, or a configurable external ping) and responds with `200` or `503`.

```js
ready(_req, res) {
  // dependency check logic
  res.status(200).json({ status: 'ready', service: 'user-management', timestamp: new Date().toISOString() });
}
```

### `user-management` — `healthRoutes.js`

**File:** `user-management/src/adapters/inbound/http/routes/healthRoutes.js`

- **Change:** Register the new route:

```js
/** GET /api/health/ready */
router.get('/ready', controller.ready.bind(controller));
```

### `README.md`

- Add `GET /api/health/ready` rows to the endpoint tables for both services.

---

## Dependency Upgrade Plan

N/A — not applicable to this task. No dependency version changes are required. All existing dependencies (`express ^4.18.2`, `jest ^29.7.0`, `supertest ^6.3.3`, Spring Boot 3.2, Spring Security) already support the additive endpoint work.

---

## Infrastructure Changes

### Kubernetes / Orchestration

The new `/ready` endpoint is specifically designed for Kubernetes readiness probes. Once deployed, Kubernetes manifests should be updated to reference it:

```yaml
# payment-service Deployment
readinessProbe:
  httpGet:
    path: /api/health/ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5

livenessProbe:
  httpGet:
    path: /api/health
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
```

```yaml
# user-management Deployment
readinessProbe:
  httpGet:
    path: /api/health/ready
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 5

livenessProbe:
  httpGet:
    path: /api/health
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 10
```

> **TODO:** Kubernetes manifest file paths are not present in the provided context. Locate and update the relevant `Deployment` YAML files in the repository.

### Docker

No Docker base image changes required.

### CI/CD

**File:** `.github/workflows/ci.yml`

- Ensure the existing test jobs (`npm test` for `user-management`, `./mvnw test` for `payment-service`) run the new readiness endpoint tests as part of the standard pipeline. No structural CI changes are needed beyond confirming coverage gates (see Testing Strategy).

> **TODO:** Confirm the exact job names and step structure in `.github/workflows/ci.yml` — file content not provided in context.

---

## Rollback Strategy

Each phase is independently reversible because all changes are purely additive.

| Phase | Rollback Steps |
|---|---|
| Phase 2 (payment-service `/ready`) | Remove the `ready()` method from `HealthController.java` and its corresponding test in `HealthControllerTest.java`. Revert via `git revert` or delete the method and redeploy. `SecurityConfig.java` requires no rollback. |
| Phase 3 (user-management `/ready`) | Remove the `ready()` method from `HealthController.js` and the `router.get('/ready', ...)` line from `healthRoutes.js`. Remove the corresponding test block from `health.test.js`. Redeploy. |
| Phase 4 (security/routes/README) | Revert README changes. Route and security changes are already covered by Phase 2/3 rollbacks. |
| Phase 5 (tests/CI) | Test files can be reverted independently without affecting runtime behaviour. |

No database migrations, schema changes, or infrastructure state changes are involved, so rollback at any phase carries zero data-loss risk.

---

## Testing Strategy

### Unit Tests

**`user-management`** — extend `user-management/src/__tests__/health.test.js`:
- `GET /api/health/ready` returns `200` with `{ status: 'ready', service: 'user-management' }` when dependencies are healthy.
- `GET /api/health/ready` returns `503` when a simulated dependency failure is injected.
- Response `Content-Type` is `application/json`.
- Tool: **Jest 29** + **Supertest 6**.

**`payment-service`** — extend `payment-service/src/test/java/com/payments/adapters/inbound/rest/HealthControllerTest.java`:
- `GET /api/health/ready` returns `200` with `status: "ready"` under normal conditions.
- `GET /api/health/ready` returns `503` when a mocked dependency is unavailable (use `@MockBean`).
- Tool: **JUnit 5** + **Spring Boot Test** (`@SpringBootTest` + `@AutoConfigureMockMvc`) with the existing `TestSecurityConfig` override.

### Integration Tests

- Verify `/api/health/ready` is reachable without authentication credentials in both services (confirming security permit rules work end-to-end).
- For `payment-service`, use **Testcontainers** (already in stack per `AGENTS.md`) if the readiness check involves a real DB or Redis connection.

### Regression Tests

- Re-run the full existing test suites after changes to confirm `GET /api/health` (liveness) behaviour is unaffected.
- Confirm `GET /api/payments/**` still requires JWT (no accidental security rule widening).

### Coverage Targets & CI Gates

| Service | Tool | Minimum Coverage Target | CI Gate |
|---|---|---|---|
| `user-management` | Jest `--coverage` | 80% lines (existing baseline) | Fail build if below threshold |
| `payment-service` | Maven Surefire / JaCoCo | 80% lines (existing baseline) | Fail build if below threshold |

Coverage is already collected via `npm test` (`jest --coverage`) and `./mvnw test`. No new tooling is required — add coverage thresholds to `jest` config in `package.json` and to the Maven `jacoco-maven-plugin` configuration in `pom.xml` if not already enforced.

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| Audit existing `/health` endpoints; confirm green tests | Phase 1 | Day 1 | TODO |
| `payment-service` `/ready` endpoint implemented | Phase 2 | Day 2 | TODO |
| `user-management` `/ready` endpoint implemented | Phase 3 | Day 2 | TODO |
| Security config, routes, and README updated | Phase 4 | Day 3 | TODO |
| All tests written, passing, and CI gates enforced | Phase 5 | Day 4 | TODO |
| Kubernetes readiness probe manifests updated | Phase 4 | Day 4 | TODO |