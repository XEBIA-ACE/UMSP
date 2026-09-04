# CONSTITUTION — Health & Readiness Endpoints

## Project Identity

**Name:** Health & Readiness Endpoint Addition — `user-payment-service` monorepo

**Purpose:** Add `/health` (liveness) and `/ready` (readiness) HTTP endpoints to both the `user-management` (Node.js/Express) and `payment-service` (Java/Spring Boot) microservices so that orchestration platforms (e.g. Kubernetes) and load balancers can probe service availability without credentials.

**High-level goal:** Both services expose consistent, unauthenticated `GET /api/health` and `GET /api/ready` endpoints that return structured JSON and appropriate HTTP status codes. The `/health` endpoint already exists in both services; this project completes the surface by adding `/ready` and ensuring both endpoints are consistent, tested, and documented.

---

## Guiding Principles

1. **Prefer extending existing `HealthController` files over creating new ones** because both services already contain a working `/api/health` implementation; duplication would create drift.
2. **Prefer unauthenticated access to both endpoints over requiring a JWT** because load balancers and Kubernetes probes cannot carry bearer tokens; `SecurityConfig.java` already permits `/api/health/**` and this pattern must be extended to `/api/ready/**`.
3. **Prefer a distinct `/ready` endpoint over overloading `/health`** because liveness (process is alive) and readiness (process can serve traffic) are separate Kubernetes probe semantics with different failure consequences.
4. **Prefer returning `503 Service Unavailable` from `/ready` when dependencies are not reachable** over always returning `200`, because a `200` from an unready service causes the orchestrator to route traffic prematurely.
5. **Prefer no business logic inside health/ready controllers** because these adapters must remain lightweight and must not introduce failure modes that mask real service health.
6. **Prefer consistent JSON response shape across both services** (`status`, `service`, `timestamp`) because cross-service observability tooling depends on a uniform schema.

---

## Constraints

- **Effort ceiling:** Moderate option — scope is limited to adding `/ready` alongside the existing `/health` in both services. No infrastructure changes, no new dependencies beyond what is already present.
- **Technology mandates:**
  - `user-management`: Node.js 20 LTS, Express 4.x — no runtime upgrade permitted.
  - `payment-service`: Java 17 (source code) / Java 21 (AGENTS.md runtime), Spring Boot 3.2 — no framework upgrade permitted.
  - Both services must remain on their current build tools (`npm`/`jest`; `mvn`/`JUnit 5`).
- **Security constraint:** Both endpoints must be explicitly permit-listed in `SecurityConfig.java` (payment-service) and any equivalent auth middleware (user-management) — no credentials required.
- **Scope freeze:** Changes are confined to inbound HTTP adapter layer only. Domain, application, and outbound layers must not be modified.
- **Timeline:** TODO — person-days estimate not provided in upgrade option; treat as a sub-1-day task given existing scaffolding.

---

## Quality Standards

- **Test coverage:** Every new endpoint must have at least one integration test asserting: correct HTTP status code, `Content-Type: application/json`, and all required JSON fields (`status`, `service`, `timestamp`). The `/ready` endpoint must additionally have a test asserting `503` behaviour when a dependency is unavailable (or a documented stub if no real dependency check is in scope).
- **Code review:** All changes require at least one peer review before merge; no self-merge on `main`.
- **Security verification:** CI must confirm that both `/api/health` and `/api/ready` return `200` without an `Authorization` header, and that all other non-health routes still require authentication.
- **Documentation:** `README.md` endpoint tables for both services must be updated to include `GET /api/ready` before the PR is merged.
- **Deployment gate:** CI pipeline (`ci.yml`) must pass all existing and new tests with zero failures before merge.

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | Mount readiness probe at `GET /api/ready` | Keeps liveness (`/health`) and readiness (`/ready`) semantically separate, matching Kubernetes probe conventions | Accepted |
| ADR-002 | Reuse existing `HealthController` files for both endpoints | Both services already have a `HealthController`; adding a `check()` / `ready()` method avoids a new class and keeps the adapter surface minimal | Accepted |
| ADR-003 | Permit `/api/ready/**` without authentication in `SecurityConfig.java` | Consistent with the existing `/api/health/**` permit rule; probes cannot carry credentials | Accepted |
| ADR-004 | Return `{ status, service, timestamp }` JSON shape for both endpoints | Already established by existing `/health` implementations in both services; consistency reduces observability tooling changes | Accepted |
| ADR-005 | Readiness dependency check scope | TODO — whether `/ready` performs a real DB/Redis ping or returns a static `ok` is not specified; must be decided before implementation begins |  Proposed |