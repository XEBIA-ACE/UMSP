# CONSTITUTION — Health & Readiness Endpoints

## Project Identity

**Name:** Health & Readiness Endpoint Addition — `user-payment-service` monorepo

**Purpose:** Add `/health` (liveness) and `/ready` (readiness) HTTP endpoints to both the `user-management` (Node.js/Express) and `payment-service` (Java/Spring Boot) microservices so that orchestration platforms (e.g. Kubernetes) and load balancers can probe service availability without credentials.

**High-level goal:** Both services expose consistent, unauthenticated `GET /api/health` and `GET /api/ready` endpoints that return structured JSON and appropriate HTTP status codes. The liveness endpoint (`/health`) is already partially implemented; the readiness endpoint (`/ready`) is net-new for both services.

---

## Guiding Principles

1. **Prefer `/api/health` for liveness and `/api/ready` for readiness over a single combined endpoint** because Kubernetes distinguishes liveness probes (is the process alive?) from readiness probes (is the service ready to accept traffic?), and conflating them causes incorrect restart/traffic-routing behaviour.

2. **Prefer unauthenticated access to both endpoints over JWT-gated access** because load balancers and orchestrators probe without credentials; the existing `SecurityConfig.java` already permits `/api/health/**` and this pattern must be extended to `/api/ready/**`.

3. **Prefer a consistent JSON response shape across both services over service-specific formats** because monitoring tooling consumes both endpoints and divergent schemas increase integration cost. Minimum required fields: `status`, `service`, `timestamp`.

4. **Prefer keeping health/ready controllers free of business logic over embedding dependency checks in the domain layer** because these endpoints must remain fast and side-effect-free; they are infrastructure concerns, not domain concerns.

5. **Prefer extending existing test patterns (MockMvc for Java, Supertest for Node.js) over introducing new test frameworks** because both test stacks are already established and adding frameworks increases maintenance overhead within the effort ceiling.

---

## Constraints

- **Effort ceiling:** Moderate option — scope is limited to adding the two endpoints and their tests. No refactoring of unrelated code is permitted within this task.
- **Technology mandates:**
  - `user-management`: Node.js 20 LTS, Express 4.x — no runtime upgrades.
  - `payment-service`: Java 17 (source confirms Java 17; AGENTS.md references Java 21 — **TODO: confirm target JDK version before implementation**), Spring Boot 3.2 — no framework upgrades.
- **Security mandate:** Both endpoints must be publicly accessible without authentication. `SecurityConfig.java` must be updated to permit `/api/ready/**` alongside the existing `/api/health/**` rule.
- **Scope freeze:** No changes to domain, application, or persistence layers. No new external dependencies may be introduced for this task.
- **Response contract:** `GET /api/ready` must return `200 OK` when ready and `503 Service Unavailable` when not ready. `GET /api/health` must return `200 OK` at all times the process is alive.

---

## Quality Standards

- **Test coverage:** Every new endpoint must have at minimum one integration test asserting: correct HTTP status code, `Content-Type: application/json`, and presence of `status` and `timestamp` fields in the response body.
- **Security regression test:** At least one test per service must confirm the endpoint is reachable without an authentication token (mirrors the existing `HealthControllerTest` pattern).
- **Code review:** All changes require review against this constitution before merge — specifically verifying the security permit rules and response shape consistency.
- **No broken existing tests:** The CI pipeline (`ci.yml`) must pass with zero regressions. `./mvnw test` and `npm test -- --coverage` must both exit 0.
- **Documentation:** `README.md` endpoint tables for both services must be updated to include the `/api/ready` row before the task is considered complete.

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | Mount health endpoints at `/api/health` (not `/health` or `/actuator/health`) | Existing `HealthController.java` and `healthRoutes.js` already use `/api/health`; consistency requires the same base path for `/api/ready` | Accepted |
| ADR-002 | Permit `/api/health/**` and `/api/ready/**` without authentication in `SecurityConfig.java` | Orchestrators probe without credentials; existing security config already establishes this pattern for `/api/health/**` | Accepted |
| ADR-003 | Readiness endpoint returns `503` when not ready, `200` when ready | Standard Kubernetes readiness probe convention; allows the platform to remove the pod from load-balancer rotation without restarting it | Accepted |
| ADR-004 | Do not introduce Spring Boot Actuator for this task | Scope is constrained to a minimal addition; Actuator would expand the attack surface and dependency footprint beyond what the upgrade option authorises | Accepted |
| ADR-005 | Target JDK version for `payment-service` | README states Java 17; AGENTS.md states Java 21 — **TODO: resolve before implementation** | Proposed |