# PLAN: Update Project Documentation to Reflect Modernized Stack

## Overview

**Migration strategy: Big-bang (single-pass documentation update)**

The task is a documentation-only modernization: reconciling `README.md` and `AGENTS.md` with the actual implemented stack visible in the source code. No runtime code, infrastructure, or dependencies are being changed. The risk score is low (documentation carries no deployment risk) and the effort estimate is small (moderate option, documentation-scoped). A big-bang approach is appropriate — all documentation files are updated in a single coordinated pass, reviewed, and merged. There is no need for strangler-fig or feature-flag strategies on a docs-only change.

The primary discrepancy driving this work is that `README.md` describes the payment service as **Java 17 · Spring Boot 3.2**, while `AGENTS.md` and the actual source code (`jakarta.validation` imports, Spring Boot 3.x conventions, Java records in `ProcessPaymentRequest.java`) confirm the runtime is **Java 21 LTS · Spring Boot 3.x**. Additional gaps exist in the README's architecture description, environment variable tables, and service structure relative to what `AGENTS.md` and the code context show.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 | Audit: diff `README.md` against `AGENTS.md` and source code to produce a complete list of inaccuracies | None | 0.25 person-days |
| 2 | Update `README.md` service table, stack versions, architecture section, endpoint tables, environment variable tables, and quick-start commands | Phase 1 audit complete | 0.5 person-days |
| 3 | Review and align `AGENTS.md` for any gaps (project structure completeness, stack table accuracy) | Phase 2 complete | 0.25 person-days |
| 4 | Peer review, approval, and merge | Phases 2–3 complete | 0.25 person-days |

**Total estimated effort: ~1.25 person-days** (derived from the moderate upgrade option for a documentation-scoped task).

---

## Component Changes

### `README.md`

**What changes structurally:**

1. **Service table (top of file)** — The `payment-service` row must be corrected:

   | Current (incorrect) | Corrected |
   |---|---|
   | `Java 17 · Spring Boot 3.2` | `Java 21 LTS · Spring Boot 3.x` |

   The `user-management` row (`Node.js 20 · Express 4`) is consistent with `AGENTS.md` and `package.json` — no change required.

2. **Architecture Overview section** — The hexagonal architecture diagram is accurate in concept but the service names in the diagram should match the directory names used in `AGENTS.md` (`gateway/`, `user-service/`, `payment-service/`) rather than the generic labels currently shown.

3. **Services section — User Management Service** — The quick-start block references `cd user-management`; the actual directory per `AGENTS.md` and `package.json` (`"name": "user-management-service"`) is `user-management`. Verify directory name consistency. The endpoint table is consistent with the route files (`auth.routes.js`, `user.routes.js`) — no change required.

4. **Services section — Payment Service** — The quick-start block is accurate (`cd payment-service`, `./mvnw spring-boot:run`). The endpoint table matches `PaymentController.java` (`POST /api/payments`, `GET /api/payments/{id}`, `POST /api/payments/{id}/refund`) — no change required.

5. **Environment Variables — Payment Service table** — The following variables are referenced in source but absent or misnamed in the README:

   | Variable in source | Current README status | Action |
   |---|---|---|
   | `stripe.api.key` → env key `STRIPE_API_KEY` | Present | Confirm |
   | `paypal.client.id` → `PAYPAL_CLIENT_ID` | Present | Confirm |
   | `paypal.client.secret` → `PAYPAL_CLIENT_SECRET` | Present | Confirm |
   | `paypal.mode` → `PAYPAL_MODE` | Present | Confirm |
   | `notification.email.enabled` → `NOTIFICATION_EMAIL_ENABLED` | Present | Confirm |
   | `oauth2.issuer.uri` → `OAUTH2_ISSUER_URI` | Present | Confirm |
   | `SERVER_PORT` | Present | Confirm |

   Source: `PayPalGatewayAdapter.java` (`${paypal.client.id}`, `${paypal.client.secret}`, `${paypal.mode:sandbox}`), `StripeGatewayAdapter.java` (`${stripe.api.key}`), `EmailNotificationAdapter.java` (`${notification.email.enabled:false}`).

6. **Docker Compose example** — The truncated `docker-compose.yml` snippet in the README should be completed to reference all three services (`gateway`, `user-service`, `payment-service`) consistent with `AGENTS.md` section 2 and `docker-compose.yml` / `docker-compose.test.yml` file references.

7. **Running Both Services Together section** — Update to reflect the three-service architecture (gateway + user-service + payment-service) rather than the two-service framing.

**Files affected:** `README.md`

---

### `AGENTS.md`

**What changes structurally:**

1. **Stack table** — The table in `AGENTS.md` section 1 is largely accurate. Verify the Spring Boot version entry reads `Spring Boot 3.x` (not a specific patch) to stay consistent with the corrected README.

2. **Project Structure tree** — The `user-service/src/main/java/com/company/userservice/UserReposit` entry is truncated in the provided context. Ensure the full path is present in the actual file. The `payment-service` tree should reflect the package structure visible in source: `com.payments.adapters.inbound.rest` (`HealthController`, `PaymentController`), `com.payments.adapters.outbound.persistence` (`InMemoryPaymentRepository`, `PaymentEntity`), `com.payments.adapters.outbound.stripe` (`StripeGatewayAdapter`), `com.payments.adapters.outbound.paypal` (`PayPalGatewayAdapter`), `com.payments.adapters.outbound.notification` (`EmailNotificationAdapter`), `com.payments.application.service` (`PaymentApplicationService`), `com.payments.application.dto` (`ProcessPaymentRequest`, `ProcessPaymentResponse`, `RefundRequest`, `RefundResponse`), `com.payments.domain.model` (`Payment`, `PaymentMethod`, `PaymentStatus`), `com.payments.domain.ports.inbound` (`GetPaymentUseCase`, `ProcessPaymentUseCase`, `RefundPaymentUseCase`), `com.payments.domain.ports.outbound` (`PaymentRepositoryPort`, `StripeGatewayPort`, `PayPalGatewayPort`, `NotificationPort`).

3. **Gateway section** — The `gateway/` directory tree in `AGENTS.md` matches the source files provided (`app.js`, `server.js`, `config/index.js`, `config/oauth2.js`, middleware files, route files, controller files, service files, schema files, utils). No structural changes needed.

**Files affected:** `AGENTS.md`

---

## Dependency Upgrade Plan

N/A — not applicable to this task. No dependency versions are being changed; this is a documentation-only update. All version references in documentation must be aligned to what is already deployed, as confirmed by `package.json` and source code imports.

For reference, the versions to be reflected accurately in documentation (sourced from `package.json` and `AGENTS.md`):

| Component | Version to Document | Source of Truth |
|---|---|---|
| Node.js | 20 LTS | `AGENTS.md` stack table |
| Express | 4.x (`^4.18.2`) | `package.json` dependencies |
| Java | 21 LTS | `AGENTS.md` stack table |
| Spring Boot | 3.x | `AGENTS.md` stack table; `jakarta.validation` imports confirm Spring Boot 3 |
| PostgreSQL | 15 | `AGENTS.md` stack table |
| Redis | 7 | `AGENTS.md` stack table |
| Jest | `^29.7.0` | `package.json` devDependencies |
| Supertest | `^6.3.3` | `package.json` devDependencies |
| bcryptjs | `^2.4.3` | `package.json` dependencies |
| jsonwebtoken | `^9.0.2` | `package.json` dependencies |
| nodemailer | `^6.9.7` | `package.json` dependencies |
| uuid | `^9.0.0` | `package.json` dependencies |

---

## Infrastructure Changes

N/A — not applicable to this task. No Docker base images, Kubernetes manifests, CI/CD pipelines, or IaC files are being modified. The existing `docker-compose.yml`, `docker-compose.test.yml`, `.github/workflows/ci.yml`, and `.github/workflows/security-scan.yml` are referenced in documentation but not changed.

---

## Rollback Strategy

Because this task touches only Markdown documentation files tracked in Git, rollback is trivially achievable at any phase:

**Phase 1 (Audit):** No files modified; nothing to roll back.

**Phase 2 (README.md updates):**
- Revert via `git revert <commit-sha>` targeting the README.md commit, or `git checkout <previous-sha> -- README.md`.
- The previous README.md state is fully recoverable from Git history.

**Phase 3 (AGENTS.md updates):**
- Revert via `git revert <commit-sha>` targeting the AGENTS.md commit, or `git checkout <previous-sha> -- AGENTS.md`.

**Phase 4 (Merge):**
- If the PR has been merged and issues are found post-merge, open a follow-up PR with corrective changes, or revert the merge commit: `git revert -m 1 <merge-commit-sha>`.

Each file change is independently reversible because `README.md` and `AGENTS.md` are modified in separate commits within the same PR.

---

## Testing Strategy

Documentation changes do not participate in the standard unit/integration/performance test pyramid. The applicable verification strategy is:

**Linting / formatting gates (CI):**
- If a Markdown linter (e.g. `markdownlint`) is configured in `.github/workflows/ci.yml`, it must pass on the updated files. TODO: confirm whether `markdownlint` or equivalent is present in `ci.yml`.
- All code blocks in the README (bash commands, YAML snippets) should be manually verified to be syntactically correct.

**Accuracy review checklist (manual, pre-merge):**
1. Every version number in `README.md` matches a corresponding entry in `AGENTS.md`, `package.json`, or source imports.
2. Every file path in `AGENTS.md` section 2 project structure tree corresponds to an actual file in the repository.
3. Every environment variable in the README tables matches a `@Value("${...}")` annotation or `config/index.js` reference in source.
4. Every endpoint in the README endpoint tables matches a `@GetMapping`/`@PostMapping`/route definition in source (`PaymentController.java`, `auth.routes.js`, `user.routes.js`, `payment.routes.js`).
5. Quick-start commands (`npm install`, `npm start`, `./mvnw spring-boot:run`) are verified against `package.json` scripts and the Maven wrapper presence.

**CI gate:** PR must pass all existing CI checks in `.github/workflows/ci.yml` (which run the Node.js Jest suite and Java JUnit 5 suite). Documentation changes should not break any existing test. No new CI gates are required for this task.

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| Audit complete — inaccuracy list signed off | Phase 1 | Day 1, morning | TODO |
| `README.md` updated and pushed to feature branch | Phase 2 | Day 1, afternoon | TODO |
| `AGENTS.md` reviewed and updated | Phase 3 | Day 2, morning | TODO |
| PR reviewed, approved, and merged to main | Phase 4 | Day 2, afternoon | TODO |

**Total calendar time: ~2 days** at moderate effort, consistent with the ~1.25 person-days estimate accounting for review cycles.