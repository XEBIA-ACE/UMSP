## Authoritative Upgrade Scope
1. Upgrade Java runtime from 11 to 17 LTS (prerequisite for Spring Boot 3.x)
2. Update Docker base image from adoptopenjdk/openjdk11-openj9:alpine to eclipse-temurin:17-jre-alpine
3. Update Maven compiler source/target from 11 to 17 in all pom.xml modules
4. Upgrade spring-boot-starter-parent 2.5.12 → 3.3.x (transitively upgrades Spring Framework 5.3→6.1, Spring Security 5.5→6.3, Hibernate 5.4→6.5, Spring MVC 5.3→6.1)
5. Run OpenRewrite javax-to-jakarta namespace migration recipe across all source modules (sm-core, sm-shop, sm-shop-model, sm-core-model, sm-core-modules)
6. Replace io.springfox:springfox-swagger2 2.9.2 with org.springdoc:springdoc-openapi-starter-webmvc-ui 2.5.0
7. Upgrade io.jsonwebtoken:jjwt 0.8.0 → io.jsonwebtoken:jjwt-api 0.12.6 + jjwt-impl + jjwt-jackson (breaking API migration)
8. Upgrade commons-fileupload:commons-fileupload 1.3.3 → 1.5 (fixes CVE-2023-24998)
9. Upgrade commons-io:commons-io 2.7 → 2.15.1 (fixes CVE-2021-29425)
10. Upgrade com.google.guava:guava 27.1-jre → 33.2.1-jre (fixes CVE-2023-2976)
11. Upgrade org.apache.httpcomponents:httpclient 4.5.2 → 4.5.14 (fixes CVE-2020-13956)
12. Upgrade commons-validator:commons-validator 1.5.1 → 1.8.0
13. Upgrade org.apache.commons:commons-collections4 4.1 → 4.4
14. Upgrade org.apache.commons:commons-lang3 3.5 → 3.14.0
15. Upgrade org.owasp.antisamy:antisamy 1.6.7 → 1.7.5
16. Upgrade org.mapstruct:mapstruct 1.3.0.Final → 1.6.2 (Java 17 annotation processor compatibility)
17. Remove pinned elasticsearch 7.5.2 property; validate OpenSearch client dependency is correctly declared
18. Add OWASP Dependency-Check Maven plugin to CircleCI pipeline
19. Restrict Spring Boot Actuator endpoints to management port with authentication
20. Add Dockerfile HEALTHCHECK instruction
21. Remove H2 database file from Docker image build context
22. Raise JaCoCo line coverage threshold for sm-core and sm-shop to 20%

- Blockers: javax-to-jakarta namespace migration touches every module; requires thorough regression testing given near-zero coverage in sm-core (0%) and sm-shop (4%), JJWT 0.8.0 → 0.12.x is a breaking API change requiring code changes in JWT generation and parsing logic, Springfox → springdoc-openapi migration requires replacing all @ApiOperation/@Api annotations with OpenAPI 3 equivalents, Hibernate 5→6 introduces breaking changes in HQL, criteria API, and type mappings; custom queries must be audited, Drools 7.32.0.Final compatibility with Spring Boot 3.x / Jakarta EE must be verified before upgrade; Drools 8.x is the Jakarta-compatible line, Infinispan 9.4.18.Final is not compatible with Spring Boot 3.x; must be upgraded or replaced (see aggressive option for full replacement), Spring Security 6.x removes several deprecated APIs used in 5.x; security configuration classes must be rewritten, Low test coverage increases regression risk; recommend writing integration tests for critical paths before migration
- Impacted areas: source code, CI/CD, infrastructure, tests, docs

---

# Migration Plan: Shopizer Spring Boot 3.3 Migration & Full Dependency Refresh

## Preconditions

Before any phase begins:
1. Code Insights index confirmed: repo `afe6da7b-f274-4d6c-be69-db56bcdd26a8`, ref `3.2.7`, commit `6a4a0a65a3408ee8f62597b51d1b3aac24b77dee`, 17,804 nodes, 10,959 edges, 1,210 Java files. [Q-01, Q-02] _(Unverified: no Code Insights evidence ID supplied.)_
2. A feature branch `feature/sb3-migration` is created from `3.2.7`. _(Unverified: no Code Insights evidence ID supplied.)_
3. All team members have Java 17 JDK installed locally.
4. CircleCI pipeline is green on the base branch.
5. The OWASP Dependency-Check Maven plugin is added to the root `pom.xml` and CI before any dependency change is merged (Phase 0). _(Unverified: no Code Insights evidence ID supplied.)_

---

## Strategy

The migration is sequenced into **seven dependency-ordered phases** to ensure each phase can be compiled, tested, and rolled back independently. The critical path is:

```
Phase 0 (CI hardening)
  → Phase 1 (Java 17 + Docker + MapStruct)
    → Phase 2 (CVE dependency refresh — no API breaks)
      → Phase 3 (Drools + Infinispan spike + pre-migration tests)
        → Phase 4 (Spring Boot 3.3.6 + javax→jakarta + Security 6 + Hibernate 6)
          → Phase 5 (JJWT 0.12.6 + Springfox→springdoc)
            → Phase 6 (Coverage gates + final hardening)
```

Phases 0–2 are low-risk and can be merged quickly. Phase 3 is the critical blocker gate. Phase 4 is the highest-risk phase and must not begin until Phase 3 is complete and integration tests are in place.

---

## Phase 0 — CI Hardening & Baseline (Est. 2 person-days)

**Goal:** Establish security scanning and coverage baselines before any dependency changes.

### Changes
1. Add `org.owasp:dependency-check-maven` plugin to root `pom.xml` with CVSS threshold 7.0 (HIGH). _(Unverified: no Code Insights evidence ID supplied.)_
2. Add OWASP Dependency-Check step to `.circleci/config.yml`. _(Unverified: no Code Insights evidence ID supplied.)_
3. Record current JaCoCo coverage baselines for `sm-core` (0 %) and `sm-shop` (4 %) — do NOT raise thresholds yet. _(Unverified: no Code Insights evidence ID supplied.)_
4. Verify CircleCI pipeline passes with new plugin.

### Affected Files
- `pom.xml` (root) _(Unverified: no Code Insights evidence ID supplied.)_
- `.circleci/config.yml` _(Unverified: no Code Insights evidence ID supplied.)_

### Acceptance Criteria
- OWASP report generated on every CI build.
- Existing tests continue to pass.

---

## Phase 1 — Java 17 Runtime, Docker, MapStruct (Est. 3 person-days)

**Goal:** Raise the Java runtime and toolchain to 17 LTS without touching Spring Boot or application code.

### Changes
1. Update `Dockerfile`: change `FROM adoptopenjdk/openjdk11-openj9:alpine` to `FROM eclipse-temurin:17-jre-alpine`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Add `HEALTHCHECK` instruction to `Dockerfile`. _(Unverified: no Code Insights evidence ID supplied.)_
3. Remove `SALESMANAGER.h2.db` from Docker image build context (add to `.dockerignore` or remove `COPY` instruction). _(Unverified: no Code Insights evidence ID supplied.)_
4. Update Maven compiler `source` and `target` properties from `11` to `17` in all five `pom.xml` files. _(Unverified: no Code Insights evidence ID supplied.)_
5. Update Maven compiler plugin version to `3.13.0` in root `pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
6. Upgrade `org.mapstruct:mapstruct` from `1.3.0.Final` to `1.6.2` in the relevant `pom.xml` (required before Java 17 annotation processing). _(Unverified: no Code Insights evidence ID supplied.)_
7. Update `mapstruct-processor` version to `1.6.2` in annotation processor configuration. _(Unverified: no Code Insights evidence ID supplied.)_

### Affected Files
- `Dockerfile` _(Unverified: no Code Insights evidence ID supplied.)_
- `.dockerignore` (create or update) _(Unverified: no Code Insights evidence ID supplied.)_
- `pom.xml` (root) — compiler plugin version, MapStruct version _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/pom.xml` — compiler source/target _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/pom.xml` — compiler source/target, MapStruct _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop-model/pom.xml` — compiler source/target _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-model/pom.xml` — compiler source/target _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-modules/pom.xml` — compiler source/target _(Unverified: no Code Insights evidence ID supplied.)_

### Affected Symbols
- `ReadableProductMapper` (sm-shop, lines 65–691) — MapStruct annotation processor [Q-12] _(Unverified: no Code Insights evidence ID supplied.)_
- `PersistableProductDefinitionMapper` (sm-shop) — MapStruct annotation processor [Q-13] _(Unverified: no Code Insights evidence ID supplied.)_

### Acceptance Criteria
- `mvn clean package -DskipTests` succeeds with Java 17. _(Unverified: no Code Insights evidence ID supplied.)_
- Docker image builds and starts.
- HEALTHCHECK passes.
- H2 file absent from image.

---

## Phase 2 — CVE Dependency Refresh (No API Breaks) (Est. 3 person-days)

**Goal:** Eliminate all critical and high CVEs that do not require API-level code changes.

### Dependency Changes (all in root `pom.xml` or relevant module `pom.xml`) _(Unverified: no Code Insights evidence ID supplied.)_

| Dependency | From | To | CVE Fixed |
|-----------|------|----|-----------|
| commons-fileupload:commons-fileupload | 1.3.3 | 1.5 | CVE-2023-24998, CVE-2016-1000031 |
| commons-io:commons-io | 2.7 | 2.15.1 | CVE-2021-29425 |
| com.google.guava:guava | 27.1-jre | 33.2.1-jre | CVE-2023-2976 |
| org.apache.httpcomponents:httpclient | 4.5.2 | 4.5.14 | CVE-2020-13956 |
| commons-validator:commons-validator | 1.5.1 | 1.8.0 | — |
| org.apache.commons:commons-collections4 | 4.1 | 4.4 | — |
| org.apache.commons:commons-lang3 | 3.5 | 3.14.0 | — |
| org.owasp.antisamy:antisamy | 1.6.7 | 1.7.5 | — |
| elasticsearch version property | 7.5.2 | Remove property | EOL |

### Affected Files
- `pom.xml` (root) — dependency management section _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/pom.xml`, `sm-shop/pom.xml` — direct dependency declarations _(Unverified: no Code Insights evidence ID supplied.)_

### Acceptance Criteria
- OWASP Dependency-Check reports no CRITICAL or HIGH CVEs for upgraded dependencies.
- All existing tests pass.
- `mvn dependency:tree` shows no `io.springfox` or `elasticsearch:7.5.2` artifacts. _(Unverified: no Code Insights evidence ID supplied.)_

---

## Phase 3 — Compatibility Spikes & Pre-Migration Integration Tests (Est. 8 person-days)

**Goal:** Resolve the two unverified blockers (Drools, Infinispan) and write integration tests for critical paths before the high-risk namespace migration.

### 3a — Drools Compatibility Spike
- Determine whether Drools 7.32.0.Final can run under Spring Boot 3.x / Jakarta EE (unlikely) or whether upgrade to Drools 8.x is required.
- Affected classes: `DroolsBeanFactory` (sm-core, lines 24–112), `PromoCodeCalculatorModule`, `ShippingDecisionPreProcessorImpl`, `CustomShippingQuoteRules`. [Q-08, Q-09] _(Unverified: no Code Insights evidence ID supplied.)_
- Decision gate: if Drools 8.x upgrade is required, estimate additional effort and escalate before proceeding.

### 3b — Infinispan Compatibility Spike
- Determine whether Infinispan 9.4.18.Final can be upgraded to 14+ or must be replaced.
- Affected classes: `CmsStaticContentFileManagerImpl` (infinispan package), `CmsImageFileManagerImpl` (infinispan package). [Q-14] _(Unverified: no Code Insights evidence ID supplied.)_
- Decision gate: if replacement is required, estimate additional effort and escalate.

### 3c — Pre-Migration Integration Tests
Write integration tests covering the following critical paths before the namespace migration:
- Admin authentication: `POST /api/v1/auth/login` → JWT token issuance via `AuthenticateUserApi` → `JWTAdminAuthenticationManager` → `JWTTokenUtil` [Q-06, Q-07] _(Unverified: no Code Insights evidence ID supplied.)_
- Customer authentication: `POST /api/v1/customer/login` → `AuthenticateCustomerApi` → `JWTCustomerAuthenticationManager` → `JWTTokenUtil` _(Unverified: no Code Insights evidence ID supplied.)_
- Product catalog read: `GET /api/v1/products/{id}` → `ReadableProductMapper` (fan-out 20) [Q-12] _(Unverified: no Code Insights evidence ID supplied.)_
- Order processing: `OrderFacadeImpl.processOrder` (fan-out 22) [Q-13] _(Unverified: no Code Insights evidence ID supplied.)_
- Category management: extend `CategoryManagementAPIIntegrationTest` (already exists in sm-shop/test) [Q-03] _(Unverified: no Code Insights evidence ID supplied.)_

### Affected Files
- `sm-shop/src/test/java/com/salesmanager/test/shop/integration/` — new test classes _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/test/java/com/salesmanager/test/` — new test classes _(Unverified: no Code Insights evidence ID supplied.)_

### Acceptance Criteria
- Drools and Infinispan compatibility decisions documented.
- JaCoCo line coverage for `sm-core` ≥ 10 % (interim gate before final 20 % target). _(Unverified: no Code Insights evidence ID supplied.)_
- JaCoCo line coverage for `sm-shop` ≥ 10 % (interim gate). _(Unverified: no Code Insights evidence ID supplied.)_
- All new tests pass on the current (pre-migration) codebase.

---

## Phase 4 — Spring Boot 3.3.6 + javax→jakarta + Security 6 + Hibernate 6 (Est. 12 person-days)

**Goal:** The core migration. This is the highest-risk phase.

### 4a — Spring Boot Parent Upgrade
- Change `spring-boot-starter-parent` from `2.5.12` to `3.3.6` in root `pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
- This transitively upgrades: Spring Framework 5.3→6.1, Spring Security 5.5→6.3, Hibernate 5.4→6.5, Spring MVC 5.3→6.1.

### 4b — javax→jakarta Namespace Migration
- Run OpenRewrite recipe `org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_3` across all five modules. _(Unverified: no Code Insights evidence ID supplied.)_
- Verify no `import javax.` remains (except intentionally retained `javax.mail`, `javax.xml` if applicable). [AC-12] _(Unverified: no Code Insights evidence ID supplied.)_
- Affected: all 1,210 Java files across `sm-core`, `sm-shop`, `sm-shop-model`, `sm-core-model`, `sm-core-modules`. _(Unverified: no Code Insights evidence ID supplied.)_

### 4c — Spring Security 6 Rewrite
- Rewrite `MultipleEntryPointsSecurityConfig.java` from `WebSecurityConfigurerAdapter` pattern to `SecurityFilterChain` bean model. _(Unverified: no Code Insights evidence ID supplied.)_
- Update `AuthenticationTokenFilter.java`, `JWTAdminAuthenticationProvider.java`, `JWTCustomerAuthenticationProvider.java`, `ServicesAuthenticationSuccessHandler.java`, `UserAuthenticationSuccessHandler.java`. [Q-10] _(Unverified: no Code Insights evidence ID supplied.)_
- Restrict Actuator endpoints to management port with authentication in `application.properties`/`application.yml`. _(Unverified: no Code Insights evidence ID supplied.)_

### 4d — Hibernate 6 Query Audit
- Audit all JPQL/HQL in `CategoryServiceImpl`, `OrderServiceImpl`, `ProductServiceImpl`, `ShippingServiceImpl`, `PaymentServiceImpl`. [Q-14] _(Unverified: no Code Insights evidence ID supplied.)_
- Update any deprecated `Session.createCriteria()` calls to JPA Criteria API. _(Unverified: no Code Insights evidence ID supplied.)_
- Verify `AuditSection` (fan-in 31) and `Transaction` (fan-in 22) JPA annotations are correct under Hibernate 6. [Q-03] _(Unverified: no Code Insights evidence ID supplied.)_

### 4e — Drools/Infinispan Migration (outcome of Phase 3 spike)
- Apply the upgrade or replacement strategy determined in Phase 3.

### Affected Files
- `pom.xml` (root) — parent version _(Unverified: no Code Insights evidence ID supplied.)_
- All Java source files in all five modules — namespace migration
- `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/AuthenticationTokenFilter.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/admin/JWTAdminAuthenticationProvider.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/customer/JWTCustomerAuthenticationProvider.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/ServicesAuthenticationSuccessHandler.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/admin/security/UserAuthenticationSuccessHandler.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/configuration/DroolsBeanFactory.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/cms/content/infinispan/CmsStaticContentFileManagerImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/cms/product/infinispan/CmsImageFileManagerImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/category/CategoryServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/shipping/ShippingServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/payments/PaymentServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-model/src/main/java/com/salesmanager/core/model/common/audit/AuditSection.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-model/src/main/java/com/salesmanager/core/model/payments/Transaction.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `src/main/resources/application.properties` or `application.yml` — Actuator management port config _(Unverified: no Code Insights evidence ID supplied.)_

### Acceptance Criteria
- `mvn clean package` succeeds. _(Unverified: no Code Insights evidence ID supplied.)_
- All pre-migration integration tests pass.
- No `import javax.` in source (AC-12). _(Unverified: no Code Insights evidence ID supplied.)_
- Spring context loads without errors.
- Admin and customer authentication endpoints return valid tokens (AC-6, AC-7).
- Actuator health on management port only (AC-9).

---

## Phase 5 — JJWT 0.12.6 + Springfox→springdoc (Est. 5 person-days)

**Goal:** Replace the two abandoned/CVE-bearing API-breaking libraries.

### 5a — JJWT Migration
- Remove `io.jsonwebtoken:jjwt:0.8.0` from `pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
- Add `io.jsonwebtoken:jjwt-api:0.12.6`, `io.jsonwebtoken:jjwt-impl:0.12.6` (runtime), `io.jsonwebtoken:jjwt-jackson:0.12.6` (runtime). _(Unverified: no Code Insights evidence ID supplied.)_
- Rewrite `JWTTokenUtil.java` (lines 26–193): replace `Jwts.builder()...signWith(SignatureAlgorithm.HS512, secret)` with `Jwts.builder()...signWith(key)` pattern; replace `Jwts.parser().setSigningKey(secret)` with `Jwts.parser().verifyWith(key).build()`. [Q-07] _(Unverified: no Code Insights evidence ID supplied.)_
- Update `AuthenticationTokenFilter.java`, `JWTAdminAuthenticationManager.java`, `JWTCustomerAuthenticationManager.java`. [Q-06] _(Unverified: no Code Insights evidence ID supplied.)_
- Validate token round-trip in integration tests.

### 5b — Springfox→springdoc Migration
- Remove `io.springfox:springfox-swagger2:2.9.2` and `io.springfox:springfox-swagger-ui` from `pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
- Add `org.springdoc:springdoc-openapi-starter-webmvc-ui:2.5.0`. _(Unverified: no Code Insights evidence ID supplied.)_
- Remove Springfox `@EnableSwagger2` and `Docket` bean from `ShopApplicationConfiguration.java`. _(Unverified: no Code Insights evidence ID supplied.)_
- Replace all `@Api` → `@Tag`, `@ApiOperation` → `@Operation`, `@ApiParam` → `@Parameter`, `@ApiResponse` → `@ApiResponse` (io.swagger.v3) across all controller classes in `sm-shop`. _(Unverified: no Code Insights evidence ID supplied.)_
- Configure springdoc properties in `application.properties`. _(Unverified: no Code Insights evidence ID supplied.)_

### Affected Files
- `pom.xml` (root or sm-shop/pom.xml) — JJWT and springdoc dependency changes _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/JWTTokenUtil.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/AuthenticationTokenFilter.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/admin/JWTAdminAuthenticationManager.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/customer/JWTCustomerAuthenticationManager.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/application/config/ShopApplicationConfiguration.java` _(Unverified: no Code Insights evidence ID supplied.)_
- All `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**/*.java` — Springfox annotation replacement _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/resources/application.properties` — springdoc config _(Unverified: no Code Insights evidence ID supplied.)_

### Acceptance Criteria
- `mvn dependency:tree` shows no `io.springfox` or `io.jsonwebtoken:jjwt:0.8.0` artifacts (AC-13, AC-14). _(Unverified: no Code Insights evidence ID supplied.)_
- Admin and customer login return valid JWT tokens (AC-6, AC-7).
- OpenAPI UI accessible at `/swagger-ui.html` (AC-8). _(Unverified: no Code Insights evidence ID supplied.)_
- OWASP report shows no CRITICAL/HIGH CVEs (AC-5).

---

## Phase 6 — Coverage Gates & Final Hardening (Est. 2 person-days)

**Goal:** Raise JaCoCo thresholds to the committed targets and verify all quality gates.

### Changes
1. Raise JaCoCo line coverage threshold for `sm-core` to 20 % in `sm-core/pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Raise JaCoCo line coverage threshold for `sm-shop` to 20 % in `sm-shop/pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
3. Write any additional tests needed to meet the 20 % threshold.
4. Run full regression suite.
5. Generate final OWASP Dependency-Check report.
6. Update `README.md` and API documentation to reflect Spring Boot 3.3.6, Java 17, and springdoc-openapi. _(Unverified: no Code Insights evidence ID supplied.)_

### Affected Files
- `sm-core/pom.xml` — JaCoCo threshold _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/pom.xml` — JaCoCo threshold _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/test/` — additional tests if needed _(Unverified: no Code Insights evidence ID supplied.)_
- `README.md` _(Unverified: no Code Insights evidence ID supplied.)_

### Acceptance Criteria
- All 14 acceptance criteria (AC-1 through AC-14) pass.
- CircleCI pipeline green on `feature/sb3-migration` branch. _(Unverified: no Code Insights evidence ID supplied.)_

---

## Rollback Strategy

Each phase is merged as a separate PR. Rollback is achieved by reverting the PR for that phase. Phases 0–2 are independently revertible. Phase 4 (the namespace migration) is the most difficult to roll back; the pre-migration integration tests in Phase 3 are the primary safety net.

For Phase 4, a rollback tag `pre-sb3-migration` should be created on the branch before Phase 4 begins. _(Unverified: no Code Insights evidence ID supplied.)_

---

## Monitoring After Deployment

- Monitor application startup logs for `BeanCreationException` or `NoSuchBeanDefinitionException`. _(Unverified: no Code Insights evidence ID supplied.)_
- Monitor JWT authentication error rates in application logs.
- Monitor Actuator `/actuator/health` on management port. _(Unverified: no Code Insights evidence ID supplied.)_
- Run OWASP Dependency-Check on every subsequent dependency change.
- Review JaCoCo coverage trend in CI after each merge.