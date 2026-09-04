# CONSTITUTION — User Management and Payment Service Documentation Modernization

## Project Identity

**Name:** User Management and Payment Service — Documentation Modernization
**Purpose:** Update all project documentation to accurately reflect the current modernized stack as implemented in the codebase.
**Goal:** Eliminate discrepancies between the existing `README.md` and `AGENTS.md` and the actual running stack, ensuring every developer-facing document is a reliable source of truth.

---

## Guiding Principles

1. **Prefer accuracy over completeness** because the README currently documents `Java 17 · Spring Boot 3.2` for the payment service while the codebase uses `Java 21 LTS · Spring Boot 3.x`, creating onboarding risk.
2. **Prefer a single authoritative stack table over scattered inline references** because version mismatches exist across `README.md` and `AGENTS.md`, and duplication is the root cause.
3. **Prefer documenting what is implemented over what is aspirational** because several adapters (PayPal, email notification) are stubs with TODO markers; documentation must clearly distinguish production-ready components from placeholders.
4. **Prefer explicit environment variable documentation over implicit defaults** because payment and user services each carry required secrets (`STRIPE_API_KEY`, `JWT_SECRET`, etc.) with no fallback, and missing documentation causes broken deployments.
5. **Prefer preserving architecture documentation** because the Hexagonal Architecture diagram and port/adapter descriptions in the README are accurate and must not be removed or altered during the update.

---

## Constraints

- **Effort ceiling:** Moderate option — documentation-only changes; no source code modifications are in scope.
- **Scope freeze:** Changes are limited to `README.md`, `AGENTS.md`, and any directly referenced documentation files. No refactoring of source code, tests, or CI configuration is permitted under this task.
- **Technology mandates (must be reflected accurately in docs):**
  - Node.js **20 LTS** + Express **4.x** (gateway/BFF layer, port 3000)
  - Java **21 LTS** + Spring Boot **3.x** (user-service and payment-service, port 8080)
  - PostgreSQL **15**, Redis **7**
  - Flyway (migrations), Testcontainers (Java integration tests)
  - GitHub Actions (CI/CD)
- **Do not document** `InMemoryPaymentRepository` or `InMemoryUserRepository` as production persistence — they are explicitly dev/test adapters.
- **Timeline:** TODO — person-days estimate not provided in the upgrade option.

---

## Quality Standards

- **Accuracy gate:** Every version number in documentation must match a version declared in `package.json` or `pom.xml` (or `AGENTS.md` stack table). Zero tolerance for version drift at merge time.
- **Completeness check:** All environment variables present in `.env.example` files must appear in the README environment variable tables. Reviewer must verify parity before approving.
- **Stub disclosure:** Any component documented as a feature (e.g. PayPal integration, email notifications) must include a visible callout noting stub/placeholder status if the implementation contains a TODO.
- **Code review:** Minimum one peer review required; reviewer must confirm documentation against actual source files, not prior documentation.
- **No broken commands:** Every `bash` code block in the README must be manually verified to execute without error in a clean checkout before merge.
- **Architecture diagram:** The ASCII Hexagonal Architecture diagram must be retained verbatim unless the architecture itself has changed (it has not).

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | Correct payment-service runtime from `Java 17` to `Java 21 LTS` in README service table | `AGENTS.md` and source code (`pom.xml` context) reference Java 21; README is stale | Accepted |
| ADR-002 | Document `InMemoryPaymentRepository` and `InMemoryUserRepository` as dev/test-only adapters, not production persistence | Source code Javadoc explicitly states "suitable for development, testing, and demo purposes — replace for production" | Accepted |
| ADR-003 | Add stub/placeholder callouts for PayPal gateway and email notification adapters | Both adapters contain explicit `TODO` markers and return mock results; documenting them as complete features would mislead integrators | Accepted |
| ADR-004 | Retain the Node.js Express layer as "API Gateway / BFF" (not a standalone service) | `AGENTS.md` and source structure (`gateway/`) confirm it proxies to Spring services; README currently mislabels it as `user-management` service | Accepted |
| ADR-005 | Database and cache versions (PostgreSQL 15, Redis 7) to be added to README if absent | Present in `AGENTS.md` stack table but not surfaced in README quick-start or architecture sections | Proposed |