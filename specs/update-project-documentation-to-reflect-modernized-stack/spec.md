# Spec: Update Project Documentation to Reflect Modernized Stack

## Summary

This spec covers the updates required to bring the project's documentation (`README.md` and `AGENTS.md`) into alignment with the actual modernized stack as reflected in the source code and configuration files. The primary discrepancy is that `README.md` describes the payment service as running on **Java 17 · Spring Boot 3.2**, while `AGENTS.md` and the source code confirm the runtime is **Java 21 LTS** with **Spring Boot 3.x**. Additional documentation gaps exist around the monorepo's true structure (an API gateway layer is present in code but absent from the README), the in-memory persistence adapters used in development/test, and stub gateway implementations. The expected outcome is a single, consistent, accurate set of documentation that correctly describes all services, their runtimes, ports, environment variables, and architectural boundaries.

---

## Motivation

- **Version inconsistency (medium urgency):** `README.md` states the payment service uses `Java 17 · Spring Boot 3.2`. `AGENTS.md` and the actual project structure specify `Java 21 (LTS)` and `Spring Boot 3.x`. This mismatch creates confusion for onboarding engineers and CI/CD configuration.
- **Missing service documentation:** The `gateway/` directory (Node.js 20 / Express 4 API Gateway / BFF layer) is fully implemented in source but is not documented in `README.md` as a distinct service. The README describes only `user-management` and `payment-service`.
- **Structural mismatch:** `README.md` references a `user-management/` directory and a `payment-service/` directory at the root. `AGENTS.md` and the source code show the monorepo root contains `gateway/`, `user-service/`, and `payment-service/` directories. The `user-management/` path used in README quick-start commands does not match the `user-service/` path in `AGENTS.md`.
- **Undocumented development adapters:** `InMemoryPaymentRepository` and `InMemoryUserRepository` are the active persistence adapters but are not mentioned in the README, leading developers to assume a live database is always required.
- **Undocumented stub gateways:** `PayPalGatewayAdapter` and `StripeGatewayAdapter` contain stub/TODO implementations. The README does not communicate this to developers setting up locally.
- **Tech debt:** Failure to keep documentation synchronized with the codebase increases onboarding time and risks incorrect infrastructure provisioning.

---

## Current State

### README.md

| Element | Current (Incorrect) Value |
|---|---|
| Payment service runtime | `Java 17 · Spring Boot 3.2` |
| Payment service port | `8080` |
| User management runtime | `Node.js 20 · Express 4` |
| User management port | `3000` |
| Services listed | `user-management`, `payment-service` |
| Directory references | `user-management/`, `payment-service/` |
| Gateway/BFF layer | Not mentioned |
| In-memory adapters | Not mentioned |
| Stub gateway implementations | Not mentioned |
| `AGENTS.md` reference | Not present |

### AGENTS.md

| Element | Current Value |
|---|---|
| Node.js runtime | `Node.js 20 LTS` |
| Java runtime | `Java 21 (LTS)` |
| Spring Boot version | `Spring Boot 3.x` |
| Gateway directory | `gateway/` |
| User service directory | `user-service/` |
| Payment service directory | `payment-service/` |
| Key config files documented | Yes (full project structure tree) |

### Key source-code elements relevant to documentation accuracy

- `gateway/src/app.js`, `gateway/src/server.js` — Express API Gateway entry points (undocumented in README)
- `gateway/src/config/index.js`, `gateway/src/config/oauth2.js` — centralised config (env vars not listed in README)
- `user-management/package.json` — confirms `express ^4.18.2`, `jest ^29.7.0`, `supertest ^6.3.3`, `nodemon ^3.0.2`
- `InMemoryPaymentRepository.java` — active dev/test persistence adapter; no JPA annotations
- `InMemoryUserRepository.js` — active dev/test persistence adapter
- `PayPalGatewayAdapter.java` — stub implementation; reads `paypal.client.id`, `paypal.client.secret`, `paypal.mode`
- `StripeGatewayAdapter.java` — live Stripe SDK integration; reads `stripe.api.key`
- `EmailNotificationAdapter.java` — reads `notification.email.enabled` (default `false`)
- `ProcessPaymentRequest.java` — record with `userId`, `amount`, `currency`, `method`, `description`
- `PaymentController.java` — endpoints: `POST /api/payments`, `GET /api/payments/{id}`, `POST /api/payments/{id}/refund`
- `HealthController.java` — endpoint: `GET /api/health`

---

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| README — payment service runtime | `Java 17 · Spring Boot 3.2` | `Java 21 (LTS) · Spring Boot 3.x` | N |
| README — services table | Lists `user-management` (Node.js 20 · Express 4, port 3000) and `payment-service` (Java 17 · Spring Boot 3.2, port 8080) | Lists `gateway` (Node.js 20 · Express 4, port 3000), `user-service` (Java 21 · Spring Boot 3.x, port TODO), `payment-service` (Java 21 · Spring Boot 3.x, port 8080) | N |
| README — directory references in quick-start | `cd user-management` | `cd gateway` or `cd user-service` (whichever is correct per final structure) | N |
| README — gateway service section | Absent | New section documenting the Express API Gateway/BFF: responsibilities, key routes, quick-start, Docker instructions, and environment variables | N |
| README — environment variables (gateway) | Absent | Add table covering gateway-specific env vars (OAuth2 config, upstream service URLs, rate-limit settings) sourced from `gateway/src/config/index.js` and `gateway/src/config/oauth2.js` | N |
| README — development adapter notice | Absent | Add note that `InMemoryPaymentRepository` and `InMemoryUserRepository` are active in development/test; a database-backed adapter is required for production | N |
| README — stub gateway notice | Absent | Add note that `PayPalGatewayAdapter` is a stub returning mock results; `StripeGatewayAdapter` uses the live Stripe SDK | N |
| README — `AGENTS.md` reference | Absent | Add reference directing contributors to `AGENTS.md` for the authoritative stack and project-structure overview | N |
| AGENTS.md — stack table | Accurate per source code | No changes required; serves as the source of truth | N |

---

## Compatibility & Breaking Changes

Documentation-only changes carry no runtime compatibility impact. No API contracts, data models, or configuration keys are being altered.

| Change | Impact on Callers | Migration Path |
|---|---|---|
| Correcting Java version from 17 to 21 in README | Developers who provisioned Java 17 environments based on the README may need to upgrade their local JDK | Install Java 21 LTS; update any local `.java-version` or `JAVA_HOME` references accordingly |
| Directory path corrections (`user-management/` → correct path) | Developers following old README quick-start commands will need to use updated paths | Use the corrected directory names as documented in the updated README |
| Gateway service added to README | None — additive only | N/A |
| In-memory adapter and stub gateway notices | None — informational only | N/A |

---

## Acceptance Criteria

1. **Given** the updated `README.md`, **when** a reviewer reads the services summary table, **then** the payment service runtime is listed as `Java 21 (LTS)` and `Spring Boot 3.x` — not `Java 17` or `Spring Boot 3.2`.

2. **Given** the updated `README.md`, **when** a reviewer reads the services summary table, **then** the API Gateway/BFF service (Node.js 20 · Express 4, port 3000) is listed as a distinct entry alongside `user-service` and `payment-service`.

3. **Given** the updated `README.md`, **when** a reviewer reads the quick-start instructions for each service, **then** every `cd <directory>` command references a directory that exists in the repository root as confirmed by `AGENTS.md` and the source tree.

4. **Given** the updated `README.md`, **when** a reviewer reads the environment variables section for the gateway service, **then** at least the variables sourced from `gateway/src/config/index.js` and `gateway/src/config/oauth2.js` are listed with their names, defaults, and descriptions.

5. **Given** the updated `README.md`, **when** a reviewer reads the payment service section, **then** a clearly labelled notice states that `InMemoryPaymentRepository` is the active persistence adapter for development and testing, and that a production deployment requires a database-backed adapter.

6. **Given** the updated `README.md`, **when** a reviewer reads the payment service section, **then** a clearly labelled notice states that the PayPal gateway adapter is a stub returning mock results, and that the Stripe adapter uses the live Stripe SDK.

7. **Given** the updated `README.md`, **when** a reviewer reads the top-level introduction or contributing section, **then** a reference to `AGENTS.md` is present and identifies it as the authoritative source for stack versions and project structure.

8. **Given** both `README.md` and `AGENTS.md`, **when** a reviewer compares the Java runtime version stated in each document, **then** both documents agree on `Java 21 (LTS)`.

9. **Given** the updated `README.md`, **when** a reviewer reads the Docker Compose example, **then** the service names and build context paths match the directory names confirmed in `AGENTS.md`.

10. **Given** the CI pipeline (GitHub Actions), **when** a pull request modifying `README.md` or `AGENTS.md` is opened, **then** a markdown lint check passes with no errors (verifiable via the existing `ci.yml` workflow or a dedicated lint step).

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | What is the correct internal port for `user-service` (Spring Boot)? The README lists port 8080 for the payment service but does not document a port for the user service. | TODO | TODO |
| 2 | What is the canonical root directory name for the user-facing Node.js service — `user-management/` (as in README) or `user-service/` (as in AGENTS.md)? The discrepancy must be resolved before documentation is updated. | TODO | TODO |
| 3 | What environment variables does `gateway/src/config/index.js` and `gateway/src/config/oauth2.js` expose? These files are referenced in AGENTS.md but their contents are not provided in the source context. | TODO | TODO |
| 4 | Are there additional gateway-specific environment variables (e.g. upstream service URLs, rate-limit thresholds, correlation ID header name) that must be added to the README env-vars table? | TODO | TODO |
| 5 | Should the Docker Compose example in the README be updated to include the gateway service, and if so, what is the correct `build` context and port mapping? | TODO | TODO |
| 6 | Is `Spring Boot 3.x` the intended version specifier in documentation, or should a specific patch version (e.g. `3.2.x`, `3.3.x`) be stated? | TODO | TODO |