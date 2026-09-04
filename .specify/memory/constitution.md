# CONSTITUTION — GitHub Actions CI Pipeline

## Project Identity

**Name:** user-payment-service CI Pipeline
**Purpose:** Configure a GitHub Actions CI pipeline that enforces code quality, test coverage, and security hygiene across both the `user-management` (Node.js 20 / Express) and `payment-service` (Java 21 / Spring Boot 3.x) microservices in a single monorepo.
**High-level goal:** Every pull request and push to the main branch must pass lint, automated tests, and a security scan before merge is permitted.

---

## Guiding Principles

1. **Prefer per-service jobs over a single monolithic job** because the two services use different runtimes (Node.js 20 and Java 21) and toolchains (npm/Jest vs. Maven/JUnit 5); conflating them increases failure blast radius and obscures root cause.
2. **Prefer path-filtered triggers over always-on triggers** because changes to `user-management/` should not re-run the Java test suite and vice versa, keeping CI fast and resource-efficient.
3. **Prefer secrets-based injection over hardcoded values** because the codebase handles payment credentials (Stripe, PayPal) and JWT secrets; no secret must appear in workflow YAML or logs.
4. **Prefer fail-fast lint before test execution** because ESLint (Node.js) and Checkstyle/SpotBugs (Java) catch trivial errors cheaply; running the full test suite on broken code wastes CI minutes.
5. **Prefer dependency audit as a mandatory gate over advisory-only** because the service processes financial transactions and user credentials, making supply-chain risk a compliance concern, not a nice-to-have.
6. **Prefer Docker Compose test environment for integration tests** because `docker-compose.test.yml` already exists and Testcontainers requires a Docker daemon; the CI runner must support Docker-in-Docker or a Docker socket.

---

## Constraints

| Constraint | Detail |
|---|---|
| **Effort ceiling** | Moderate option — scope is limited to pipeline configuration only; no refactoring of application code. |
| **Node.js runtime** | 20 LTS (as declared in `AGENTS.md` and `package.json`) |
| **Java runtime** | 21 LTS (as declared in `AGENTS.md`; README states Java 17 — **TODO: confirm canonical version before finalising workflow `java-version`**) |
| **Build tools** | npm (Node.js), Maven Wrapper `./mvnw` (Java) — no Gradle, no Yarn |
| **CI platform** | GitHub Actions exclusively; no external CI service |
| **Workflow files** | Must live at `.github/workflows/ci.yml` and `.github/workflows/security-scan.yml` per existing project structure |
| **Secrets** | `JWT_SECRET`, `STRIPE_API_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` must be consumed from GitHub Actions secrets; never echoed |
| **Scope freeze** | Pipeline configuration only — no changes to application source, test files, or Docker images |

---

## Quality Standards

| Standard | Measurable Bar |
|---|---|
| **Node.js test coverage** | Jest `--coverage` must report ≥ 80% line coverage across `src/**/*.js` (excluding `src/__tests__/`); pipeline fails below this threshold |
| **Java test execution** | `./mvnw test` must exit 0; any failing JUnit 5 test fails the pipeline |
| **Lint — Node.js** | ESLint must exit 0 with zero errors (warnings permitted); config sourced from existing `.eslintrc.js` |
| **Lint — Java** | TODO: confirm whether Checkstyle or SpotBugs plugin is present in `pom.xml`; at minimum `./mvnw verify` must pass |
| **Dependency audit — Node.js** | `npm audit --audit-level=high` must exit 0; high or critical CVEs block merge |
| **Dependency audit — Java** | OWASP Dependency-Check or `./mvnw dependency:analyze` must run in `security-scan.yml`; critical findings block merge |
| **PR gate** | All CI jobs must be configured as required status checks; merge to main is blocked until all pass |
| **Workflow documentation** | Each workflow file must include inline comments explaining every job and non-obvious step |

---

## Decision Log

| ID | Decision | Rationale | Status |
|---|---|---|---|
| ADR-001 | Split CI into two workflow files: `ci.yml` (lint + test) and `security-scan.yml` (SAST + audit) | Matches existing file structure in `.github/workflows/`; separates fast feedback from slower security scans | Accepted |
| ADR-002 | Use `actions/setup-node@v4` with `node-version: '20'` and `actions/setup-java@v4` with `distribution: 'temurin'` | Aligns with declared runtimes; Temurin is the standard LTS distribution for GitHub Actions | Accepted |
| ADR-003 | Cache npm dependencies (`~/.npm`) and Maven local repository (`~/.m2`) in CI | Reduces cold-start time on repeated runs; standard practice for both ecosystems | Accepted |
| ADR-004 | Run integration tests using `docker-compose.test.yml` | File already exists; Testcontainers used by Java service requires Docker; avoids duplicating environment setup | Accepted |
| ADR-005 | Canonical Java version is TODO | `AGENTS.md` states Java 21; `README.md` states Java 17; must be resolved by reviewing `pom.xml` `<java.version>` property before workflow is written | Proposed |