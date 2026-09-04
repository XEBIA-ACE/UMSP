# Spec: Add /health and /ready Endpoints

## Summary

This spec covers the addition of standardised liveness (`/health`) and readiness (`/ready`) HTTP probe endpoints to both the `user-management` service (Node.js 20 / Express 4) and the `payment-service` (Java 17 / Spring Boot 3.2). The `user-management` service already exposes `GET /api/health`; the `payment-service` already exposes `GET /api/health`. The expected outcome is that both services expose a consistent, unauthenticated `/api/health` (liveness) endpoint and a new `/api/ready` (readiness) endpoint, enabling orchestration platforms such as Kubernetes to distinguish between a process that is alive and one that is fully ready to serve traffic.

---

## Motivation

- **Operational requirement (medium urgency):** Both services are deployed in containerised environments (Docker / Kubernetes per `README.md` and `AGENTS.md`). Kubernetes requires separate liveness and readiness probes to correctly manage pod lifecycle. Without a `/ready` endpoint, the platform cannot distinguish a starting-up or degraded service from a healthy one, risking traffic being routed to unready pods.
- **Consistency gap:** The `user-management` service and `payment-service` each have a `/api/health` liveness endpoint, but neither exposes a `/api/ready` readiness endpoint. The two existing `/api/health` implementations share the same response contract (`status`, `service`, `timestamp`) but are not formally specified, creating a risk of divergence.
- **Tech debt:** The `payment-service` `SecurityConfig` explicitly permits `/api/health/**` but has no rule for a readiness path. Any new probe path must be added to the security allowlist to remain accessible without authentication.

---

## Current State

### user-management (Node.js 20 / Express 4)

| Element | Detail |
|---|---|
| Controller class | `HealthController` (`user-management/src/adapters/inbound/http/controllers/HealthController.js`) |
| Method | `check(_req, res)` |
| Route file | `healthRoutes.js` — mounts `GET /` on a sub-router, registered at `/api/health` |
| Response shape | `{ status: "ok", service: "user-management", timestamp: <ISO-8601 string> }` |
| HTTP status | `200 OK` |
| Auth | No authentication required (no middleware applied to health routes) |
| Test file | `user-management/src/__tests__/health.test.js` — covers status, timestamp format, and Content-Type |
| Missing | No `GET /api/ready` endpoint exists |

### payment-service (Java 17 / Spring Boot 3.2)

| Element | Detail |
|---|---|
| Controller class | `HealthController` (`payment-service/src/main/java/com/payments/adapters/inbound/rest/HealthController.java`) |
| Mapping | `@RequestMapping("/api/health")`, `@GetMapping` on `health()` method |
| Response shape | `Map<String, String>` with keys `status`, `service`, `timestamp` |
| HTTP status | `200 OK` |
| Auth | `SecurityConfig` permits `/api/health/**` without authentication; all other requests require JWT or are denied |
| Test file | `HealthControllerTest.java` — `@SpringBootTest` with `TestSecurityConfig` overriding auth; covers status, service name, timestamp presence |
| Missing | No `GET /api/ready` endpoint exists; `SecurityConfig` has no rule for `/api/ready/**` |

---

## Proposed Changes

### user-management

| Component | Before | After | Breaking? |
|---|---|---|---|
| `HealthController.js` | Single `check()` method serving liveness only | Add `ready()` method returning readiness status | N |
| `healthRoutes.js` | `GET /` → liveness | Add `GET /ready` → readiness | N |
| Response contract (`/api/health`) | `{ status, service, timestamp }` | Unchanged | N |
| Response contract (`/api/ready`) | Does not exist | `{ status: "ok" \| "unavailable", service, timestamp }` with `200` or `503` | N (new) |
| Test file `health.test.js` | Covers `/api/health` only | Add test cases for `GET /api/ready` | N |

### payment-service

| Component | Before | After | Breaking? |
|---|---|---|---|
| `HealthController.java` | Single `health()` method at `GET /api/health` | Add `ready()` method at `GET /api/ready` | N |
| `SecurityConfig.java` | Permits `/api/health/**`; no rule for `/api/ready/**` | Also permit `/api/ready/**` without authentication | N |
| Response contract (`/api/health`) | `Map<String,String>` with `status`, `service`, `timestamp` | Unchanged | N |
| Response contract (`/api/ready`) | Does not exist | `Map<String,String>` with `status`, `service`, `timestamp`; `200` or `503` | N (new) |
| `HealthControllerTest.java` | Covers `GET /api/health` only | Add test cases for `GET /api/ready` | N |

### Shared contract (both services)

The readiness endpoint must reflect whether the service's critical dependencies (e.g., database connectivity, required configuration) are available. When all dependencies are healthy the response status is `"ok"` and HTTP `200` is returned. When one or more dependencies are unavailable the response status is `"unavailable"` and HTTP `503 Service Unavailable` is returned.

> **Note:** The specific dependencies checked by `/api/ready` are TODO — see Open Questions.

---

## Compatibility & Breaking Changes

| Change | Impact | Migration Path |
|---|---|---|
| New `GET /api/ready` endpoint (both services) | Additive — no existing callers affected | No migration required; callers opt in |
| `SecurityConfig.java` updated to permit `/api/ready/**` | Existing security rules for `/api/payments/**` and the default `denyAll()` are unchanged | No migration required |
| `/api/health` response shape unchanged | No impact on existing load-balancer or Kubernetes liveness probe configurations | No migration required |
| HTTP `503` returned by `/api/ready` when unready | New behaviour on a new endpoint | Kubernetes readiness probe must be configured to treat `503` as "not ready" (standard behaviour) |

---

## Acceptance Criteria

1. **Given** the `user-management` service is running, **when** `GET /api/health` is called without an `Authorization` header, **then** the response is `200 OK` with `Content-Type: application/json` and a body containing `"status": "ok"`, `"service": "user-management"`, and a non-empty `timestamp` field that is a valid ISO-8601 string.

2. **Given** the `payment-service` is running, **when** `GET /api/health` is called without an `Authorization` header, **then** the response is `200 OK` with `Content-Type: application/json` and a body containing `"status": "ok"`, `"service": "payment-service"`, and a non-empty `timestamp` field.

3. **Given** the `user-management` service is running and all required dependencies are available, **when** `GET /api/ready` is called without an `Authorization` header, **then** the response is `200 OK` with `Content-Type: application/json` and a body containing `"status": "ok"`, `"service": "user-management"`, and a non-empty `timestamp` field.

4. **Given** the `payment-service` is running and all required dependencies are available, **when** `GET /api/ready` is called without an `Authorization` header, **then** the response is `200 OK` with `Content-Type: application/json` and a body containing `"status": "ok"`, `"service": "payment-service"`, and a non-empty `timestamp` field.

5. **Given** the `user-management` service is running and a required dependency is unavailable, **when** `GET /api/ready` is called, **then** the response is `503 Service Unavailable` with `Content-Type: application/json` and a body containing `"status": "unavailable"`.

6. **Given** the `payment-service` is running and a required dependency is unavailable, **when** `GET /api/ready` is called, **then** the response is `503 Service Unavailable` with `Content-Type: application/json` and a body containing `"status": "unavailable"`.

7. **Given** the `payment-service` `SecurityConfig` is active, **when** `GET /api/ready` is called without an `Authorization` header, **then** the response is not `401 Unauthorized` and not `403 Forbidden` (i.e., the endpoint is publicly accessible).

8. **Given** the `payment-service` `SecurityConfig` is active, **when** any request is made to a path other than `/api/health/**`, `/api/ready/**`, or `/api/payments/**`, **then** the response is `403 Forbidden` (the existing `denyAll()` default is preserved).

9. **Given** the CI pipeline runs, **when** the `user-management` test suite executes (`npm test`), **then** all existing `health.test.js` tests pass and new tests covering `GET /api/ready` (status `200`, `"status": "ok"`, valid timestamp, correct `Content-Type`) also pass with no reduction in coverage for the health adapter.

10. **Given** the CI pipeline runs, **when** the `payment-service` test suite executes (`./mvnw test`), **then** all existing `HealthControllerTest` tests pass and new tests covering `GET /api/ready` (status `200`, `"status": "ok"`, timestamp present) also pass.

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | What specific dependencies should the `/api/ready` endpoint check for each service? (e.g., database reachability, Redis connectivity, external gateway availability) | TODO | TODO |
| 2 | Should `/api/ready` perform active dependency probes on every call, or rely on a cached/background health state to avoid adding latency to the probe path? | TODO | TODO |
| 3 | Should the readiness response body enumerate individual dependency statuses (e.g., `{ "db": "ok", "redis": "degraded" }`) or only a top-level `status` field? | TODO | TODO |
| 4 | Is a `GET /api/ready` path sufficient, or is a separate startup probe endpoint also required for Kubernetes `startupProbe` configuration? | TODO | TODO |
| 5 | Should the `user-management` service's `/api/ready` endpoint be protected by the same rate-limiting middleware (`rateLimiter.js`) applied to other routes, or exempted? | TODO | TODO |
| 6 | Are there any SLA or response-time requirements for the probe endpoints (e.g., must respond within 200 ms) that should be enforced in CI? | TODO | TODO |