# Spec: Configure GitHub Actions CI Pipeline (Lint, Test, Security Scan)

## Summary

This spec covers the creation and configuration of a GitHub Actions CI pipeline for the `user-payment-service` monorepo. The pipeline will enforce code quality (linting), execute automated test suites, and run security scans across both the Node.js 20 / Express 4 `user-management` service and the Java 21 / Spring Boot 3.x `payment-service`. The expected outcome is a fully automated CI workflow that runs on every pull request and push to the main branch, blocking merges on lint failures, test failures, or detected security vulnerabilities.

## Motivation

- **No existing CI enforcement:** The repository contains two production services with test suites (Jest + Supertest for Node.js; JUnit 5 + Mockito + Testcontainers for Java) but no automated pipeline to run them on code changes. Defects and regressions can merge undetected.
- **Security posture:** Both services handle authentication (JWT, OAuth2), payment processing (Stripe, PayPal), and sensitive user data. Without automated dependency auditing and SAST scanning, known CVEs in dependencies (e.g., `jsonwebtoken ^9.0.2`, `express ^4.18.2`, Spring Boot 3.x transitive dependencies) may go unnoticed.
- **Code quality consistency:** ESLint and Prettier configuration files (`.eslintrc.js`, `.prettierrc`) exist in the `gateway/` layer and the `user-management` service but are not enforced automatically. Java code style is similarly unenforced in CI.
- **Upgrade urgency:** Medium. Services are in active development; establishing CI gates now prevents accumulation of quality and security debt before the codebase grows further.
- **Compliance readiness:** Payment processing integrations (Stripe, PayPal) and OAuth2 token handling require demonstrable security controls; automated scanning supports audit evidence.

## Current State

The repository structure defines two workflow file placeholders under `.github/workflows/` but no implemented pipeline content is present in the provided context:

| File | Current State |
|---|---|
| `.github/workflows/ci.yml` | Placeholder — no implemented content provided |
| `.github/workflows/security-scan.yml` | Placeholder — no implemented content provided |

**Node.js service (`user-management`):**
- Runtime: Node.js 20 LTS
- Package manager: npm (with `package-lock.json`)
- Test runner: Jest 29.7.0 with coverage (`npm test` → `jest --coverage`)
- Test location: `user-management/src/__tests__/**/*.test.js`
- Lint config: `.eslintrc.js` (referenced in `gateway/`; TODO: confirm presence in `user-management/`)
- Formatter config: `.prettierrc`
- Key test files: `health.test.js`, `loginUser.test.js`, `registerUser.test.js`

**Java service (`payment-service`):**
- Runtime: Java 21 LTS (AGENTS.md); README.md states Java 17 — **see Open Questions**
- Build tool: Maven (Maven Wrapper `./mvnw` referenced in README)
- Test runner: JUnit 5 + Mockito; integration tests use Testcontainers
- Test command: `./mvnw test`
- Key test files: `HealthControllerTest.java`, `PaymentControllerTest.java`, `PaymentApplicationServiceTest.java`
- Spring Boot version: 3.x (AGENTS.md) / 3.2 (README.md)

**Docker:**
- `docker-compose.yml` and `docker-compose.test.yml` exist for local and test environments
- Both services have `Dockerfile`s

**Security tooling:** No existing SAST or dependency audit tooling is configured in CI.

## Proposed Changes

| Component | Before | After | Breaking? |
|---|---|---|---|
| `.github/workflows/ci.yml` | Empty placeholder | Implemented workflow: Node.js lint + test job; Java build + test job; triggered on push and pull_request to main | N |
| `.github/workflows/security-scan.yml` | Empty placeholder | Implemented workflow: npm audit for Node.js; OWASP Dependency-Check or Maven dependency audit for Java; CodeQL or equivalent SAST scan | N |
| Node.js lint step | Not enforced in CI | ESLint run against `user-management/` source; Prettier format check | N |
| Node.js test step | Manual only | `npm ci` + `npm test` (Jest with coverage) executed in CI on Node.js 20 | N |
| Java build + test step | Manual only | `./mvnw verify` (compiles, runs unit and integration tests) executed in CI on Java 21 | N |
| Coverage reporting | Not collected in CI | Jest coverage report and JaCoCo (or Maven Surefire) report uploaded as CI artifacts | N |
| Dependency audit (Node.js) | Not automated | `npm audit` with configurable severity threshold | N |
| Dependency audit (Java) | Not automated | Maven dependency vulnerability check (OWASP Dependency-Check plugin or equivalent) | N |
| SAST scan | Not present | GitHub CodeQL analysis or equivalent, covering JavaScript and Java | N |
| CI trigger | None | Push to `main`/`master`; all pull requests targeting `main`/`master` | N |

## Compatibility & Breaking Changes

No breaking changes are introduced. The CI pipeline is additive infrastructure. The following migration notes apply to contributors:

| Change | Impact on Callers | Migration Path |
|---|---|---|
| Lint enforcement on PRs | PRs with ESLint violations will fail CI | Fix lint errors locally before pushing; run ESLint against `user-management/` source |
| Test gate on PRs | PRs with failing Jest or JUnit tests will be blocked | All existing tests must pass; new code must include passing tests |
| `npm ci` replaces `npm install` in CI | Requires committed `package-lock.json` | `package-lock.json` is already present; no action needed |
| Security scan on PRs | PRs introducing high/critical CVEs may be flagged | Review and remediate flagged dependencies; severity threshold policy TODO — see Open Questions |
| Java version pinned in CI | Builds will fail if source is incompatible with pinned JDK | Resolve Java 17 vs. Java 21 discrepancy first (see Open Questions) |

## Acceptance Criteria

1. **Given** a pull request is opened against the main branch, **when** the CI workflow triggers, **then** the `ci.yml` workflow runs and its status is reported on the pull request within GitHub's checks UI.

2. **Given** the Node.js CI job runs, **when** `npm ci` executes in the `user-management/` directory, **then** all dependencies install without error using the committed `package-lock.json`.

3. **Given** the Node.js CI job runs, **when** ESLint is executed against the `user-management/src/` directory, **then** the step exits with code 0 when no lint violations are present, and exits with a non-zero code when violations exist.

4. **Given** the Node.js CI job runs, **when** `npm test` executes, **then** all Jest tests in `user-management/src/__tests__/` pass (including `health.test.js`, `loginUser.test.js`, `registerUser.test.js`) and the job exits with code 0.

5. **Given** a test in `user-management/src/__tests__/` is intentionally broken, **when** the CI pipeline runs, **then** the Node.js test job fails and the pull request check is marked as failed.

6. **Given** the Java CI job runs, **when** `./mvnw verify` executes in the `payment-service/` directory with the correct JDK version, **then** all JUnit 5 tests (including `HealthControllerTest`, `PaymentControllerTest`, `PaymentApplicationServiceTest`) pass and the job exits with code 0.

7. **Given** a JUnit test in `payment-service/` is intentionally broken, **when** the CI pipeline runs, **then** the Java test job fails and the pull request check is marked as failed.

8. **Given** the CI pipeline completes successfully, **when** the workflow run is inspected, **then** Jest coverage output and Maven Surefire/JaCoCo reports are available as downloadable artifacts on the workflow run.

9. **Given** the security scan workflow runs, **when** `npm audit` executes against `user-management/` dependencies, **then** the step fails if any dependency has a vulnerability at or above the configured severity threshold (TODO: threshold to be confirmed — see Open Questions).

10. **Given** the security scan workflow runs, **when** the Java dependency vulnerability check executes against `payment-service/pom.xml`, **then** the step fails if any dependency has a known CVE at or above the configured severity threshold.

11. **Given** the SAST scan runs via CodeQL (or equivalent), **when** it analyses JavaScript source in `user-management/` and Java source in `payment-service/`, **then** results are published to the GitHub Security tab and the workflow step completes without infrastructure error.

12. **Given** a push is made directly to the main branch, **when** the CI and security scan workflows trigger, **then** both workflows execute all jobs end-to-end without configuration errors.

13. **Given** the CI pipeline runs, **when** no secrets (`JWT_SECRET`, `STRIPE_API_KEY`, `PAYPAL_CLIENT_SECRET`, etc.) are present in the environment, **then** tests that do not require live external services still pass (unit tests and mocked integration tests must not require real credentials).

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | Java runtime version discrepancy: AGENTS.md specifies Java 21 LTS; README.md states Java 17. Which version should be pinned in the CI workflow matrix? | TODO | TODO |
| 2 | Spring Boot version discrepancy: AGENTS.md states Spring Boot 3.x; README.md states Spring Boot 3.2. Should the CI workflow pin a specific patch version for reproducibility? | TODO | TODO |
| 3 | Does an `.eslintrc.js` file exist in `user-management/` (separate from `gateway/.eslintrc.js`), or should the gateway config be extended/shared? | TODO | TODO |
| 4 | What is the minimum severity threshold for `npm audit` and the Java dependency scan to fail the build (low / moderate / high / critical)? | TODO | TODO |
| 5 | Should the security scan run on every PR, on a scheduled cron, or both? | TODO | TODO |
| 6 | Do Testcontainers-based integration tests in `payment-service/` require Docker-in-Docker in the CI runner, or is the GitHub Actions hosted runner environment sufficient? | TODO | TODO |
| 7 | Are there required secrets (e.g., `STRIPE_API_KEY`, `OAUTH2_ISSUER_URI`) that must be configured as GitHub Actions repository secrets for any CI test to pass, or are all tests fully mocked? | TODO | TODO |
| 8 | Should CI enforce a minimum code coverage threshold (e.g., fail if Jest coverage drops below X%)? If yes, what is the threshold? | TODO | TODO |
| 9 | Which SAST tool is preferred: GitHub CodeQL (free for public repos), or a third-party tool (e.g., Snyk, SonarCloud)? | TODO | TODO |
| 10 | Should the `gateway/` Node.js layer have its own CI job separate from `user-management/`, given it has its own `package.json` and test config? | TODO | TODO |