# Spec: Add /health and /ready Endpoints

## Summary

This spec covers the addition of liveness (`/health`) and readiness (`/ready`) probe endpoints to both the `user-management` (Node.js 20 / Express 4) and `payment-service` (Java 17 / Spring Boot 3.2) microservices. The `user-management` service already exposes `GET /api/health`; the `payment-service` already exposes `GET /api/health`. The expected outcome is that both services expose a consistent, unauthenticated `/api/health` (liveness) endpoint and a new `/api/ready` (readiness) endpoint, enabling orchestration platforms such as Kubernetes to perform reliable liveness and readiness probing against both services.

---

## Motivation

- **Operational requirement:** Container orchestrators (e.g. Kubernetes) require distinct liveness and readiness probes. A single combined endpoint cannot express the difference between "the process is alive" and "the service is ready to accept traffic" (e.g. database connection established, downstream dependencies reachable).
- **Current gap:** Both services expose only a liveness-style `GET /api/health` endpoint. Neither service exposes a dedicated `/api/ready` endpoint. Without a readiness probe, orchestrators cannot safely gate traffic during startup or graceful shutdown.
- **Upgrade urgency:** Medium — no CVE or EOL driver; the gap creates operational risk during rolling deployments and restarts.
- **Tech debt:** The existing `GET /api/health` endpoint in both services returns a static `"status": "ok"` payload with no dependency checks, making it unsuitable for use as a readiness signal.

---

## Current State

### `user-management` (Node.js 20 · Express 4 · port 3000)

| Element | Detail |
|---|---|
| Controller class | `HealthController` (`src/adapters/inbound/http/controllers/HealthController.js`) |
| Route registration | `createHealthRouter()` (`src/adapters/inbound/http/routes/healthRoutes.js`) mounts `GET /` under the `/api/health` prefix |
| Mounted path | `GET /api/health` |
| Response shape | `{ status: "ok", service: "user-management", timestamp: "<ISO-8601>" }` |
| HTTP status | `200 OK` |
| Auth requirement | None (unauthenticated) |
| Readiness endpoint | **Does not exist** |
| Existing tests | `src/__tests__/health.test.js` — covers status 200, JSON content-type, ISO timestamp |

### `payment-service` (Java 17 · Spring Boot 3.2 · port 8080)

| Element | Detail |
|---|---|
| Controller class | `HealthController` (`com.payments.adapters.inbound.rest.HealthController`) |
| Request mapping | `@RequestMapping("/api/health")` with `@GetMapping` on `health()` method |
| Response shape | `{ "status": "ok", "service": "payment-service", "timestamp": "<ISO-8601>" }` |
| HTTP status | `200 OK` |
| Auth requirement | None — `SecurityConfig` permits `/api/health/**` without authentication |
| Security config | `com.payments.infrastructure.config.SecurityConfig` — `requestMatchers("/api/health/**").permitAll()` |
| Readiness endpoint | **Does not exist** |
| Existing tests | `HealthControllerTest` — `@SpringBootTest` with `TestSecurityConfig` overriding auth; covers status 200, `status: ok`, `service: payment-service`, non-empty timestamp |

---

## Proposed Changes

### Overview

Both services require a new `GET /api/ready` endpoint. The existing `GET /api/health` endpoint is retained unchanged as the liveness probe. The readiness probe must reflect whether the service is ready to serve traffic (dependency checks are in scope; specific dependencies are noted as TODO where not confirmed by context).

### Component Table

| Component | Before | After | Breaking? |
|---|---|---|---|
| `user-management` — `HealthController.js` | Exposes `check()` for liveness only | Adds `ready()` method for readiness check | N |
| `user-management` — `healthRoutes.js` | Registers `GET /` (→ `/api/health`) | Also registers `GET /ready` (→ `/api/ready`) | N |
| `user-management` — health test file | Tests `GET /api/health` only | Adds tests for `GET /api/ready` | N |
| `payment-service` — `HealthController.java` | `@GetMapping` on `health()` at `/api/health` | Adds `@GetMapping("/ready")` method `ready()` at `/api/health/ready` | N |
| `payment-service` — `SecurityConfig.java` | Permits `/api/health/**` | No change required — wildcard already covers `/api/health/ready` | N |
| `payment-service` — `HealthControllerTest.java` | Tests `GET /api/health` only | Adds tests for `GET /api/health/ready` | N |
| README.md endpoint tables | Lists `GET /api/health` for both services | Adds `GET /api/ready` (user-management) and `GET /api/health/ready` (payment-service) | N |

### Endpoint Paths

| Service | Liveness (existing) | Readiness (new) |
|---|---|---|
| `user-management` | `GET /api/health` | `GET /api/ready` |
| `payment-service` | `GET /api/health` | `GET /api/health/ready` |

> **Note:** The `payment-service` readiness endpoint is placed at `/api/health/ready` because `HealthController` is already mapped to `/api/health` and the existing `SecurityConfig` wildcard `"/api/health/**"` covers it without modification. The `user-management` readiness endpoint is placed at `/api/ready` to match the flat routing convention already used in that service.

### Response Shape — Readiness Endpoint

Both services shall return a JSON body on the readiness endpoint:

- **When ready:** HTTP `200 OK` with `{ "status": "ready", "service": "<service-name>", "timestamp": "<ISO-8601>" }`
- **When not ready:** HTTP `503 Service Unavailable` with `{ "status": "unavailable", "service": "<service-name>", "timestamp": "<ISO-8601>", "reason": "<human-readable description>" }`

### Dependency Checks for Readiness

The readiness probe should verify that the service can serve traffic. Specific checks:

| Service | Dependency to check | Source confirmation |
|---|---|---|
| `user-management` | TODO — no database or external dependency confirmed in provided context for this service | TODO |
| `payment-service` | TODO — `InMemoryPaymentRepository` is in use (no real DB); Stripe/PayPal gateway reachability check scope TBD | TODO |

> If no dependency checks are implemented in the initial iteration, the readiness endpoint may return `200 ready` unconditionally, matching the liveness behaviour, and dependency checks can be added incrementally. This must be agreed with the owning team.

---

## Compatibility & Breaking Changes

| Change | Impact | Migration Path |
|---|---|---|
| New `GET /api/ready` route in `user-management` | Additive — no existing callers affected | None required |
| New `GET /api/health/ready` route in `payment-service` | Additive — no existing callers affected | None required |
| `SecurityConfig` wildcard `/api/health/**` already covers `/api/health/ready` | No change to security rules needed | None required |
| Readiness endpoint returns `503` when not ready | New behaviour — callers (orchestrators) must handle `503` | Kubernetes liveness/readiness probe configuration should use `failureThreshold` and `periodSeconds` appropriate for the service startup time |
| `GET /api/health` liveness endpoint | Unchanged | None required |

---

## Acceptance Criteria

### `user-management` — Liveness (existing, must remain passing)

1. Given the `user-management` service is running, when a client sends `GET /api/health` without an `Authorization` header, then the response status is `200 OK`, the `Content-Type` header matches `application/json`, and the body contains `{ "status": "ok", "service": "user-management" }` with a non-empty `timestamp` field that parses as a valid ISO-8601 date-time string.

### `user-management` — Readiness (new)

2. Given the `user-management` service is running and all required dependencies are reachable, when a client sends `GET /api/ready` without an `Authorization` header, then the response status is `200 OK`, the `Content-Type` header matches `application/json`, and the body contains `{ "status": "ready", "service": "user-management" }` with a non-empty `timestamp` field that parses as a valid ISO-8601 date-time string.

3. Given the `user-management` service is running but a required dependency is unavailable, when a client sends `GET /api/ready`, then the response status is `503 Service Unavailable` and the body contains `{ "status": "unavailable" }` with a non-empty `reason` field.

4. Given the `user-management` service is running, when a client sends `GET /api/ready` without an `Authorization` header, then the request is not rejected with `401 Unauthorized` or `403 Forbidden` (the endpoint is publicly accessible).

### `payment-service` — Liveness (existing, must remain passing)

5. Given the `payment-service` is running, when a client sends `GET /api/health` without a JWT bearer token, then the response status is `200 OK`, the `Content-Type` header matches `application/json`, and the body contains `{ "status": "ok", "service": "payment-service" }` with a non-empty `timestamp` field.

### `payment-service` — Readiness (new)

6. Given the `payment-service` is running and all required dependencies are reachable, when a client sends `GET /api/health/ready` without a JWT bearer token, then the response status is `200 OK`, the `Content-Type` header matches `application/json`, and the body contains `{ "status": "ready", "service": "payment-service" }` with a non-empty `timestamp` field that parses as a valid ISO-8601 date-time string.

7. Given the `payment-service` is running but a required dependency is unavailable, when a client sends `GET /api/health/ready`, then the response status is `503 Service Unavailable` and the body contains `{ "status": "unavailable" }` with a non-empty `reason` field.

8. Given the `payment-service` is running, when a client sends `GET /api/health/ready` without a JWT bearer token, then the request is not rejected with `401 Unauthorized` or `403 Forbidden` (the `SecurityConfig` permits `/api/health/**` without authentication, which covers this path).

### CI

9. Given the CI pipeline runs, when all unit and integration tests execute, then all existing tests for `HealthController` (both services) continue to pass and new tests for the `/ready` endpoint achieve at least the same coverage level as the existing health tests.

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | What specific dependency checks should the `user-management` readiness probe perform? (e.g. database ping, Redis connectivity) The provided context shows only an in-memory repository — is a real DB expected before this work lands? | TODO | TODO |
| 2 | What specific dependency checks should the `payment-service` readiness probe perform? Should it verify Stripe/PayPal gateway reachability, or only internal state (e.g. application context started)? | TODO | TODO |
| 3 | Should the readiness endpoint return `200` unconditionally in the initial iteration (matching liveness behaviour) with dependency checks added in a follow-up, or must dependency checks be included in this iteration? | TODO | TODO |
| 4 | The `user-management` readiness path is proposed as `/api/ready` (flat) while `payment-service` uses `/api/health/ready` (nested). Should both services use the same path convention for consistency? | TODO | TODO |
| 5 | Should the readiness response body include a structured `checks` array (one entry per dependency) or is a single `reason` string sufficient for the initial implementation? | TODO | TODO |
| 6 | Are there any API gateway or load-balancer routing rules that need updating to pass through the new `/api/ready` and `/api/health/ready` paths? | TODO | TODO |