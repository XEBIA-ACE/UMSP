# Tasks: Add /health and /ready Endpoints

## Prerequisites

- [ ] [XS] Confirm Node.js 20 LTS is installed and `npm` is available for `user-management` service
- [ ] [XS] Confirm Java 17+ JDK and Maven wrapper (`./mvnw`) are available for `payment-service`
- [ ] [XS] Verify local test suites pass on `main` before branching: run `npm test` in `user-management/` and `./mvnw test` in `payment-service/`

---

## Phase 1 — Preparation

- [ ] [XS] Create feature branch `feat/health-ready-endpoints` from `main`
- [ ] [XS] Record baseline test results for `user-management` by running `npm test -- --coverage` and saving the summary output
- [ ] [XS] Record baseline test results for `payment-service` by running `./mvnw test` and saving the Surefire summary output

---

## Phase 2 — Core Upgrade

### user-management (Node.js / Express)

- [ ] [S] Add `GET /api/ready` route to `user-management/src/adapters/inbound/http/routes/healthRoutes.js` that returns `{ status: "ready", service: "user-management", timestamp: <ISO> }` with HTTP 200, following the same pattern as the existing `GET /` (liveness) route
- [ ] [S] Add a `ready()` method to `user-management/src/adapters/inbound/http/controllers/HealthController.js` that returns the readiness payload, mirroring the existing `check()` method structure
- [ ] [XS] Verify `createHealthRouter()` in `user-management/src/adapters/inbound/http/routes/healthRoutes.js` mounts the new `GET /ready` route so it is reachable at `/api/ready` via the app's router

### payment-service (Java / Spring Boot)

- [ ] [S] Add a `GET /api/ready` handler method `ready()` to `payment-service/src/main/java/com/payments/adapters/inbound/rest/HealthController.java` that returns `{ "status": "ready", "service": "payment-service", "timestamp": <ISO> }` with `ResponseEntity<Map<String, String>>` HTTP 200, following the same pattern as the existing `health()` method
- [ ] [XS] Update `payment-service/src/main/java/com/payments/infrastructure/config/SecurityConfig.java` to add `/api/health/ready` (or extend the existing `/api/health/**` matcher) to the `permitAll()` rule in `securityFilterChain()` so the readiness probe is unauthenticated

---

## Phase 3 — Testing & Validation

### user-management

- [ ] [S] Add test case `GET /api/ready returns 200 with status "ready"` to `user-management/src/__tests__/health.test.js`, asserting HTTP 200, `res.body.status === "ready"`, `res.body.service === "user-management"`, a valid ISO timestamp, and `Content-Type: application/json`
- [ ] [XS] Run `npm test -- --coverage` in `user-management/` and confirm all existing tests still pass and the new `/api/ready` test passes

### payment-service

- [ ] [S] Add test method `ready_returnsReady()` to `payment-service/src/test/java/com/payments/adapters/inbound/rest/HealthControllerTest.java` using `MockMvc` to assert `GET /api/health/ready` returns HTTP 200, `$.status == "ready"`, `$.service == "payment-service"`, and `$.timestamp` is not empty, using the existing `TestSecurityConfig` override
- [ ] [XS] Run `./mvnw test` in `payment-service/` and confirm all existing tests still pass and the new `ready_returnsReady()` test passes

---

## Phase 4 — CI/CD & Infrastructure

N/A — not applicable to this task. No pipeline files, Dockerfiles, or IaC configs reference the health endpoints and no changes to those assets are required to expose the new route.

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Update the `payment-service` endpoint table in `README.md` to add a row for `GET /api/health/ready` with auth `None` and description `Readiness probe`
- [ ] [XS] Update the `user-management` endpoint table in `README.md` to add a row for `GET /api/ready` with description `Readiness probe`