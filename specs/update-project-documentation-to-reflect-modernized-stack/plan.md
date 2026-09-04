# PLAN: Update Project Documentation to Reflect Modernized Stack

## Overview

**Migration strategy: Big-bang (single-pass documentation update)**

The task is a documentation-only modernization: reconciling `README.md` and `AGENTS.md` with the actual implemented stack visible in the source code. No runtime code, infrastructure, or dependencies are being changed. The risk score is low (documentation carries no deployment risk) and the effort estimate is small (moderate option, documentation-scoped). A big-bang approach is appropriate — all documentation files are updated in a single coordinated pass, reviewed, and merged. There is no need for strangler-fig or feature-flag strategies for a docs-only change.

The primary discrepancy driving this work is that `README.md` describes the payment service as **"Java 17 · Spring Boot 3.2"** while `AGENTS.md` and the actual source code (`PaymentController.java` uses `jakarta.validation`, `ProcessPaymentRequest.java` uses Java records, `PaymentApplicationService.java` targets Spring Boot 3.x conventions) confirm the runtime is **Java 21 LTS with Spring Boot 3.x**. Additionally, `README.md` describes the user-management service as a standalone Node.js service while `AGENTS.md` describes a gateway/BFF architecture with separate Spring Boot microservices behind it.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 | Audit: diff `README.md` and `AGENTS.md` against source code to produce a complete list of inaccuracies | None | 0.25 person-days |
| 2 | Update `README.md`: correct stack table, service descriptions, project structure, environment variable tables, and Docker Compose example | Phase 1 audit complete | 0.5 person-days |
| 3 | Update `AGENTS.md`: verify stack table entries, project structure tree, and any inline notes against current source | Phase 1 audit complete | 0.25 person-days |
| 4 | Peer review and merge | Phases 2–3 complete | 0.25 person-days |

**Total estimated effort: ~1.25 person-days** (derived from the moderate upgrade option for a documentation-scoped task).

---

## Component Changes

### `README.md`

**What changes structurally:**

1. **Service stack table** (top of file) — The `payment-service` row currently reads `Java 17 · Spring Boot 3.2`. This must be corrected to `Java 21 LTS · Spring Boot 3.x` to match `AGENTS.md` and the source (`UserServiceApplication.java`, `PaymentController.java` with `jakarta.*` imports which require Spring Boot 3.x / Jakarta EE 10, and Java records in `ProcessPaymentRequest.java` which are stable from Java 16+ but the declared runtime in `AGENTS.md` is Java 21).

2. **Service descriptions** — The `user-management` section describes a standalone Node.js service. The actual architecture (per `AGENTS.md` and the `gateway/` source tree) is a **Node.js/Express API Gateway (BFF layer)** that proxies to Spring Boot microservices (`user-service/` and `payment-service/`). The description must reflect this.

3. **Project structure** — `README.md` references `/user-management` and `/payment-service` as top-level directories. The actual structure (per `AGENTS.md`) is:
   - `gateway/` — Node.js/Express BFF
   - `user-service/` — Spring Boot user management
   - `payment-service/` — Spring Boot payment orchestration

4. **Quick-start commands** — The `user-management` quick-start block references `cd user-management`. This must be updated to `cd gateway` (or the correct directory per the actual repo layout).

5. **Environment variable tables** — The user-management table omits variables relevant to the gateway's proxy behaviour (e.g. upstream service URLs). The payment-service table references `OAUTH2_ISSUER_URI` which aligns with `SecurityConfig.java` — this entry is correct and should be retained.

6. **Docker Compose example** — The inline YAML snippet references `./user-management` as the build context. This must be updated to `./gateway`. The `payment-service` port mapping (`8080:8080`) is correct per `HealthController.java` (`/api/health`) and `PaymentController.java` (`/api/payments`).

7. **Architecture diagram** — The hexagonal architecture ASCII diagram is accurate and should be retained unchanged.

**Files affected:**
- `README.md` — all sections noted above

**APIs modified:** None (documentation only).

---

### `AGENTS.md`

**What changes structurally:**

1. **Stack table** — Entries appear accurate against source code. Verify the following specific entries during Phase 1 audit:
   - `Node.js 20 LTS` — confirm against `gateway/package.json` (currently shows `"node"` engine field is absent; TODO: confirm `.nvmrc` or `Dockerfile` in `gateway/`).
   - `Express 4.x` — confirmed: `gateway/package.json` lists `"express": "^4.18.2"`.
   - `Java 21 (LTS)` — confirmed by `AGENTS.md` itself; verify against `user-service/pom.xml` and `payment-service/pom.xml` (not fully shown in context — TODO: confirm `<java.version>` property).
   - `Spring Boot 3.x` — consistent with `jakarta.validation` imports in `PaymentController.java` and `ProcessPaymentRequest.java`.
   - `Jest ^29.7.0` — confirmed: `gateway/package.json` (note: tests live under `user-management/` in context but the gateway is the Node layer per `AGENTS.md`).
   - `JUnit 5 + Mockito` — confirmed: `PaymentApplicationServiceTest.java` uses `@ExtendWith(MockitoExtension.class)` and AssertJ.

2. **Project structure tree** — The tree in `AGENTS.md` is truncated (the `UserReposit` line is cut off). The full `UserRepository` class name and remaining structure entries should be completed.

3. **No other structural changes** are required to `AGENTS.md` based on available context.

**Files affected:**
- `AGENTS.md` — stack table verification, project structure tree completion

**APIs modified:** None (documentation only).

---

### `tasks.md` (if present)

Per `AGENTS.md` section 2, `tasks.md` is described as an "agent-generated task tracker (created before coding)". If this file exists and references the old stack versions, it should be updated to reflect Java 21 and the corrected directory names. **TODO: confirm whether `tasks.md` exists and contains stack references.**

---

## Dependency Upgrade Plan

N/A — not applicable to this task. No dependency versions are being changed; this is a documentation-only update. All version numbers referenced in documentation corrections are sourced directly from `gateway/package.json` and `AGENTS.md` as provided in context.

---

## Infrastructure Changes

N/A — not applicable to this task. No Docker base images, Kubernetes manifests, CI/CD pipelines, or IaC files are being modified. The documentation may reference these artefacts (e.g. `docker-compose.yml`, `.github/workflows/ci.yml`) but their content is not changing.

---

## Rollback Strategy

Because this task touches only Markdown documentation files tracked in Git, rollback is trivially achievable at any phase:

**Phase 1 (Audit):**
- The audit produces no file changes. Nothing to roll back.

**Phase 2 (README.md update):**
- `git revert <commit-sha>` targeting the README.md commit restores the previous content exactly.
- Alternatively: `git checkout <previous-sha> -- README.md && git commit -m "revert: restore README.md"`.

**Phase 3 (AGENTS.md update):**
- `git revert <commit-sha>` targeting the AGENTS.md commit restores the previous content exactly.
- Alternatively: `git checkout <previous-sha> -- AGENTS.md && git commit -m "revert: restore AGENTS.md"`.

**Phase 4 (Merged PR):**
- Revert the merge commit on the main branch: `git revert -m 1 <merge-commit-sha>`.
- Each phase's commit should be atomic (one logical change per commit) to make targeted revert possible without affecting unrelated changes.

---

## Testing Strategy

Documentation changes do not participate in the standard unit/integration/performance test pyramid. The applicable verification strategy is:

**Linting / formatting (CI gate):**
- Run a Markdown linter (e.g. `markdownlint-cli`) against `README.md` and `AGENTS.md` as part of the existing `.github/workflows/ci.yml` pipeline. Add a step if not already present:
  ```yaml
  - name: Lint Markdown
    run: npx markdownlint-cli README.md AGENTS.md
  ```

**Link validation (CI gate):**
- Run a dead-link checker (e.g. `markdown-link-check`) to verify that any URLs or internal anchor links in the updated documents resolve correctly.

**Manual review checklist (peer review gate — Phase 4):**
- [ ] Stack table in `README.md` matches `AGENTS.md` stack table exactly.
- [ ] Directory names in `README.md` quick-start blocks match actual repo structure (`gateway/`, `user-service/`, `payment-service/`).
- [ ] Java version in `README.md` service table reads `Java 21 LTS · Spring Boot 3.x`.
- [ ] `gateway/package.json` `express` version (`^4.18.2`) is consistent with `Express 4.x` in `AGENTS.md`.
- [ ] No sensitive values (API keys, secrets) have been introduced into documentation.
- [ ] `AGENTS.md` project structure tree is complete (no truncated lines).

**No unit, integration, regression, or performance tests are required** for this documentation-only task. The existing test suites (`jest --coverage` for the gateway, `./mvnw test` for Java services) are unaffected and should continue to pass without modification as a baseline CI gate confirming no source files were accidentally modified.

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| Audit complete — inaccuracy list signed off | Phase 1 | Day 1, morning | TODO |
| `README.md` updated and pushed to feature branch | Phase 2 | Day 1, afternoon | TODO |
| `AGENTS.md` updated and pushed to feature branch | Phase 3 | Day 1, afternoon | TODO |
| PR reviewed, CI green, merged to main | Phase 4 | Day 2, morning | TODO |

**Total calendar time: ~1.5 days** (derived from the ~1.25 person-day effort estimate under the moderate upgrade option, with a small buffer for review turnaround).