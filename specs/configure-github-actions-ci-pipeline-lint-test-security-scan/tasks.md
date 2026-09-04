# Tasks: Configure GitHub Actions CI Pipeline (lint, test, security scan)

## Prerequisites

- [ ] [XS] Confirm GitHub Actions is enabled for the repository and the `.github/workflows/` directory exists at the monorepo root
- [ ] [XS] Verify Node.js 20 LTS and Java 21 runner images are available in the GitHub Actions runner environment (ubuntu-latest)
- [ ] [XS] Confirm repository secrets `STRIPE_API_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, and `JWT_SECRET` are registered in GitHub repository Settings → Secrets and variables → Actions (required for integration test steps)
- [ ] [XS] Confirm `package-lock.json` is committed in `user-management/` so `npm ci` is reproducible in CI
- [ ] [XS] Confirm Maven Wrapper (`mvnw` / `.mvn/`) is committed in `payment-service/` so `./mvnw` is executable without a pre-installed Maven binary

---

## Phase 1 — Preparation

- [ ] [XS] Create feature branch `ci/github-actions-pipeline` from `main` in the monorepo root
- [ ] [S] Capture local test baseline for `user-management` by running `npm ci && npm test -- --coverage` in `user-management/` and recording pass/fail counts and coverage percentages from `coverage/` output
- [ ] [S] Capture local test baseline for `payment-service` by running `./mvnw test` in `payment-service/` and recording Surefire pass/fail counts from `target/surefire-reports/`
- [ ] [XS] Add `.env.example` values as non-secret CI environment variable defaults in `.github/workflows/ci.yml` (e.g. `NODE_ENV=test`, `JWT_EXPIRES_IN=7d`, `NOTIFICATION_EMAIL_ENABLED=false`, `PAYPAL_MODE=sandbox`) so tests run without real credentials

---

## Phase 2 — Core Upgrade

- [ ] [M] Create `.github/workflows/ci.yml` with a `lint-and-test-node` job that:
  - triggers on `push` and `pull_request` to `main`
  - uses `actions/checkout@v4`
  - sets up Node.js 20 with `actions/setup-node@v4` and `cache: 'npm'` pointing to `user-management/package-lock.json`
  - runs `npm ci` in `user-management/`
  - runs ESLint via `npx eslint .` using `user-management/.eslintrc.js`
  - runs `npm test -- --coverage` in `user-management/` and uploads `user-management/coverage/` as an artifact

- [ ] [M] Add a `test-java` job to `.github/workflows/ci.yml` that:
  - uses `actions/setup-java@v4` with `distribution: temurin` and `java-version: 21`
  - caches the Maven local repository (`~/.m2`) keyed on `payment-service/pom.xml`
  - runs `./mvnw --batch-mode test` in `payment-service/`
  - uploads `payment-service/target/surefire-reports/` as an artifact
  - sets required environment variables: `OAUTH2_ISSUER_URI`, `STRIPE_API_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` from repository secrets

- [ ] [S] Create `.github/workflows/security-scan.yml` with a `dependency-audit-node` job that:
  - triggers on `push` to `main` and on a weekly schedule (`cron: '0 3 * * 1'`)
  - runs `npm audit --audit-level=high` in `user-management/`
  - fails the job if high or critical vulnerabilities are found

- [ ] [S] Add a `dependency-audit-java` job to `.github/workflows/security-scan.yml` that:
  - uses `actions/setup-java@v4` with `distribution: temurin` and `java-version: 21`
  - runs `./mvnw --batch-mode dependency:check -DfailBuildOnCVSS=7` (OWASP Dependency-Check plugin) in `payment-service/`
  - uploads the generated `target/dependency-check-report.html` as an artifact

- [ ] [S] Add a `codeql-analysis` job to `.github/workflows/security-scan.yml` using `github/codeql-action/init@v3` and `github/codeql-action/analyze@v3` targeting both `javascript` (for `user-management/`) and `java` (for `payment-service/`) language matrices

---

## Phase 3 — Testing & Validation

- [ ] [S] Trigger the `ci.yml` workflow on the feature branch via a draft pull request and confirm the `lint-and-test-node` job passes with the same test counts captured in Phase 1 baseline
- [ ] [S] Confirm the `test-java` job passes and Surefire reports for `HealthControllerTest`, `PaymentControllerTest`, and `PaymentApplicationServiceTest` all show green in the uploaded artifact
- [ ] [XS] Confirm ESLint step exits 0 against `user-management/.eslintrc.js` with no blocking errors
- [ ] [XS] Confirm `npm audit` step in `security-scan.yml` completes without failing on the current `user-management/package.json` dependency set
- [ ] [XS] Confirm OWASP Dependency-Check step completes and the HTML report artifact is accessible in the Actions run summary

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [XS] Add `paths` filters to the `lint-and-test-node` job trigger in `.github/workflows/ci.yml` so it only runs when files under `user-management/**` change, avoiding unnecessary runs on Java-only commits
- [ ] [XS] Add `paths` filters to the `test-java` job trigger in `.github/workflows/ci.yml` so it only runs when files under `payment-service/**` change
- [ ] [XS] Set `JAVA_TOOL_OPTIONS: -Dfile.encoding=UTF-8` as a job-level environment variable in the `test-java` job in `.github/workflows/ci.yml` to prevent encoding issues in Surefire output on ubuntu-latest runners
- [ ] [XS] Add branch protection rule configuration note to `.github/workflows/ci.yml` (as a comment block) documenting that `lint-and-test-node` and `test-java` should be set as required status checks on `main` in repository Settings → Branches

---

## Phase 5 — Documentation & Rollout

- [ ] [S] Update `README.md` to add a "CI Status" section with badge markdown for the `ci.yml` workflow and `security-scan.yml` workflow pointing to the correct repository path
- [ ] [XS] Update `AGENTS.md` stack table to reflect that GitHub Actions CI is now active with lint, test, and security-scan jobs, replacing the placeholder row
- [ ] [XS] Merge the feature branch `ci/github-actions-pipeline` to `main` via pull request after all required status checks pass
- [ ] [XS] Verify the first post-merge run of `security-scan.yml` on `main` completes successfully and the weekly cron schedule is visible in the Actions tab