## Authoritative Pipeline Facts
These facts are generated from Tech Analysis and the selected Upgrade Option and take precedence over narrative text.

### Current State
| Category | Component | Current value | Source |
| --- | --- | --- | --- |
| language | Java | 11 | Tech Analysis |
| runtime | JVM | 11 | Tech Analysis |
| build_tool | Build tool | Maven | Tech Analysis |
| package_manager | Package manager | Maven | Tech Analysis |
| framework | Spring Boot | 2.5.12 | Tech Analysis |
| framework | Spring Security | 5.5.x (transitive via Spring Boot 2.5.12) | Tech Analysis |
| framework | Spring MVC | 5.3.x (transitive via Spring Boot 2.5.12) | Tech Analysis |
| framework | Springfox Swagger2 | 2.9.2 | Tech Analysis |
| framework | Hibernate (via Spring Data JPA) | 5.4.x (transitive via Spring Boot 2.5.12) | Tech Analysis |
| framework | Drools | 7.32.0.Final | Tech Analysis |
| framework | Infinispan | 9.4.18.Final | Tech Analysis |
| framework | MapStruct | 1.3.0.Final | Tech Analysis |
| dependency | spring-boot-starter-parent | 2.5.12 | Tech Analysis |
| dependency | io.jsonwebtoken:jjwt | 0.8.0 | Tech Analysis |
| dependency | commons-fileupload:commons-fileupload | 1.3.3 | Tech Analysis |
| dependency | elasticsearch | 7.5.2 | Tech Analysis |
| dependency | com.google.guava:guava | 27.1-jre | Tech Analysis |
| dependency | org.apache.commons:commons-lang3 | 3.5 | Tech Analysis |
| dependency | commons-io:commons-io | 2.7 | Tech Analysis |
| dependency | org.apache.commons:commons-collections4 | 4.1 | Tech Analysis |
| dependency | commons-validator:commons-validator | 1.5.1 | Tech Analysis |
| dependency | org.apache.httpcomponents:httpclient | 4.5.2 | Tech Analysis |
| dependency | com.fasterxml.jackson.core:jackson-databind | 2.13.4.1 | Tech Analysis |
| dependency | org.infinispan:infinispan-core | 9.4.18.Final | Tech Analysis |
| dependency | io.springfox:springfox-swagger2 | 2.9.2 | Tech Analysis |
| dependency | org.owasp.antisamy:antisamy | 1.6.7 | Tech Analysis |
| dependency | adoptopenjdk/openjdk11-openj9:alpine (Docker base) | JDK 11 OpenJ9 | Tech Analysis |

### Target State
| Component | Current | Explicit target | Source |
| --- | --- | --- | --- |
| MapStruct | 1.3.0.Final | 1.6.2 | Selected Upgrade Option |
| io.jsonwebtoken:jjwt-api | 0.8.0 | 0.12.6 | Selected Upgrade Option |
| springdoc-openapi-starter-webmvc-ui | N/A (replacing springfox-swagger2 2.9.2) | 2.5.0 | Selected Upgrade Option |
| Hibernate ORM | 5.4.x | 6.5.x (managed by Spring Boot 3.3.x BOM) | Selected Upgrade Option |
| Spring Security | 5.5.x | 6.3.x (managed by Spring Boot 3.3.x BOM) | Selected Upgrade Option |
| Spring Framework | 5.3.x | 6.1.x (managed by Spring Boot 3.3.x BOM) | Selected Upgrade Option |
| spring-boot-starter-parent | 2.5.12 | 3.3.6 | Selected Upgrade Option |
| Maven compiler plugin | unknown | 3.13.0 | Selected Upgrade Option |
| Docker base image | adoptopenjdk/openjdk11-openj9:alpine | eclipse-temurin:17-jre-alpine | Selected Upgrade Option |
| Java Runtime | 11 | 17 | Selected Upgrade Option |
| Upgrade spring-boot-starter-parent | 2.5.12 | 3.3.x (transitively upgrades Spring Framework 5.3→6.1, Spring Security 5.5→6.3, Hibernate 5.4→6.5, Spring MVC 5.3→6.1) | Selected Upgrade Option |
| Upgrade io.jsonwebtoken:jjwt | 0.8.0 | io.jsonwebtoken:jjwt-api 0.12.6 + jjwt-impl + jjwt-jackson (breaking API migration) | Selected Upgrade Option |
| Upgrade commons-fileupload:commons-fileupload | 1.3.3 | 1.5 (fixes CVE-2023-24998) | Selected Upgrade Option |
| Upgrade commons-io:commons-io | 2.7 | 2.15.1 (fixes CVE-2021-29425) | Selected Upgrade Option |
| Upgrade com.google.guava:guava | 27.1-jre | 33.2.1-jre (fixes CVE-2023-2976) | Selected Upgrade Option |
| Upgrade org.apache.httpcomponents:httpclient | 4.5.2 | 4.5.14 (fixes CVE-2020-13956) | Selected Upgrade Option |
| Upgrade commons-validator:commons-validator | 1.5.1 | 1.8.0 | Selected Upgrade Option |
| Upgrade org.apache.commons:commons-collections4 | 4.1 | 4.4 | Selected Upgrade Option |
| Upgrade org.apache.commons:commons-lang3 | 3.5 | 3.14.0 | Selected Upgrade Option |
| Upgrade org.owasp.antisamy:antisamy | 1.6.7 | 1.7.5 | Selected Upgrade Option |
| Upgrade org.mapstruct:mapstruct | 1.3.0.Final | 1.6.2 (Java 17 annotation processor compatibility) | Selected Upgrade Option |

## Authoritative Modernization Decision
- Selected option: Spring Boot 3.3 Migration & Full Dependency Refresh (`moderate`)
- Effort: 35 person-days
- Risk score: 6/10
- Blockers: javax-to-jakarta namespace migration touches every module; requires thorough regression testing given near-zero coverage in sm-core (0%) and sm-shop (4%), JJWT 0.8.0 → 0.12.x is a breaking API change requiring code changes in JWT generation and parsing logic, Springfox → springdoc-openapi migration requires replacing all @ApiOperation/@Api annotations with OpenAPI 3 equivalents, Hibernate 5→6 introduces breaking changes in HQL, criteria API, and type mappings; custom queries must be audited, Drools 7.32.0.Final compatibility with Spring Boot 3.x / Jakarta EE must be verified before upgrade; Drools 8.x is the Jakarta-compatible line, Infinispan 9.4.18.Final is not compatible with Spring Boot 3.x; must be upgraded or replaced (see aggressive option for full replacement), Spring Security 6.x removes several deprecated APIs used in 5.x; security configuration classes must be rewritten, Low test coverage increases regression risk; recommend writing integration tests for critical paths before migration
- Impacted areas: source code, CI/CD, infrastructure, tests, docs

### Open Questions
- Verify the target requirement for Java; current value `11` is intentionally omitted from Target State.
- Verify the target requirement for JVM; current value `11` is intentionally omitted from Target State.
- Verify the target requirement for Build tool; current value `Maven` is intentionally omitted from Target State.
- Verify the target requirement for Package manager; current value `Maven` is intentionally omitted from Target State.
- Select and verify an exact supported target for Hibernate ORM; the selected option specifies `6.5.x (managed by Spring Boot 3.3.x BOM)`.
- Select and verify an exact supported target for Spring Security; the selected option specifies `6.3.x (managed by Spring Boot 3.3.x BOM)`.
- Select and verify an exact supported target for Spring Framework; the selected option specifies `6.1.x (managed by Spring Boot 3.3.x BOM)`.
- Select and verify an exact supported target for Upgrade spring-boot-starter-parent; the selected option specifies `3.3.x (transitively upgrades Spring Framework 5.3→6.1, Spring Security 5.5→6.3, Hibernate 5.4→6.5, Spring MVC 5.3→6.1)`.

---

# Specification: Shopizer Spring Boot 3.3 Migration & Full Dependency Refresh

## 1. Summary

Migrate the Shopizer headless commerce platform from Spring Boot 2.5.12 / Java 11 to Spring Boot 3.3.6 / Java 17 LTS. The migration encompasses the mandatory `javax`→`jakarta` namespace migration across all five Maven modules, replacement of the abandoned Springfox Swagger2 library with springdoc-openapi 2.5.0, a breaking JJWT API upgrade from 0.8.0 to 0.12.6, and a full refresh of all CVE-bearing dependencies. Infrastructure hardening (Docker base image, Actuator security, HEALTHCHECK, H2 file removal) and CI improvements (OWASP Dependency-Check, JaCoCo threshold raise) are included in scope. _(Unverified: no Code Insights evidence ID supplied.)_

**Selected option:** Spring Boot 3.3 Migration & Full Dependency Refresh (moderate)  
**Effort:** 35 person-days  
**Risk score:** 6/10  
**Upgrade urgency:** Critical

---

## 2. Motivation

- Spring Boot 2.5.12 reached end-of-life in May 2023 and no longer receives security patches. [Q-01]
- Multiple critical and high CVEs are present in the dependency tree: JJWT 0.8.0 (CVE-2022-45688), commons-fileupload 1.3.3 (CVE-2023-24998, CVE-2016-1000031), commons-io 2.7 (CVE-2021-29425), Guava 27.1-jre (CVE-2023-2976), Infinispan 9.4.18.Final (EOL, multiple CVEs), httpclient 4.5.2 (CVE-2020-13956). [Upstream Tech Analysis]
- Springfox Swagger2 2.9.2 is abandoned and incompatible with Spring Boot 3.x. [Upstream Tech Analysis]
- The H2 database file is copied into the Docker image, creating a data-exposure risk. [Upstream Tech Analysis]
- Spring Boot Actuator endpoints show no evidence of restriction configuration. [Upstream Tech Analysis]
- Test coverage in `sm-core` is 0 % and in `sm-shop` is 4 % line coverage, compounding migration risk. [Upstream Tech Analysis] _(Unverified: no Code Insights evidence ID supplied.)_

---

## 3. Repository Evidence

| Evidence | Finding | Query ID |
|----------|---------|----------|
| Repo identity | `https://github.com/shopizer-ecommerce/shopizer`, ref `3.2.7`, commit `6a4a0a65a3408ee8f62597b51d1b3aac24b77dee` | Q-01 | _(Unverified: no Code Insights evidence ID supplied.)_
| Index status | 1 job, state `succeeded`; 17,804 nodes, 10,959 edges, 1,210 Java files, 4 manifests | Q-02 | _(Unverified: no Code Insights evidence ID supplied.)_
| Module structure | 5 modules: `sm-core` (358 elements), `sm-shop` (326), `sm-shop-model` (323), `sm-core-model` (187), `sm-core-modules` (15) | Q-03 | _(Unverified: no Code Insights evidence ID supplied.)_
| Application entry point | `sm-shop/src/main/java/com/salesmanager/shop/application/ShopApplication.java` | Q-03 | _(Unverified: no Code Insights evidence ID supplied.)_
| JWT implementation | `JWTTokenUtil` (sm-shop, lines 26–193), `JWTAdminAuthenticationManager`, `JWTCustomerAuthenticationManager`, `AuthenticationTokenFilter`, `AuthenticateUserApi`, `AuthenticateCustomerApi` | Q-06, Q-07 | _(Unverified: no Code Insights evidence ID supplied.)_
| Security configuration | `MultipleEntryPointsSecurityConfig.java` — blast radius touches `AuthenticationTokenFilter`, `CredentialsServiceImpl`, `JWTAdminAuthenticationProvider`, `JWTCustomerAuthenticationProvider`, `ServicesAuthenticationSuccessHandler`, `UserAuthenticationSuccessHandler` | Q-10 | _(Unverified: no Code Insights evidence ID supplied.)_
| Drools usage | `DroolsBeanFactory` (sm-core, lines 24–112), used by `PromoCodeCalculatorModule`, `ShippingDecisionPreProcessorImpl`, `CustomShippingQuoteRules` | Q-08, Q-09 | _(Unverified: no Code Insights evidence ID supplied.)_
| Infinispan usage | `CmsStaticContentFileManagerImpl` (infinispan package), `CmsImageFileManagerImpl` (infinispan package) — confirmed by module dependency graph | Q-14 | _(Unverified: no Code Insights evidence ID supplied.)_
| Mapper complexity | `ReadableProductMapper` (sm-shop, lines 65–691, fan-out 20), `PersistableProductDefinitionMapper` (fan-out 16), `OrderFacadeImpl` (lines 113–1648, fan-out 22) | Q-12, Q-13 | _(Unverified: no Code Insights evidence ID supplied.)_
| Test infrastructure | `CategoryManagementAPIIntegrationTest` (sm-shop/test), `ShoppingCartTest`, `OrderTest`, `ProductTest` (sm-core/test) — 37 test modules total | Q-03 | _(Unverified: no Code Insights evidence ID supplied.)_
| Dead code | No dead code candidates found at confidence ≥ 0.9 | Q-11 |
| Hotspots | `ServiceRuntimeException` (fan-in 215), `ServiceException` (fan-in 153), `ResourceNotFoundException` (fan-in 135) — all in exception layer | Q-03 | _(Unverified: no Code Insights evidence ID supplied.)_
| Dependency manifests | `pom.xml`, `sm-core-model/pom.xml`, `sm-core/pom.xml`, `sm-shop/pom.xml` confirmed by index job stats (4 manifests) | Q-02 | _(Unverified: no Code Insights evidence ID supplied.)_

---

## 4. Current State

| Component | Current Version | Status |
|-----------|----------------|--------|
| Java Runtime | 11 | EOL for Spring Boot 3.x |
| Docker base image | `adoptopenjdk/openjdk11-openj9:alpine` | Deprecated | _(Unverified: no Code Insights evidence ID supplied.)_
| Maven compiler source/target | 11 | Incompatible with Spring Boot 3.x |
| spring-boot-starter-parent | 2.5.12 | EOL |
| Spring Framework | 5.3.x (transitive) | EOL |
| Spring Security | 5.5.x (transitive) | EOL |
| Spring MVC | 5.3.x (transitive) | EOL |
| Hibernate ORM | 5.4.x (transitive) | EOL |
| Springfox Swagger2 | 2.9.2 | Abandoned; incompatible with Spring Boot 3.x |
| io.jsonwebtoken:jjwt | 0.8.0 | CVE-2022-45688; critically outdated |
| commons-fileupload | 1.3.3 | CVE-2023-24998, CVE-2016-1000031 |
| commons-io | 2.7 | CVE-2021-29425 |
| com.google.guava:guava | 27.1-jre | CVE-2023-2976 |
| org.apache.httpcomponents:httpclient | 4.5.2 | CVE-2020-13956 |
| commons-validator | 1.5.1 | Outdated |
| commons-collections4 | 4.1 | Outdated |
| commons-lang3 | 3.5 | Outdated |
| org.owasp.antisamy:antisamy | 1.6.7 | Outdated |
| org.mapstruct:mapstruct | 1.3.0.Final | Incompatible with Java 17 annotation processor |
| Drools | 7.32.0.Final | Jakarta EE compatibility unverified |
| Infinispan | 9.4.18.Final | EOL; Jakarta EE incompatible |
| elasticsearch property | 7.5.2 (pinned) | EOL; project uses OpenSearch client |
| JaCoCo threshold sm-core | 0 % | Below target |
| JaCoCo threshold sm-shop | 4 % | Below target |
| OWASP Dependency-Check | Not present in CI | Missing |
| Actuator endpoint restriction | Not configured | Security gap |
| Dockerfile HEALTHCHECK | Not present | Missing |
| H2 file in Docker image | Present | Data exposure risk |

---

## 5. Target State

| Component | Target Version | Source |
|-----------|---------------|--------|
| Java Runtime | 17 LTS | Verified compatibility matrix |
| Docker base image | `eclipse-temurin:17-jre-alpine` | Verified compatibility matrix | _(Unverified: no Code Insights evidence ID supplied.)_
| Maven compiler source/target | 17 | Selected upgrade option |
| Maven compiler plugin | 3.13.0 | Verified compatibility matrix |
| spring-boot-starter-parent | 3.3.6 | Verified compatibility matrix |
| Spring Framework | 6.1.x (BOM-managed) | Verified compatibility matrix |
| Spring Security | 6.3.x (BOM-managed) | Verified compatibility matrix |
| Spring MVC | 6.1.x (BOM-managed) | Verified compatibility matrix |
| Hibernate ORM | 6.5.x (BOM-managed) | Verified compatibility matrix |
| springdoc-openapi-starter-webmvc-ui | 2.5.0 | Verified compatibility matrix |
| io.jsonwebtoken:jjwt-api | 0.12.6 | Verified compatibility matrix |
| io.jsonwebtoken:jjwt-impl | 0.12.6 | Selected upgrade option |
| io.jsonwebtoken:jjwt-jackson | 0.12.6 | Selected upgrade option |
| commons-fileupload | 1.5 | Selected upgrade option |
| commons-io | 2.15.1 | Selected upgrade option |
| com.google.guava:guava | 33.2.1-jre | Selected upgrade option |
| org.apache.httpcomponents:httpclient | 4.5.14 | Selected upgrade option |
| commons-validator | 1.8.0 | Selected upgrade option |
| commons-collections4 | 4.4 | Selected upgrade option |
| commons-lang3 | 3.14.0 | Selected upgrade option |
| org.owasp.antisamy:antisamy | 1.7.5 | Selected upgrade option |
| org.mapstruct:mapstruct | 1.6.2 | Verified compatibility matrix |
| Drools | **TODO — spike required** (minimum 8.0.0) | Unverified; see open question OQ-1 |
| Infinispan | **TODO — spike required** (minimum 14.0.0.Final) | Unverified; see open question OQ-2 |
| elasticsearch property | Removed | Selected upgrade option |
| JaCoCo threshold sm-core | ≥ 20 % | Selected upgrade option |
| JaCoCo threshold sm-shop | ≥ 20 % | Selected upgrade option |
| OWASP Dependency-Check | Added to CircleCI pipeline | Selected upgrade option |
| Actuator endpoint restriction | Management port + authentication | Selected upgrade option |
| Dockerfile HEALTHCHECK | Added | Selected upgrade option |
| H2 file in Docker image | Removed from build context | Selected upgrade option |

---

## 6. Current-to-Target Compatibility Matrix

| Component | Current | Target | Compatibility Status | Breaking Change |
|-----------|---------|--------|---------------------|-----------------|
| Docker base image | adoptopenjdk/openjdk11-openj9:alpine | eclipse-temurin:17-jre-alpine | Incompatible → Compatible | No |
| spring-boot-starter-parent | 2.5.12 | 3.3.6 | Incompatible → Compatible | **YES** — javax→jakarta, Security 6 API removals, Hibernate 6 HQL |
| Spring Security | 5.5.x | 6.3.x | Incompatible → Compatible | **YES** — deprecated APIs removed |
| Hibernate ORM | 5.4.x | 6.5.x | Incompatible → Compatible | **YES** — HQL syntax, criteria API, type mappings |
| Springfox → springdoc-openapi | 2.9.2 | 2.5.0 | Incompatible → Compatible | **YES** — annotation replacement required |
| JJWT | 0.8.0 | 0.12.6 | Incompatible → Compatible | **YES** — full API rewrite |
| MapStruct | 1.3.0.Final | 1.6.2 | Incompatible → Compatible | Minor — annotation processor config update |
| commons-fileupload | 1.3.3 | 1.5 | CVE → Patched | No |
| commons-io | 2.7 | 2.15.1 | CVE → Patched | No |
| Guava | 27.1-jre | 33.2.1-jre | CVE → Patched | No |
| httpclient | 4.5.2 | 4.5.14 | CVE → Patched | No |
| commons-validator | 1.5.1 | 1.8.0 | Outdated → Current | No |
| commons-collections4 | 4.1 | 4.4 | Outdated → Current | No |
| commons-lang3 | 3.5 | 3.14.0 | Outdated → Current | No |
| antisamy | 1.6.7 | 1.7.5 | Outdated → Current | No |

---

## 7. Scope

### In Scope
- All 22 changes listed in the selected upgrade option.
- All five Maven modules: `sm-core`, `sm-shop`, `sm-shop-model`, `sm-core-model`, `sm-core-modules`. _(Unverified: no Code Insights evidence ID supplied.)_
- Source code, CI/CD (CircleCI), infrastructure (Dockerfile), tests, and documentation.

### Out of Scope
- Java 21 upgrade (future increment).
- Drools upgrade beyond the compatibility spike (T-05).
- Infinispan replacement with Redis/Spring Cache (future increment; spike only in this effort).
- Kubernetes manifests or Helm charts (none detected in repository).
- Distributed tracing / OpenTelemetry instrumentation.
- Structured logging configuration.
- Graceful shutdown configuration.
- Spring Cloud Config or Vault integration.

---

## 8. Affected Components and Interfaces

### Security Layer (sm-shop)
- `MultipleEntryPointsSecurityConfig.java` — Spring Security 6 rewrite required [Q-10] _(Unverified: no Code Insights evidence ID supplied.)_
- `AuthenticationTokenFilter.java` — JJWT API migration [Q-06] _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTTokenUtil.java` (lines 26–193) — JJWT API migration [Q-07] _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTAdminAuthenticationManager.java`, `JWTCustomerAuthenticationManager.java` — JJWT migration _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTAdminAuthenticationProvider.java`, `JWTCustomerAuthenticationProvider.java` — Spring Security 6 _(Unverified: no Code Insights evidence ID supplied.)_
- `AuthenticateUserApi.java`, `AuthenticateCustomerApi.java` — JWT token issuance endpoints _(Unverified: no Code Insights evidence ID supplied.)_
- `CredentialsServiceImpl.java`, `CredentialsService.java` — blast radius of security config [Q-10] _(Unverified: no Code Insights evidence ID supplied.)_

### API Documentation Layer (sm-shop)
- All classes annotated with `@Api`, `@ApiOperation`, `@ApiParam` (Springfox) — must be replaced with OpenAPI 3 equivalents (`@Tag`, `@Operation`, `@Parameter`) _(Unverified: no Code Insights evidence ID supplied.)_
- `ShopApplicationConfiguration.java` — Springfox bean configuration removal _(Unverified: no Code Insights evidence ID supplied.)_

### Persistence Layer (sm-core, sm-core-model)
- All JPA entities using `javax.persistence.*` — namespace migration to `jakarta.persistence.*` _(Unverified: no Code Insights evidence ID supplied.)_
- `AuditSection.java` (fan-in 31) — JPA annotation migration [Q-03] _(Unverified: no Code Insights evidence ID supplied.)_
- `Transaction.java` (fan-in 22) — JPA annotation migration [Q-03] _(Unverified: no Code Insights evidence ID supplied.)_
- Custom HQL queries in `CategoryServiceImpl`, `OrderServiceImpl`, `ProductServiceImpl`, `ShippingServiceImpl` — Hibernate 6 audit required [Q-14] _(Unverified: no Code Insights evidence ID supplied.)_
- `CmsStaticContentFileManagerImpl` (infinispan), `CmsImageFileManagerImpl` (infinispan) — Infinispan migration [Q-14] _(Unverified: no Code Insights evidence ID supplied.)_

### Rules Engine (sm-core)
- `DroolsBeanFactory.java` (lines 24–112) — Drools Jakarta compatibility spike [Q-08] _(Unverified: no Code Insights evidence ID supplied.)_
- `PromoCodeCalculatorModule.java`, `ShippingDecisionPreProcessorImpl.java`, `CustomShippingQuoteRules.java` — Drools consumers [Q-08] _(Unverified: no Code Insights evidence ID supplied.)_

### Mapper Layer (sm-shop)
- `ReadableProductMapper.java` (lines 65–691, fan-out 20) — MapStruct 1.6.2 annotation processor [Q-12] _(Unverified: no Code Insights evidence ID supplied.)_
- `PersistableProductDefinitionMapper.java` (fan-out 16) — MapStruct migration [Q-13] _(Unverified: no Code Insights evidence ID supplied.)_
- `OrderFacadeImpl.java` (lines 113–1648, fan-out 22) — highest complexity class [Q-13] _(Unverified: no Code Insights evidence ID supplied.)_

### Infrastructure
- `Dockerfile` — base image, HEALTHCHECK, H2 file removal _(Unverified: no Code Insights evidence ID supplied.)_
- `.circleci/config.yml` — OWASP Dependency-Check plugin, JaCoCo thresholds _(Unverified: no Code Insights evidence ID supplied.)_

---

## 9. Breaking Changes

| # | Change | Affected Files | Mitigation |
|---|--------|---------------|------------|
| BC-1 | `javax.*` → `jakarta.*` namespace | All 1,210 Java files across 5 modules | OpenRewrite recipe `org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_3` | _(Unverified: no Code Insights evidence ID supplied.)_
| BC-2 | Spring Security 6 removes `WebSecurityConfigurerAdapter` and deprecated filter chain APIs | `MultipleEntryPointsSecurityConfig.java` and all security classes in blast radius | Rewrite to `SecurityFilterChain` bean model | _(Unverified: no Code Insights evidence ID supplied.)_
| BC-3 | JJWT 0.8.0 → 0.12.6 full API rewrite | `JWTTokenUtil.java`, `AuthenticationTokenFilter.java`, `JWTAdminAuthenticationManager.java`, `JWTCustomerAuthenticationManager.java` | Migrate to `Jwts.parser().verifyWith(key).build()` pattern | _(Unverified: no Code Insights evidence ID supplied.)_
| BC-4 | Springfox annotations removed | All `@Api`, `@ApiOperation`, `@ApiParam` usages across sm-shop | Replace with `@Tag`, `@Operation`, `@Parameter` from `io.swagger.v3.oas.annotations` | _(Unverified: no Code Insights evidence ID supplied.)_
| BC-5 | Hibernate 6 HQL/criteria changes | Custom queries in `CategoryServiceImpl`, `OrderServiceImpl`, `ProductServiceImpl`, `ShippingServiceImpl` | Audit and update HQL; replace deprecated `Session.createCriteria()` | _(Unverified: no Code Insights evidence ID supplied.)_
| BC-6 | Drools 7 uses `javax.enterprise` | `DroolsBeanFactory.java` and consumers | Spike required; may require upgrade to Drools 8.x | _(Unverified: no Code Insights evidence ID supplied.)_
| BC-7 | Infinispan 9.x uses `javax.*` | `CmsStaticContentFileManagerImpl`, `CmsImageFileManagerImpl` | Spike required; may require upgrade to Infinispan 14+ or replacement | _(Unverified: no Code Insights evidence ID supplied.)_

---

## 10. Testable Acceptance Criteria

| ID | Criterion | Verification Method |
|----|-----------|-------------------|
| AC-1 | Application compiles with Java 17 and Spring Boot 3.3.6 | `mvn clean package -DskipTests` exits 0 | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-2 | All existing tests pass | `mvn test` exits 0 | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-3 | JaCoCo line coverage ≥ 20 % for sm-core | JaCoCo report in CI |
| AC-4 | JaCoCo line coverage ≥ 20 % for sm-shop | JaCoCo report in CI |
| AC-5 | No CRITICAL or HIGH CVEs in OWASP report | OWASP Dependency-Check report in CI |
| AC-6 | Admin login returns valid JWT | `POST /api/v1/auth/login` returns HTTP 200 with token | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-7 | Customer login returns valid JWT | `POST /api/v1/customer/login` returns HTTP 200 with token | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-8 | OpenAPI UI accessible | `GET /swagger-ui.html` returns HTTP 200 | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-9 | Actuator health on management port only | `GET /actuator/health` on app port returns 404; on management port returns 200 | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-10 | Docker image builds and starts | `docker build` and `docker run` succeed; HEALTHCHECK passes | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-11 | H2 file absent from Docker image | `docker run --rm <image> ls /path/to/SALESMANAGER.h2.db` returns non-zero | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-12 | No `javax.` imports remain in source | `grep -r "import javax\." src/` returns 0 matches (excluding `javax.mail`, `javax.xml` if intentionally retained) | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-13 | Springfox dependency absent | `mvn dependency:tree` shows no `io.springfox` artifacts | _(Unverified: no Code Insights evidence ID supplied.)_
| AC-14 | JJWT 0.8.0 absent | `mvn dependency:tree` shows no `io.jsonwebtoken:jjwt:0.8.0` | _(Unverified: no Code Insights evidence ID supplied.)_

---

## 11. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R-1 | javax→jakarta migration introduces runtime failures in untested code paths | High (sm-core 0 %, sm-shop 4 % coverage) | High | Write integration tests for critical paths before migration; use OpenRewrite to minimise manual errors |
| R-2 | Drools 7.32.0.Final incompatible with Jakarta EE; no verified upgrade path | Medium | High | Spike T-05 must complete before Spring Boot upgrade; fallback: disable Drools temporarily |
| R-3 | Infinispan 9.4.18.Final incompatible with Spring Boot 3.x | High | High | Spike T-05 must complete; fallback: replace with Spring Cache + local Caffeine for dev |
| R-4 | Hibernate 6 HQL changes break custom queries | Medium | Medium | Audit all JPQL/HQL in `CategoryServiceImpl`, `OrderServiceImpl`, `ProductServiceImpl`, `ShippingServiceImpl` | _(Unverified: no Code Insights evidence ID supplied.)_
| R-5 | Spring Security 6 API removals break authentication | High | Critical | Rewrite `MultipleEntryPointsSecurityConfig` before upgrading Spring Boot | _(Unverified: no Code Insights evidence ID supplied.)_
| R-6 | JJWT 0.12.x API is a full rewrite; token format may change | High | High | Validate token round-trip in integration tests; document any format change |
| R-7 | MapStruct 1.3.0.Final annotation processor incompatible with Java 17 | Medium | Medium | Upgrade MapStruct to 1.6.2 before raising Java version |
| R-8 | 35 person-day budget insufficient if Drools/Infinispan spikes reveal full rewrites | Medium | Medium | Escalate early; Drools/Infinispan work may require a separate effort |

---

## 12. Open Questions

| ID | Question | Owner | Resolution Path |
|----|----------|-------|----------------|
| OQ-1 | What is the correct Drools target version compatible with Spring Boot 3.x / Jakarta EE? | Tech Lead | Spike T-05; consult https://www.drools.org/learn/documentation.html |
| OQ-2 | What is the correct Infinispan target version, or should it be replaced with Spring Cache + Redis? | Tech Lead | Spike T-05; consult https://infinispan.org/docs/stable/titles/spring_boot/spring_boot.html |
| OQ-3 | Does the JWT token format change between JJWT 0.8.0 and 0.12.6 in a way that invalidates existing tokens? | Security Lead | Test token round-trip in T-07 |
| OQ-4 | Are there any `javax.mail` or `javax.xml` usages that should NOT be migrated to `jakarta.*`? | Dev Lead | Audit before running OpenRewrite recipe | _(Unverified: no Code Insights evidence ID supplied.)_
| OQ-5 | What is the current Maven compiler plugin version in each pom.xml? | Dev Lead | `mvn help:effective-pom` — marked as "unknown" in upstream compatibility matrix | _(Unverified: no Code Insights evidence ID supplied.)_
| OQ-6 | Is the elasticsearch 7.5.2 property the only remaining reference, or are there other elasticsearch client usages? | Dev Lead | `mvn dependency:tree` after property removal | _(Unverified: no Code Insights evidence ID supplied.)_