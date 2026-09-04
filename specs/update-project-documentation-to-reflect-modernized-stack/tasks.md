# TASKS — Update Project Documentation to Reflect Modernized Stack

## Prerequisites

- [ ] [XS] Confirm write access to the repository and ability to open PRs against the default branch
- [ ] [XS] Verify local checkout is up to date with `main` (or equivalent default branch) before beginning edits
- [ ] [XS] Confirm Node.js 20 LTS and Java 21 LTS are the authoritative runtime versions by cross-checking `gateway/package.json` engine field (if present) and `payment-service/pom.xml` `<java.version>` property against AGENTS.md stack table

---

## Phase 1 — Preparation

- [ ] [XS] Create a dedicated documentation branch (e.g. `docs/modernize-stack`) from `main` to isolate all documentation changes
- [ ] [XS] Audit the discrepancy between `README.md` payment-service stack entry (`Java 17 · Spring Boot 3.2`) and `AGENTS.md` stack table (`Java 21 LTS · Spring Boot 3.x`) to establish the single source of truth before editing either file

---

## Phase 2 — Core Upgrade

- [ ] [S] Correct the payment-service stack entry in the services table in `README.md` from `Java 17 · Spring Boot 3.2` to `Java 21 (LTS) · Spring Boot 3.x` to match the authoritative stack declared in `AGENTS.md`
- [ ] [S] Add the missing gateway/BFF layer row to the `README.md` services table — the current table lists `user-management` (Node.js 20 · Express 4 · port 3000) and `payment-service` but omits the Express API Gateway described in `AGENTS.md`; reconcile the service names and ports against the `AGENTS.md` project structure
- [ ] [S] Update the `README.md` environment variables section for the payment-service to add the missing variables present in `AGENTS.md` but absent from the table: `STRIPE_API_KEY` (maps to `stripe.api.key` used in `StripeGatewayAdapter.java`), `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` / `PAYPAL_MODE` (maps to `paypal.client.id`, `paypal.client.secret`, `paypal.mode` in `PayPalGatewayAdapter.java`), and `notification.email.enabled` (used in `EmailNotificationAdapter.java`)
- [ ] [S] Update the `README.md` Docker Compose example to reflect the three-service topology (gateway on 3000, user-service, payment-service on 8080) consistent with `AGENTS.md` section 2 project structure and the `docker-compose.yml` / `docker-compose.test.yml` files referenced there
- [ ] [M] Reconcile `AGENTS.md` stack table and project structure section to accurately reflect the current codebase: confirm Spring Boot version (3.x), verify the `gateway/` directory naming matches the `user-payment-service/` root layout, and ensure all source paths listed (e.g. `UserReposit` truncation in the project tree) are completed and accurate
- [ ] [S] Add a note in `README.md` under the payment-service section documenting that `InMemoryPaymentRepository` (`payment-service/src/main/java/com/payments/adapters/outbound/persistence/InMemoryPaymentRepository.java`) is the active persistence adapter and is not suitable for production, directing readers to replace it with a JPA/R2DBC adapter
- [ ] [S] Add a note in `README.md` under the payment-service section documenting that `PayPalGatewayAdapter` (`payment-service/src/main/java/com/payments/adapters/outbound/paypal/PayPalGatewayAdapter.java`) and `EmailNotificationAdapter` (`payment-service/src/main/java/com/payments/adapters/outbound/notification/EmailNotificationAdapter.java`) contain stub implementations with TODO items, so operators know real integrations are pending
- [ ] [XS] Verify `README.md` quick-start commands for the user-management service match the `scripts` block in `user-management/package.json` (`npm start`, `npm run dev`, `npm test`) — update any stale commands

---

## Phase 3 — Testing & Validation

N/A — not applicable to this task

---

## Phase 4 — CI/CD & Infrastructure

N/A — not applicable to this task

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Add a `## Changelog` entry (or update an existing one) in `README.md` recording the documentation corrections: Java runtime version fix, service table reconciliation, environment variable additions, and stub-adapter notices
- [ ] [XS] Open a PR from `docs/modernize-stack` to `main` with a description summarising each documentation change and the specific discrepancy it resolves, referencing the relevant source files (e.g. `StripeGatewayAdapter.java`, `PayPalGatewayAdapter.java`, `AGENTS.md`) for reviewer traceability
- [ ] [XS] After merge, verify the rendered `README.md` and `AGENTS.md` on GitHub display all tables, code blocks, and architecture diagrams correctly with no broken Markdown formatting