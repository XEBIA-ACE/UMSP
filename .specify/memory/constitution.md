# CONSTITUTION — User Management and Payment Service Documentation Modernization

## Project Identity

**Name:** User Management and Payment Service — Documentation Update
**Purpose:** Bring all project documentation into accurate alignment with the modernized stack as reflected in `AGENTS.md` and the actual source code.
**Goal:** Eliminate discrepancies between `README.md` and the real runtime stack (e.g., `README.md` incorrectly lists `Java 17 · Spring Boot 3.2` for the payment service; the authoritative stack is `Java 21 LTS · Spring Boot 3.x`), and ensure every documented quick-start, environment variable, architecture description, and service table is accurate and verifiable against the codebase.

---

## Guiding Principles

1. **Prefer source-of-truth accuracy over completeness** because stale documentation (e.g., wrong Java version) causes developer environment failures and erodes trust in the docs.
2. **Prefer `AGENTS.md` stack table over `README.md` prose** when the two conflict, because `AGENTS.md` is the designated authoritative stack reference for this project.
3. **Prefer minimal, targeted edits over rewrites** because the upgrade option is moderate-scope; only content that is factually incorrect or missing should change.
4. **Prefer verified environment variables over assumed ones** because undocumented or wrong env vars (e.g., missing `DATABASE_URL`, `REDIS_URL`) block onboarding; every variable in `.env.example` must appear in the README table.
5. **Prefer concrete version pins in documentation** over vague references (e.g., "Spring Boot 3.x") because developers need reproducible environments.

---

## Constraints

- **Effort ceiling:** Moderate option — scope is limited to documentation files (`README.md`, `AGENTS.md`, and any inline code comments that reference stack versions). No source code logic changes are in scope.
- **Technology mandates (authoritative stack, must be reflected accurately):**
  - Node.js **20 LTS** / Express **4.x** — API Gateway / BFF
  - Java **21 LTS** / Spring Boot **3.x** — User and Payment microservices
  - PostgreSQL **15**, Redis **7**
  - Flyway (schema migrations), Testcontainers (Java integration tests)
  - GitHub Actions (CI/CD)
- **Scope freeze:** No changes to application source code, test logic, or CI pipeline configuration. Documentation only.
- **No invented content:** TODO markers must be used for any information not derivable from the provided source files (e.g., exact Spring Boot patch version, full `.env.example` contents).

---

## Quality Standards

- **Accuracy gate:** Every version number appearing in updated documentation must match either `AGENTS.md`, `package.json`, or a `pom.xml` value present in the provided source. Zero unverified version strings permitted at merge.
- **Completeness check:** The README environment variable tables must cover 100% of variables defined in `.env.example` (both services). Any variable present in source config but absent from the table is a documentation defect.
- **Review requirement:** All documentation changes require at least one peer review confirming that each changed fact is traceable to a source file in the repository.
- **No broken commands:** Every shell command block in the README must be manually verified to execute without error against the described stack before the PR is merged.
- **Diff scope:** PRs touching only documentation files; any accidental source-code change causes automatic rejection.

---

## Decision Log

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| ADR-001 | `AGENTS.md` stack table is the canonical version reference | `AGENTS.md` is explicitly designated the authoritative stack document; `README.md` is the consumer-facing surface that must be kept in sync with it | Accepted |
| ADR-002 | `README.md` payment-service stack entry must be corrected from `Java 17 · Spring Boot 3.2` to `Java 21 · Spring Boot 3.x` | Direct conflict between `README.md` service table and `AGENTS.md` stack table; Java 21 LTS is the deployed runtime per `AGENTS.md` | Accepted |
| ADR-003 | In-memory repository adapters are documented as dev/test-only | `InMemoryPaymentRepository` and `InMemoryUserRepository` source code explicitly state they are not for production; README must not imply otherwise | Accepted |
| ADR-004 | PayPal and Stripe gateway adapters are documented as stub/partial implementations | Source code contains explicit `TODO` markers and stub return values; documentation must reflect integration status honestly | Accepted |
| ADR-005 | Exact Spring Boot patch version left as TODO pending `pom.xml` review | Full `pom.xml` was not provided in source context; pinning a specific patch version without verification would violate the no-invented-content rule | Proposed |