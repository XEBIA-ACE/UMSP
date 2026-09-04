# Tasks: Add /health and /ready Endpoints

## Prerequisites

- [ ] [XS] Confirm Node.js 20 LTS is installed and `npm` is available for `user-management` service
- [ ] [XS] Confirm Java 17+ JDK and Maven wrapper (`./mvnw`) are available for `payment-service`
- [ ] [XS] Verify local test suites pass on `main` before branching — run `npm test` in `user-management/` and `./mvnw test` in `payment-service/`

---

## Phase 1 — Preparation

- [ ] [XS] Create feature branch `feat/health-ready-endpoints` from `main`
- [ ] [XS] Record baseline test results for `user-management` by running `npm test -- --coverage` and saving the summary output
- [ ] [XS] Record baseline test results for `payment-service` by running `./mvnw test` and saving the Surefire summary

---

## Phase 2 — Core Upgrade

### user-management (Node.js / Express)

- [ ] [S] Add `GET /api/ready` route to `user-management/src/adapters/inbound/http/routes/healthRoutes.js` — mount a new `router.get('/ready', controller.ready.bind(controller))` entry alongside the existing `/` liveness route
- [ ] [S] Implement `ready()` method on `user-management/src/adapters/inbound/http/controllers/HealthController.js` — return `200` with `{ status: "ready", service: "user-management", timestamp: <ISO> }` when the service is ready; return `503` with `{ status: "unavailable" }` if a dependency check fails
- [ ] [XS] Verify `user-management/src/infrastructure/app.js` (the `createApp` factory) mounts `healthRoutes` at `/api/health` so that both `/api/health` and `/api/health/ready` (or `/api/ready`) are reachable — adjust mount path if `/api/ready` is the intended separate path per README table

### payment-service (Java / Spring Boot)

- [ ] [S] Add `GET /api/ready` handler to `payment-service/src/main/java/com/payments/adapters/inbound/rest/HealthController.java` — annotate with `@GetMapping("/ready")`, return `200` with `{ status: "ready", service: "payment-service", timestamp: <ISO> }` on success and `503` on failure
- [ ] [XS] Extend the `requestMatchers` permit-all rule in `payment-service/src/main/java/com/payments/infrastructure/config/SecurityConfig.java` to cover `/api/health/ready` (or the chosen ready path) — ensure the pattern `/api/health/**` already covers it, or add an explicit matcher if the ready endpoint is at a different path

---

## Phase 3 — Testing & Validation

### user-management

- [ ] [S] Add test cases for `GET /api/ready` to `user-management/src/__tests__/health.test.js` — assert `200` with `{ status: "ready", service: "user-management" }`, valid ISO timestamp, and `Content-Type: application/json`
- [ ] [XS] Run `npm test -- --coverage` in `user-management/` and confirm all existing tests still pass and new ready-endpoint tests are green

### payment-service

- [ ] [S] Add test cases for `GET /api/health/ready` to `payment-service/src/test/java/com/payments/adapters/inbound/rest/HealthControllerTest.java` — assert HTTP `200`, JSON fields `status: "ready"`, `service: "payment-service"`, and non-empty `timestamp` using `MockMvc`
- [ ] [XS] Run `./mvnw test` in `payment-service/` and confirm all existing tests still pass and new ready-endpoint tests are green

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [XS] Update Kubernetes liveness probe path (if defined in any manifest under `.github/` or `docker-compose.yml`) to confirm it targets `GET /api/health` — no change expected if already correct
- [ ] [XS] Add or update Kubernetes readiness probe path in any deployment manifests to target `GET /api/health/ready` (payment-service, port 8080) and `GET /api/ready` or `GET /api/health/ready` (user-management, port 3000) — document the chosen path clearly

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Update the **Key endpoints** table in `README.md` for `user-management` to add a row for the `/api/ready` (or `/api/health/ready`) readiness probe endpoint
- [ ] [XS] Update the **Key endpoints** table in `README.md` for `payment-service` to add a row for `GET /api/health/ready` readiness probe endpoint
- [ ] [XS] Append an entry to `AGENTS.md` stack table or endpoint reference noting the new `/ready` endpoints and their auth posture (public, no JWT required)