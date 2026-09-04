# Spec: Update Project Documentation to Reflect Modernized Stack

## Summary

This spec covers the updates required to bring the project's documentation (`README.md` and `AGENTS.md`) into alignment with the actual modernized stack as implemented in the codebase. The current `README.md` contains at least one confirmed inaccuracy — it lists the payment service runtime as **Java 17 · Spring Boot 3.2**, while `AGENTS.md` and the source code reflect **Java 21 (LTS) · Spring Boot 3.x**. Additionally, the `README.md` describes a two-service layout (`user-management` / `payment-service`) that does not fully match the three-component monorepo structure (`gateway/`, `user-service/`, `payment-service/`) documented in `AGENTS.md`. The expected outcome is a single, consistent, accurate set of documentation that correctly describes the runtime versions, service topology, architecture, and environment variables for all components.

---

## Motivation

- **Version inaccuracy (medium urgency):** `README.md` states `Java 17 · Spring Boot 3.2` for the payment service. `AGENTS.md` and the actual stack table specify **Java 21 LTS** and **Spring Boot 3.x**. Stale version references mislead contributors, cause incorrect JDK toolchain selection during onboarding, and can produce mismatched Docker base images in CI.
- **Structural mismatch:** `README.md` describes two services (`user-management`, `payment-service`) and omits the **Node.js/Express API Gateway** (`gateway/`) that is fully documented in `AGENTS.md` and present in the project structure. This causes confusion about the actual request path and port assignments.
- **Incomplete environment variable documentation:** `README.md` documents env vars for only two services; the gateway/BFF layer (`gateway/`) has its own configuration surface (OAuth2, Redis, rate limiting, upstream service URLs) that is not documented.
- **Tech debt — in-memory adapters undocumented:** Both `InMemoryPaymentRepository` and `InMemoryUserRepository` are production-visible adapters. The documentation does not note that these are development/test stubs and must be replaced before production deployment.
- **Upgrade urgency:** Medium — no EOL or CVE driver, but inaccurate documentation actively impedes onboarding and correct CI/CD configuration.

---

## Current State

### README.md — Affected Elements

| Element | Current Value | Issue |
|---|---|---|
| Payment service stack cell | `Java 17 · Spring Boot 3.2` | Incorrect; should be Java 21 · Spring Boot 3.x per AGENTS.md |
| Service table | Two rows: `user-management` (port 3000), `payment-service` (port 8080) | Missing `gateway` BFF layer; directory names differ from actual layout |
| Quick-start paths | `cd user-management`, `cd payment-service` | Directory names do not match `gateway/`, `user-service/`, `payment-service/` in AGENTS.md |
| Environment variables section | Documents `user-management` and `payment-service` vars only | No env vars documented for `gateway/` (OAuth2, Redis, upstream URLs, rate limiter) |
| Docker Compose snippet | References `./user-management` and `./payment-service` build contexts | Build context paths are incorrect |
| Architecture diagram | Not present in README | AGENTS.md has no diagram either; hexagonal architecture description exists but gateway layer is absent |
| In-memory adapter caveat | Not mentioned | `InMemoryPaymentRepository` and `InMemoryUserRepository` are undocumented as dev-only stubs |

### AGENTS.md — Affected Elements

| Element | Current Value | Issue |
|---|---|---|
| Stack table | Accurate per source code | Authoritative reference; README must be reconciled to this |
| Project structure tree | Shows `gateway/`, `user-service/`, `payment-service/` | README does not reflect this three-component layout |
| `gateway/src/config/oauth2.js` | Listed in structure | Not documented in README env vars section |

### Key Source Artefacts Referenced

- `user-management/package.json` — declares `express ^4.18.2`, `jest ^29.7.0`, `supertest ^6.3.3`, `jsonwebtoken ^9.0.2`, `bcryptjs ^2.4.3`, `uuid ^9.0.0`, `nodemailer ^6.9.7`
- `payment-service/.../StripeGatewayAdapter.java` — uses `stripe-java` SDK; `@Value("${stripe.api.key}")`
- `payment-service/.../PayPalGatewayAdapter.java` — uses `@Value("${paypal.client.id}")`, `${paypal.client.secret}`, `${paypal.mode:sandbox}`
- `payment-service/.../EmailNotificationAdapter.java` — uses `@Value("${notification.email.enabled:false}")`
- `payment-service/.../InMemoryPaymentRepository.java` — `ConcurrentHashMap`-backed stub; Javadoc explicitly states "Replace with database-backed adapter for production"
- `user-management/.../InMemoryUserRepository.js` — `Map`-backed stub; same caveat applies
- `gateway/src/config/oauth2.js` — OAuth2 client configuration (env vars TODO — not visible in provided context)

---

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| `README.md` — service stack table | `Java 17 · Spring Boot 3.2` for payment service | `Java 21 LTS · Spring Boot 3.x` | N |
| `README.md` — service table rows | Two services: `user-management` (3000), `payment-service` (8080) | Three components: `gateway` (3000), `user-service` (TODO port), `payment-service` (8080) | N |
| `README.md` — quick-start directory paths | `cd user-management`, `cd payment-service` | `cd gateway`, `cd user-service`, `cd payment-service` | N |
| `README.md` — Docker Compose build contexts | `./user-management`, `./payment-service` | `./gateway`, `./user-service`, `./payment-service` | N |
| `README.md` — environment variables section | Two services documented | Three components documented; gateway env vars added | N |
| `README.md` — in-memory adapter notice | Not present | Add a clearly labelled "Development / Test Adapters" notice for `InMemoryPaymentRepository` and `InMemoryUserRepository` | N |
| `README.md` — architecture section | Hexagonal diagram present; gateway layer absent | Update diagram/description to include the Node.js gateway as the inbound entry point | N |
| `AGENTS.md` — stack table | Accurate | No changes required; serves as the authoritative source | N |

---

## Compatibility & Breaking Changes

Documentation-only changes carry no runtime breaking changes. The table below addresses documentation consumer impact.

| Change | Impact on Consumers | Migration Path |
|---|---|---|
| Directory names corrected in README quick-start | Developers following old README paths (`cd user-management`) will get a "directory not found" error if they cloned the repo and used the old instructions | README is updated to use correct paths; no code change required |
| Java version corrected to 21 | CI pipelines or local toolchains pinned to Java 17 based on README may fail to build | Developers must update their local JDK and any CI `java-version` matrix entries to 21; this is a pre-existing mismatch, not introduced by this spec |
| Gateway service added to Docker Compose docs | Developers running only two services per old README will not start the gateway | Updated Docker Compose documentation will include all three services |
| Gateway env vars added | None — additive | N/A |
| In-memory adapter warning added | None — informational only | N/A |
| `user-service` port number | TODO — not present in provided context | TODO |
| Gateway OAuth2 / Redis env var names | TODO — `gateway/src/config/index.js` and `oauth2.js` not provided in context | TODO |

---

## Acceptance Criteria

1. **Given** the updated `README.md`, **when** a reviewer reads the service stack table, **then** the payment service row must display `Java 21 LTS` and `Spring Boot 3.x` — not `Java 17` or `Spring Boot 3.2`.

2. **Given** the updated `README.md`, **when** a reviewer counts the rows in the services table, **then** there must be exactly three rows corresponding to `gateway`, `user-service`, and `payment-service`, each with its correct port number.

3. **Given** the updated `README.md` quick-start instructions, **when** a developer executes the documented `cd` command for each service on a freshly cloned repository, **then** each command must resolve to an existing directory without error.

4. **Given** the updated `README.md` Docker Compose example, **when** a reviewer compares the `build:` context paths against the actual repository directory structure, **then** all three build contexts must match existing top-level directories.

5. **Given** the updated `README.md` environment variables section, **when** a reviewer cross-references each documented variable against the source files (`StripeGatewayAdapter.java`, `PayPalGatewayAdapter.java`, `EmailNotificationAdapter.java`, `user-management/package.json`, and gateway config), **then** every `@Value`-injected property key and every `process.env` reference present in source must have a corresponding row in the documentation.

6. **Given** the updated `README.md`, **when** a reviewer searches for references to `InMemoryPaymentRepository` or `InMemoryUserRepository`, **then** the document must contain a clearly labelled notice stating these adapters are for development and testing only and must be replaced with a persistent-store adapter before production deployment.

7. **Given** the updated `README.md` and `AGENTS.md`, **when** a reviewer compares the Java runtime version stated in both documents, **then** both must agree on `Java 21 LTS`.

8. **Given** the updated `README.md` architecture section, **when** a reviewer reads the service topology description, **then** the Node.js/Express API Gateway must be identified as the inbound entry point that proxies to `user-service` and `payment-service`.

9. **Given** a CI lint or link-check job (e.g. `markdownlint`), **when** the updated documentation files are committed, **then** the job must pass with zero errors on both `README.md` and `AGENTS.md`.

10. **Given** the updated `README.md` Docker Compose snippet, **when** a developer runs `docker compose up` using the documented configuration on a machine with Docker installed, **then** all three services must start and their respective health endpoints (`GET /api/health`) must return `200 OK`.

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | What is the correct HTTP port for `user-service` (Spring Boot user management)? The README currently only documents port 8080 for `payment-service`; `user-service` port is not visible in the provided context. | TODO | TODO |
| 2 | What are the environment variable names used by `gateway/src/config/index.js` and `gateway/src/config/oauth2.js`? These files are listed in `AGENTS.md` but their contents were not provided, so gateway env vars cannot be fully documented. | TODO | TODO |
| 3 | Should `AGENTS.md` be updated to add any missing detail (e.g. gateway env vars, in-memory adapter warnings), or is it intentionally a high-level agent reference only? | TODO | TODO |
| 4 | Is the `user-management/` directory name used in the current README intentional (i.e., does a symlink or alias exist), or is it a straightforward error that should be corrected to `gateway/` and `user-service/`? | TODO | TODO |
| 5 | Should the documentation distinguish between `Spring Boot 3.x` (as in AGENTS.md) and a specific patch version (e.g. `3.2.x`, `3.3.x`)? The `pom.xml` was not provided in context. | TODO | TODO |
| 6 | Are there additional CI workflow steps (e.g. in `.github/workflows/ci.yml`) that reference the old directory names or Java 17 that also need updating as part of this documentation pass, or is that out of scope? | TODO | TODO |