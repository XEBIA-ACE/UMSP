# Plan: Add /health and /ready Endpoints

## Overview

**Migration strategy: Feature-flag gated / incremental addition**

The `/health` endpoint already exists in both services (`payment-service` at `GET /api/health` and `user-management` at `GET /api/health`). The primary remaining work is adding a distinct `/ready` (readiness) endpoint to each service, ensuring both endpoints are correctly secured (unauthenticated), and wiring them into any orchestration probes.

Because the liveness endpoint is already live and tested, this is a low-risk, additive change. No existing code needs to be deleted or restructured. The effort is small (estimated 2–4 person-days for the "moderate" option across both services), making a simple incremental delivery the right approach — no strangler-fig or parallel-run complexity is warranted.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 | Audit existing `/health` endpoints; confirm they are reachable without auth in both services | None | 0.25 person-days |
| 2 | Add `GET /api/ready` to `payment-service` (Java/Spring Boot) | Phase 1 | 0.75 person-days |
| 3 | Add `GET /api/ready` to `user-management` (Node.js/Express) | Phase 1 | 0.75 person-days |
| 4 | Update security configuration to permit `/api/ready/**` without authentication | Phases 2–3 | 0.25 person-days |
| 5 | Write/extend tests for both new endpoints | Phases 2–4 | 0.5 person-days |
| 6 | Update README endpoint tables and any orchestration probe config | Phase 5 | 0.25 person-days |

**Total: ~2.75 person-days**

---

## Component Changes

### `payment-service` — Java / Spring Boot

#### `HealthController.java`
**File:** `payment-service/src/main/java/com/payments/adapters/inbound/rest/HealthController.java`

- Add a new `@GetMapping("/ready")` method `ready()` alongside the existing `health()` method.
- The readiness check should verify that the service's critical dependencies (e.g. payment repository) are reachable. For the current in-memory implementation, this can return `"status": "ready"` immediately; a TODO comment should mark where real dependency checks (DB, external gateways) belong.
- Return `200 OK` when ready, `503 Service Unavailable` when not.

```java
@GetMapping("/ready")
public ResponseEntity<Map<String, String>> ready() {
    // TODO: check DB connectivity, gateway reachability, etc.
    Map<String, String> body = Map.of(
        "status", "ready",
        "service", "payment-service",
        "timestamp", Instant.now().toString()
    );
    return ResponseEntity.ok(body);
}
```

No new class is required; the existing `HealthController` class at base path `/api/health` will expose `/api/health/ready`.

#### `SecurityConfig.java`
**File:** `payment-service/src/main/java/com/payments/infrastructure/config/SecurityConfig.java`

- The existing rule `.requestMatchers("/api/health/**").permitAll()` already covers `/api/health/ready` via the `/**` wildcard.
- **No change required** — confirm this is the case during Phase 1 audit.

---

### `user-management` — Node.js / Express

#### `HealthController.js`
**File:** `user-management/src/adapters/inbound/http/controllers/HealthController.js`

- Add a `ready(_req, res)` method to the `HealthController` class.
- The readiness check should verify critical dependencies are available. For the current in-memory implementation, return `"status": "ready"` immediately; mark with a TODO for real checks.
- Return `200 OK` when ready, `503 Service Unavailable` when not.

```js
ready(_req, res) {
  // TODO: check DB connectivity, external service reachability, etc.
  res.status(200).json({
    status: 'ready',
    service: 'user-management',
    timestamp: new Date().toISOString(),
  });
}
```

#### `healthRoutes.js`
**File:** `user-management/src/adapters/inbound/http/routes/healthRoutes.js`

- Add a new route binding inside `createHealthRouter()`:

```js
/** GET /api/health/ready */
router.get('/ready', controller.ready.bind(controller));
```

No new files are required; the existing router mounts at `/api/health`, so the new route resolves to `GET /api/health/ready`.

---

## Dependency Upgrade Plan

N/A — not applicable to this task. No dependency version changes are required. All existing dependencies (`express ^4.18.2`, Spring Boot 3.x, Spring Security) already support the required functionality.

---

## Infrastructure Changes

### Kubernetes / Orchestration Probes

TODO — Kubernetes manifests are not present in the provided context. Once the endpoints are live, the following probe configuration should be added to each service's Deployment manifest:

**payment-service** (port `8080`):
```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 8080
readinessProbe:
  httpGet:
    path: /api/health/ready
    port: 8080
```

**user-management** (port `3000`):
```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 3000
readinessProbe:
  httpGet:
    path: /api/health/ready
    port: 3000
```

### Docker

No base image changes required. TODO — confirm that Docker health-check `HEALTHCHECK` directives in each service's `Dockerfile` reference the correct paths if they exist.

### CI/CD

TODO — `.github/workflows/ci.yml` is referenced in `AGENTS.md` but not provided. Add a smoke-test step post-deploy that curls both `/api/health` and `/api/health/ready` and asserts `HTTP 200`.

---

## Rollback Strategy

Each phase is independently reversible because all changes are purely additive.

| Phase | Rollback Action |
|---|---|
| Phase 2 (payment-service `/ready`) | Remove the `ready()` method from `HealthController.java` and redeploy. No other files are affected. |
| Phase 3 (user-management `/ready`) | Remove the `ready()` method from `HealthController.js` and the `router.get('/ready', ...)` line from `healthRoutes.js`, then redeploy. |
| Phase 4 (security config) | No security changes are needed (existing `/**` wildcard covers the new path). If any security rule was added, revert the specific `requestMatchers` line in `SecurityConfig.java`. |
| Phase 6 (probe config) | Revert Kubernetes manifest changes via `kubectl apply` of the previous manifest version or via Git revert + CI redeploy. |

No database migrations, schema changes, or data transformations are involved. Any phase can be reverted by reverting the relevant commit and redeploying.

---

## Testing Strategy

### Unit Tests

**payment-service:**
- Extend `HealthControllerTest.java` with a test for `GET /api/health/ready`.
- Assert: `HTTP 200`, `Content-Type: application/json`, `$.status == "ready"`, `$.service == "payment-service"`, `$.timestamp` is non-empty.
- Use the existing `@TestConfiguration` / `TestSecurityConfig` pattern already in place.

**user-management:**
- Extend `health.test.js` (at `user-management/src/__tests__/health.test.js`) with a `describe('GET /api/health/ready')` block.
- Assert: `res.status === 200`, `res.body.status === 'ready'`, `res.body.service === 'user-management'`, valid ISO timestamp, `Content-Type: application/json`.
- Use the existing `supertest` + `createApp()` pattern already in place.

### Integration Tests

- Both test files already use full application context (`@SpringBootTest` / `createApp()`), so the new tests are integration-level by default.
- Verify that the `/ready` endpoint is reachable **without** an `Authorization` header (confirms security permit-all is working).

### Regression Tests

- Re-run the full existing test suites (`./mvnw test` for payment-service, `npm test` for user-management) to confirm no existing behaviour is broken.
- Coverage target: maintain existing coverage levels; the new `ready()` methods must be covered by the new tests.

### Performance Tests

N/A — health/readiness endpoints are trivial in-memory responses. No performance regression risk.

### CI Gates

- Both `./mvnw test` and `npm test --coverage` must pass before merge.
- TODO — add a CI step in `.github/workflows/ci.yml` that asserts `HTTP 200` from both `/api/health` and `/api/health/ready` in the integration test environment.
- Coverage must not drop below the current baseline (enforced by existing Jest `--coverage` and Maven Surefire configuration).

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| Audit existing `/health` endpoints | Phase 1 | Day 1 | TODO |
| `GET /api/health/ready` live in payment-service | Phase 2 | Day 1 | TODO |
| `GET /api/health/ready` live in user-management | Phase 3 | Day 1 | TODO |
| Security config confirmed / updated | Phase 4 | Day 1 | TODO |
| Tests written and passing in CI | Phase 5 | Day 2 | TODO |
| README and probe config updated | Phase 6 | Day 2 | TODO |