# Plan: Configure GitHub Actions CI Pipeline (Lint, Test, Security Scan)

## Overview

**Migration strategy: Big-bang (single-PR delivery)**

The task is greenfield CI configuration — no existing `.github/workflows/` files are in production, so there is no live pipeline to migrate away from. The risk is low: a misconfigured workflow file fails silently in CI without affecting running services. The effort estimate is small (moderate option, ~3–5 person-days total across both services), making a single coordinated delivery the most practical approach. Both workflow files (`ci.yml` and `security-scan.yml`) are introduced together so that every subsequent pull request is immediately covered.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|---|---|---|---|
| 1 | Author `.github/workflows/ci.yml` — lint + test jobs for both `user-management` (Node.js) and `payment-service` (Java/Maven) | None | 1 person-day |
| 2 | Author `.github/workflows/security-scan.yml` — dependency audit (npm audit, OWASP Dependency-Check) and SAST (CodeQL) | Phase 1 workflow structure as reference | 1 person-day |
| 3 | Validate pipelines on a feature branch: fix job failures, tune coverage gates, confirm security scan thresholds | Phases 1 & 2 merged to feature branch | 0.5 person-days |
| 4 | Merge to main, set branch-protection rules requiring CI to pass | Phase 3 green | 0.5 person-days |

---

## Component Changes

### `.github/workflows/ci.yml` (new file)

**Structure:** Two parallel jobs — `lint-and-test-gateway` (Node.js) and `lint-and-test-payment` (Java).

**`lint-and-test-gateway` job**
- Checks out repo, sets up Node.js 20.
- Working directory: `user-management/`.
- Runs `npm ci` using `user-management/package-lock.json`.
- Lint step: `npx eslint .` — config sourced from `gateway/.eslintrc.js` (referenced in AGENTS.md; apply same config pattern to `user-management/` if an `.eslintrc.js` is present, otherwise create one).
- Format check: `npx prettier --check .` — config from `gateway/.prettierrc`.
- Test step: `npm test` — invokes `jest --coverage` as defined in `user-management/package.json` `scripts.test`.
- Coverage enforcement: Jest `--coverageThreshold` flag or `jest.config.js` entry; target ≥ 80 % lines (derived from existing `collectCoverageFrom` config in `user-management/package.json`).
- Uploads `user-management/coverage/` as a workflow artifact.

**`lint-and-test-payment` job**
- Checks out repo, sets up Java 21 (matches AGENTS.md runtime; README states Java 17 — use 21 per AGENTS.md as authoritative).
- Working directory: `payment-service/`.
- Caches `~/.m2/repository` keyed on `payment-service/pom.xml` hash.
- Build + test step: `./mvnw verify` — runs `JUnit 5` tests including `HealthControllerTest`, `PaymentControllerTest`, and `PaymentApplicationServiceTest`.
- Surefire report uploaded as artifact.
- No separate lint step for Java at this stage (TODO: add Checkstyle or SpotBugs plugin to `pom.xml` if required).

**Trigger:** `push` and `pull_request` on all branches.

---

### `.github/workflows/security-scan.yml` (new file)

**Structure:** Two jobs — `dependency-audit` and `sast`.

**`dependency-audit` job**
- Node.js audit: `npm audit --audit-level=high` in `user-management/`.
- Java audit: OWASP Dependency-Check Maven plugin (`./mvnw dependency-check:check`) in `payment-service/`. Fails build on CVSS ≥ 7 (TODO: confirm threshold with security team).
- Uploads Dependency-Check HTML report as artifact.

**`sast` job**
- Uses `github/codeql-action` with languages `javascript` (covers `user-management/`) and `java` (covers `payment-service/`).
- Auto-build mode for Java; no custom build command needed for CodeQL given Maven wrapper is present.

**Trigger:** `push` to `main`, `pull_request` targeting `main`, and `schedule` (weekly, e.g. `cron: '0 3 * * 1'`).

---

### `user-management/package.json` (existing file — minor addition)

Add a dedicated `lint` script so CI can call it explicitly:

```json
"scripts": {
  "lint": "eslint src/",
  "lint:format": "prettier --check src/",
  ...
}
```

No version changes required.

---

### `payment-service/pom.xml` (existing file — TODO)

If Checkstyle or SpotBugs linting is desired for Java, add the relevant Maven plugin. Not strictly required for the initial pipeline but noted as a follow-up. Mark as TODO until `pom.xml` content is available in context.

---

## Dependency Upgrade Plan

No runtime dependency upgrades are required by this task. The CI pipeline consumes existing tooling already declared in the project.

| Dependency | Current Version | Target Version | Breaking Changes | Migration Notes |
|---|---|---|---|---|
| `jest` (devDependency) | `^29.7.0` | `^29.7.0` | None | Already at target; no change needed |
| `eslint` | Not pinned in `user-management/package.json` | Install as devDependency if absent | N/A | Add `"eslint": "^8.x"` to `user-management/package.json` devDependencies if not present; config pattern mirrors `gateway/.eslintrc.js` |
| `prettier` | Not pinned in `user-management/package.json` | Install as devDependency if absent | N/A | Add `"prettier": "^3.x"` if not present; config mirrors `gateway/.prettierrc` |
| GitHub Actions `actions/checkout` | N/A (new) | `v4` | N/A | Use `actions/checkout@v4` |
| GitHub Actions `actions/setup-node` | N/A (new) | `v4` | N/A | Use `actions/setup-node@v4` with `node-version: '20'` |
| GitHub Actions `actions/setup-java` | N/A (new) | `v4` | N/A | Use `actions/setup-java@v4` with `distribution: 'temurin'`, `java-version: '21'` |
| GitHub Actions `github/codeql-action` | N/A (new) | `v3` | N/A | Use `github/codeql-action/init@v3`, `autobuild@v3`, `analyze@v3` |

> All version numbers above are derived from the tech analysis context (Node.js 20 LTS, Java 21 LTS per AGENTS.md). GitHub Actions action versions are the current stable releases — TODO: confirm with platform team if an internal mirror or pinned SHA policy is required.

---

## Infrastructure Changes

**GitHub Actions runners:** Both workflows use `ubuntu-latest`. No self-hosted runners are referenced in context — TODO: confirm whether the organisation mandates self-hosted runners.

**Docker:** The existing `gateway/Dockerfile` and `payment-service/Dockerfile` are not invoked by the CI lint/test jobs (tests run directly via `npm test` / `./mvnw verify`). Docker Compose (`docker-compose.test.yml`) is referenced in AGENTS.md for containerised DB/Redis integration tests via Testcontainers — the Java job may need Docker-in-Docker or the `ubuntu-latest` runner's built-in Docker daemon. Add `services:` block or `docker compose -f docker-compose.test.yml up -d` step if Testcontainers tests require live PostgreSQL/Redis. TODO: verify whether `PaymentControllerTest` and `PaymentApplicationServiceTest` use Testcontainers or in-memory stubs (current code shows `InMemoryPaymentRepository`, so no external DB is needed for the existing test suite).

**Branch protection:** After Phase 4, configure the `main` branch rule in GitHub repository settings to require `lint-and-test-gateway` and `lint-and-test-payment` status checks to pass before merge. TODO: confirm branch-protection configuration is managed via Terraform/IaC or manually.

**Secrets:** The following repository secrets must be created in GitHub (Settings → Secrets → Actions) before the security-scan workflow runs end-to-end:

| Secret Name | Used By | Notes |
|---|---|---|
| `STRIPE_API_KEY` | `payment-service` integration tests (if any hit real Stripe) | Use `sk_test_…` value; not needed if all tests are mocked |
| `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` | Same caveat | TODO: confirm test isolation |
| `JWT_SECRET` | `user-management` tests | Required if `JwtAuthAdapter` is exercised in integration tests |

Current unit tests (`loginUser.test.js`, `registerUser.test.js`) use mocks and do not require live secrets. `health.test.js` uses `createApp()` with no external calls. Secrets are therefore TODO — add only if integration tests are expanded.

---

## Rollback Strategy

Each phase produces only additive file changes (new YAML files, minor `package.json` script additions). Rollback is straightforward:

| Phase | Rollback Action |
|---|---|
| Phase 1 — `ci.yml` created | Delete or revert `.github/workflows/ci.yml` via a follow-up commit or PR. Pipeline stops running immediately on next push. |
| Phase 2 — `security-scan.yml` created | Delete or revert `.github/workflows/security-scan.yml`. Scheduled scans cease. |
| Phase 3 — Threshold tuning | Revert coverage threshold changes in `jest.config.js` or `package.json`; revert CVSS threshold in `pom.xml` plugin config. Each is an independent commit. |
| Phase 4 — Branch protection enabled | Disable the required status checks in GitHub repository Settings → Branches → Branch protection rules. This is independently reversible without touching code. |

No database migrations, no runtime changes, and no infrastructure provisioning are involved — all rollbacks are single-commit reverts or UI toggles.

---

## Testing Strategy

The CI pipeline itself is validated by running it; the strategy below covers both the pipeline's own correctness and the test suites it executes.

### Unit tests (fastest feedback)
- **Node.js:** Jest, already configured in `user-management/package.json`. Tests in `src/__tests__/` — `loginUser.test.js`, `registerUser.test.js`. Run with `npm test`. Coverage target: **≥ 80 % lines** enforced via Jest `coverageThreshold`.
- **Java:** JUnit 5 + Mockito, `PaymentApplicationServiceTest` (no Spring context, pure unit). Run via `./mvnw test`. Coverage target: **≥ 80 % line coverage** enforced via JaCoCo Maven plugin (add to `pom.xml` if not present — TODO: confirm existing `pom.xml` configuration).

### Integration tests
- **Node.js:** Supertest, `health.test.js` — exercises `createApp()` end-to-end in-process. Included in `npm test` run.
- **Java:** `HealthControllerTest`, `PaymentControllerTest` — `@SpringBootTest` with `MockMvc`. Run via `./mvnw verify`. No external services required given `InMemoryPaymentRepository` and mocked use-case ports.

### Regression gate (CI gate)
- Both `ci.yml` jobs must pass (exit 0) for a PR to be mergeable once branch protection is enabled (Phase 4).
- `security-scan.yml` `dependency-audit` job: `npm audit --audit-level=high` must exit 0; OWASP check must find no CVSS ≥ 7 vulnerabilities.

### Performance tests
N/A — not applicable to this task. No load or performance testing is introduced by the CI pipeline configuration.

### CI gates summary

| Gate | Tool | Threshold | Blocks merge? |
|---|---|---|---|
| Node.js lint | ESLint | Zero errors | Yes (Phase 4) |
| Node.js format | Prettier | Zero diffs | Yes (Phase 4) |
| Node.js unit + integration | Jest | ≥ 80 % line coverage | Yes (Phase 4) |
| Java build + test | Maven / JUnit 5 | All tests green | Yes (Phase 4) |
| Node.js dependency audit | `npm audit` | No high/critical CVEs | Yes (Phase 4) |
| Java dependency audit | OWASP Dependency-Check | CVSS < 7 | Yes (Phase 4) |
| SAST | CodeQL | No critical alerts | TODO: confirm policy |

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|---|---|---|---|
| `ci.yml` authored and pushed to feature branch | Phase 1 | Day 1 | TODO |
| `security-scan.yml` authored and pushed to feature branch | Phase 2 | Day 2 | TODO |
| Both workflows green on feature branch; coverage thresholds confirmed | Phase 3 | Day 2 (afternoon) | TODO |
| PR merged to `main`; branch-protection rules enabled | Phase 4 | Day 3 | TODO |

Total estimated effort: **3 person-days** (within the moderate option range of 3–5 person-days, with the lower bound reflecting that no runtime code changes are required).