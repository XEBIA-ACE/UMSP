## Authoritative Modernization Decision
- Selected option: Spring Boot 3.3 Migration & Full Dependency Refresh (`moderate`)
- Effort: 35 person-days
- Risk score: 6/10
- Blockers: javax-to-jakarta namespace migration touches every module; requires thorough regression testing given near-zero coverage in sm-core (0%) and sm-shop (4%), JJWT 0.8.0 → 0.12.x is a breaking API change requiring code changes in JWT generation and parsing logic, Springfox → springdoc-openapi migration requires replacing all @ApiOperation/@Api annotations with OpenAPI 3 equivalents, Hibernate 5→6 introduces breaking changes in HQL, criteria API, and type mappings; custom queries must be audited, Drools 7.32.0.Final compatibility with Spring Boot 3.x / Jakarta EE must be verified before upgrade; Drools 8.x is the Jakarta-compatible line, Infinispan 9.4.18.Final is not compatible with Spring Boot 3.x; must be upgraded or replaced (see aggressive option for full replacement), Spring Security 6.x removes several deprecated APIs used in 5.x; security configuration classes must be rewritten, Low test coverage increases regression risk; recommend writing integration tests for critical paths before migration
- Impacted areas: source code, CI/CD, infrastructure, tests, docs

---

# Constitution: Shopizer Spring Boot 3.3 Migration & Full Dependency Refresh

## 1. Objective

Migrate the Shopizer headless commerce platform (ref `3.2.7`, commit `6a4a0a65a3408ee8f62597b51d1b3aac24b77dee`) from Spring Boot 2.5.12 / Java 11 to Spring Boot 3.3.x / Java 17 LTS, perform the mandatory `javax`→`jakarta` namespace migration across all five Maven modules, replace all abandoned and CVE-bearing dependencies, and establish a supported, patchable, security-hardened baseline. The selected upgrade option is **"Spring Boot 3.3 Migration & Full Dependency Refresh" (moderate)**. _(Unverified: no Code Insights evidence ID supplied.)_

---

## 2. Guiding Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| P-1 | **Evidence-first** | Every architectural claim must be grounded in a Code Insights tool result or an upstream-verified compatibility document. Inferred or assumed facts must be labelled as such. |
| P-2 | **No silent regressions** | All existing passing tests must continue to pass after each phase. New integration tests must be written for critical paths before the namespace migration is applied. |
| P-3 | **Smallest safe increment** | Changes are sequenced so that each phase can be compiled, tested, and rolled back independently. No phase bundles more than one breaking change category. |
| P-4 | **Security first** | CVE-bearing dependencies are upgraded before non-security improvements. OWASP Dependency-Check is added to CI before the first dependency change is merged. |
| P-5 | **Preserve public API contracts** | REST endpoint paths, request/response shapes, and JWT token format must remain backward-compatible unless a breaking change is explicitly documented and communicated. |
| P-6 | **Traceability** | Every task references the research query IDs that justify it. Every spec claim cites a query ID or an upstream-verified compatibility document. |
| P-7 | **Blocker-aware sequencing** | The eight known blockers (javax→jakarta coverage gap, JJWT API break, Springfox removal, Hibernate 6 HQL changes, Drools Jakarta compatibility, Infinispan incompatibility, Spring Security 6 API removal, low test coverage) are resolved in dependency order before the components that depend on them are migrated. |

---

## 3. Constraints

| # | Constraint |
|---|-----------|
| C-1 | Java runtime target is **17 LTS** (not 21). Spring Boot 3.3.x requires ≥ 17; the selected target is 17. |
| C-2 | Spring Boot target is **3.3.6** (the selected target from the compatibility matrix). |
| C-3 | All five Maven modules (`sm-core`, `sm-shop`, `sm-shop-model`, `sm-core-model`, `sm-core-modules`) must be migrated together; partial migration is not acceptable. | _(Unverified: no Code Insights evidence ID supplied.)_
| C-4 | The Docker base image must be changed to `eclipse-temurin:17-jre-alpine`; AdoptOpenJDK images are deprecated and must not remain. | _(Unverified: no Code Insights evidence ID supplied.)_
| C-5 | Drools and Infinispan compatibility with Jakarta EE / Spring Boot 3.x is **unverified** (upstream evidence status: "unverified"). No target version is committed for either component until a compatibility spike is completed. |
| C-6 | The H2 database file (`SALESMANAGER.h2.db`) must be removed from the Docker image build context before the image is published. | _(Unverified: no Code Insights evidence ID supplied.)_
| C-7 | Spring Boot Actuator endpoints must be restricted to the management port with authentication before the migrated image is deployed to any shared environment. |
| C-8 | Effort budget is **35 person-days** as specified in the selected upgrade option. |

---

## 4. Measurable Quality Gates

| Gate | Metric | Pass Threshold | Applies To |
|------|--------|---------------|------------|
| QG-1 | JaCoCo line coverage — `sm-core` | ≥ 20 % | Post-migration CI | _(Unverified: no Code Insights evidence ID supplied.)_
| QG-2 | JaCoCo line coverage — `sm-shop` | ≥ 20 % | Post-migration CI | _(Unverified: no Code Insights evidence ID supplied.)_
| QG-3 | OWASP Dependency-Check CVSS threshold | No CRITICAL or HIGH CVEs unmitigated | Every CI build |
| QG-4 | All existing tests pass | 0 test failures | Every phase merge |
| QG-5 | Application starts successfully | Spring context loads without errors | Every phase merge |
| QG-6 | JWT authentication smoke test | Admin and customer login endpoints return valid tokens | Post-JJWT migration |
| QG-7 | OpenAPI UI accessible | `/swagger-ui.html` returns HTTP 200 | Post-springdoc migration | _(Unverified: no Code Insights evidence ID supplied.)_
| QG-8 | Actuator health endpoint | Returns HTTP 200 on management port only | Post-security hardening |
| QG-9 | Docker image builds and starts | Container starts, health check passes | Post-Dockerfile changes |

---

## 5. Decision Log

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| D-1 | Target Java 17, not 21 | Spring Boot 3.3.x requires ≥ 17; the selected upgrade option explicitly targets 17 LTS. Java 21 is a future upgrade. | At spec creation |
| D-2 | Target Spring Boot 3.3.6 | Explicitly stated in the verified compatibility matrix. | At spec creation |
| D-3 | Drools and Infinispan targets deferred | Upstream evidence status is "unverified"; no target version is known. A compatibility spike (T-05) must resolve this before the Spring Boot upgrade is applied. | At spec creation |
| D-4 | Replace Springfox with springdoc-openapi 2.5.0 | Springfox is abandoned and incompatible with Spring Boot 3.x. springdoc-openapi 2.x is the verified replacement. | At spec creation |
| D-5 | JJWT migrated to split artifact model (jjwt-api + jjwt-impl + jjwt-jackson) | JJWT 0.12.x changed from a single JAR to three coordinated artifacts. All three must be declared. | At spec creation |
| D-6 | OpenRewrite used for javax→jakarta migration | Reduces manual error rate across 1,210 Java files spanning five modules. | At spec creation |
| D-7 | Integration tests written before namespace migration | sm-core has 0 % and sm-shop has 4 % line coverage; regression risk is unacceptably high without pre-migration test coverage. | At spec creation |