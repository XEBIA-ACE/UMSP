# TASKS — Update Project Documentation to Reflect Modernized Stack

## Prerequisites

- [ ] [XS] Confirm write access to the repository and the default branch in GitHub repository settings
- [ ] [XS] Verify local checkout is up to date (`git pull`) and no uncommitted changes exist in `README.md` or `AGENTS.md`
- [ ] [XS] Confirm the actual runtime versions in use by inspecting `user-management/package.json` (Node.js 20, Express 4.18.2, Jest 29.7.0) and `payment-service/pom.xml` (Java 21, Spring Boot 3.x) before editing any documentation

---

## Phase 1 — Preparation

- [ ] [XS] Create a dedicated branch `docs/modernize-stack-readme` from `main` for all documentation changes
- [ ] [XS] Audit the version discrepancy in `README.md` service table — the table lists `Java 17 · Spring Boot 3.2` for `payment-service` but `AGENTS.md` lists `Java 21 (LTS)` and `Spring Boot 3.x`; confirm the correct versions from `payment-service/pom.xml` before editing
- [ ] [XS] Cross-reference `user-management/package.json` dependency versions (`express ^4.18.2`, `jsonwebtoken ^9.0.2`, `bcryptjs ^2.4.3`, `uuid ^9.0.0`, `nodemailer ^6.9.7`) against what is documented in `README.md` and `AGENTS.md` to identify all gaps

---

## Phase 2 — Core Upgrade

- [ ] [S] Correct the `payment-service` stack entry in the `README.md` service summary table — change `Java 17 · Spring Boot 3.2` to match the confirmed version from `pom.xml` (expected: `Java 21 · Spring Boot 3.x`) in `README.md`
- [ ] [S] Update the `README.md` **Payment Service** quick-start section to reflect the actual Maven wrapper command (`./mvnw spring-boot:run`) and confirm the Docker port mapping (`8080:8080`) matches `payment-service/src/main/java/com/payments/adapters/inbound/rest/HealthController.java` and `PaymentController.java`
- [ ] [S] Update the `README.md` **Environment Variables** table for the Payment Service to add the `STRIPE_API_KEY` property key name used in `StripeGatewayAdapter.java` (`stripe.api.key` → env var `STRIPE_API_KEY`), `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` / `PAYPAL_MODE` as used in `PayPalGatewayAdapter.java`, and `NOTIFICATION_EMAIL_ENABLED` as used in `EmailNotificationAdapter.java` (`notification.email.enabled`)
- [ ] [S] Update the `README.md` **Key endpoints** table for the Payment Service to ensure the refund endpoint `POST /api/payments/{id}/refund` is listed and matches the route defined in `PaymentController.java`
- [ ] [S] Update `AGENTS.md` **Section 1 — Stack** table to reconcile `Java 21 (LTS)` and `Spring Boot 3.x` with the confirmed `pom.xml` values, and add explicit version numbers for `Express 4.18.2`, `Jest 29.7.0`, `Supertest 6.3.3`, and `PostgreSQL 15` / `Redis 7` where currently listed without patch versions
- [ ] [M] Update `AGENTS.md` **Section 2 — Project Structure** to complete the truncated directory tree — add the missing `payment-service` subtree entries for `adapters/outbound/stripe/StripeGatewayAdapter.java`, `adapters/outbound/paypal/PayPalGatewayAdapter.java`, `adapters/outbound/notification/EmailNotificationAdapter.java`, `adapters/outbound/persistence/InMemoryPaymentRepository.java`, `adapters/outbound/persistence/PaymentEntity.java`, `application/service/PaymentApplicationService.java`, `application/dto/ProcessPaymentRequest.java`, and `domain/model/Payment.java` in `AGENTS.md`
- [ ] [S] Add an **Architecture Notes** subsection to `README.md` documenting that `InMemoryPaymentRepository` (`payment-service/.../persistence/InMemoryPaymentRepository.java`) and `InMemoryUserRepository` (`user-management/src/adapters/outbound/persistence/InMemoryUserRepository.js`) are development/test adapters and must be replaced with database-backed adapters before production deployment
- [ ] [S] Add a **Stub Adapters** notice to `README.md` documenting that `PayPalGatewayAdapter.java` and `EmailNotificationAdapter.java` contain TODO stub implementations and are not production-ready, referencing the TODO comments in those files

---

## Phase 3 — Testing & Validation

- [ ] [XS] Manually verify all internal cross-references in `README.md` (directory paths, env var names, endpoint paths) against the actual source files (`PaymentController.java`, `StripeGatewayAdapter.java`, `PayPalGatewayAdapter.java`, `EmailNotificationAdapter.java`, `user-management/package.json`) to confirm no broken references were introduced
- [ ] [XS] Verify the `README.md` Docker Compose example snippet references the correct service names (`user-management`, `payment-service`) and ports (`3000`, `8080`) consistent with `docker-compose.yml`

---

## Phase 4 — CI/CD & Infrastructure

N/A — not applicable to this task

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Add a `## Changelog` entry to `README.md` (or a top-level `CHANGELOG.md` if one exists) recording the documentation corrections: Java version fix, stub adapter notices, env var table corrections, and project structure completion
- [ ] [XS] Open a pull request from `docs/modernize-stack-readme` to `main` with a description summarising each documentation correction and linking to the relevant source files as evidence for each change
- [ ] [XS] Request review from at least one team member familiar with both the Node.js gateway and the Spring Boot payment service to validate accuracy of the updated `AGENTS.md` stack table and `README.md` environment variable tables before merging