## Mandatory Upgrade Coverage
- [ ] **UPG-001: Upgrade Java runtime from 11 to 17 LTS (prerequisite for Spring Boot 3.x)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-002: Update Docker base image from adoptopenjdk/openjdk11-openj9:alpine to eclipse-temurin:17-jre-alpine**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-003: Update Maven compiler source/target from 11 to 17 in all pom.xml modules**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-004: Upgrade spring-boot-starter-parent 2.5.12 → 3.3.x (transitively upgrades Spring Framework 5.3→6.1, Spring Security 5.5→6.3, Hibernate 5.4→6.5, Spring MVC 5.3→6.1)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-005: Run OpenRewrite javax-to-jakarta namespace migration recipe across all source modules (sm-core, sm-shop, sm-shop-model, sm-core-model, sm-core-modules)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-006: Replace io.springfox:springfox-swagger2 2.9.2 with org.springdoc:springdoc-openapi-starter-webmvc-ui 2.5.0**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-007: Upgrade io.jsonwebtoken:jjwt 0.8.0 → io.jsonwebtoken:jjwt-api 0.12.6 + jjwt-impl + jjwt-jackson (breaking API migration)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-008: Upgrade commons-fileupload:commons-fileupload 1.3.3 → 1.5 (fixes CVE-2023-24998)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-009: Upgrade commons-io:commons-io 2.7 → 2.15.1 (fixes CVE-2021-29425)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-010: Upgrade com.google.guava:guava 27.1-jre → 33.2.1-jre (fixes CVE-2023-2976)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-011: Upgrade org.apache.httpcomponents:httpclient 4.5.2 → 4.5.14 (fixes CVE-2020-13956)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-012: Upgrade commons-validator:commons-validator 1.5.1 → 1.8.0**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-013: Upgrade org.apache.commons:commons-collections4 4.1 → 4.4**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-014: Upgrade org.apache.commons:commons-lang3 3.5 → 3.14.0**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-015: Upgrade org.owasp.antisamy:antisamy 1.6.7 → 1.7.5**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-016: Upgrade org.mapstruct:mapstruct 1.3.0.Final → 1.6.2 (Java 17 annotation processor compatibility)**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-017: Remove pinned elasticsearch 7.5.2 property; validate OpenSearch client dependency is correctly declared**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-018: Add OWASP Dependency-Check Maven plugin to CircleCI pipeline**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-019: Restrict Spring Boot Actuator endpoints to management port with authentication**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-020: Add Dockerfile HEALTHCHECK instruction**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-021: Remove H2 database file from Docker image build context**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-022: Raise JaCoCo line coverage threshold for sm-core and sm-shop to 20%**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **VER-023: Pin an exact target for Hibernate ORM**
  - Current selected target: `6.5.x (managed by Spring Boot 3.3.x BOM)`
  - Acceptance: An exact compatible version is selected and its compatibility evidence is recorded before manifest changes.
  - Estimate: Include within the selected option's total effort.
- [ ] **VER-024: Pin an exact target for Spring Security**
  - Current selected target: `6.3.x (managed by Spring Boot 3.3.x BOM)`
  - Acceptance: An exact compatible version is selected and its compatibility evidence is recorded before manifest changes.
  - Estimate: Include within the selected option's total effort.
- [ ] **VER-025: Pin an exact target for Spring Framework**
  - Current selected target: `6.1.x (managed by Spring Boot 3.3.x BOM)`
  - Acceptance: An exact compatible version is selected and its compatibility evidence is recorded before manifest changes.
  - Estimate: Include within the selected option's total effort.
- [ ] **VER-026: Pin an exact target for Upgrade spring-boot-starter-parent**
  - Current selected target: `3.3.x (transitively upgrades Spring Framework 5.3→6.1, Spring Security 5.5→6.3, Hibernate 5.4→6.5, Spring MVC 5.3→6.1)`
  - Acceptance: An exact compatible version is selected and its compatibility evidence is recorded before manifest changes.
  - Estimate: Include within the selected option's total effort.

---

# Tasks: Shopizer Spring Boot 3.3 Migration & Full Dependency Refresh

## Phase 0 — CI Hardening & Baseline

---

### T-01 — Add OWASP Dependency-Check to CI
**Objective:** Establish security scanning baseline before any dependency changes.  
**Evidence:** Q-02 (4 manifests confirmed), Upstream Tech Analysis (no SAST tooling detected)  
**Estimate:** 0.5 person-days  
**Risk:** Low

**Files:**
- `pom.xml` (root) _(Unverified: no Code Insights evidence ID supplied.)_
- `.circleci/config.yml` _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Add `org.owasp:dependency-check-maven:9.x` plugin to `<build><plugins>` in root `pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Configure `<failBuildOnCVSS>7</failBuildOnCVSS>` and `<format>HTML,JSON</format>`. _(Unverified: no Code Insights evidence ID supplied.)_
3. Add a `dependency-check` job step in `.circleci/config.yml` after the `test` step. _(Unverified: no Code Insights evidence ID supplied.)_
4. Archive the HTML report as a CircleCI artifact.

**Acceptance Criteria:**
- [ ] OWASP report generated on every CI build.
- [ ] Build fails if any dependency has CVSS ≥ 7.0 (HIGH or CRITICAL).
- [ ] Existing tests continue to pass.

**Rollback:** Remove plugin from `pom.xml` and CI step. _(Unverified: no Code Insights evidence ID supplied.)_

**Dependencies:** None.

---

## Phase 1 — Java 17 Runtime, Docker, MapStruct

---

### T-02 — Update Dockerfile: Base Image, HEALTHCHECK, H2 Removal
**Objective:** Replace deprecated AdoptOpenJDK base image with Eclipse Temurin 17, add HEALTHCHECK, remove H2 file.  
**Evidence:** Q-01 (repo confirmed), Upstream Tech Analysis (AdoptOpenJDK deprecated, H2 file in image, no HEALTHCHECK)  
**Estimate:** 0.5 person-days  
**Risk:** Low

**Files:**
- `Dockerfile` _(Unverified: no Code Insights evidence ID supplied.)_
- `.dockerignore` (create or update) _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Change `FROM adoptopenjdk/openjdk11-openj9:alpine` to `FROM eclipse-temurin:17-jre-alpine`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Add `HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD curl -f http://localhost:8080/actuator/health || exit 1`. _(Unverified: no Code Insights evidence ID supplied.)_
3. Remove any `COPY SALESMANAGER.h2.db` instruction (or add `SALESMANAGER.h2.db` to `.dockerignore`). _(Unverified: no Code Insights evidence ID supplied.)_
4. Verify no other H2 file references remain in the Dockerfile.

**Acceptance Criteria:**
- [ ] `docker build` succeeds. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] `docker run` starts the container. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] HEALTHCHECK passes after application startup.
- [ ] `docker run --rm <image> find / -name "SALESMANAGER.h2.db"` returns no results. _(Unverified: no Code Insights evidence ID supplied.)_

**Rollback:** Revert Dockerfile to previous version.

**Dependencies:** None.

---

### T-03 — Update Maven Compiler to Java 17 in All Modules
**Objective:** Set Java 17 as the compilation target across all five Maven modules.  
**Evidence:** Q-02 (5 modules confirmed: sm-core, sm-shop, sm-shop-model, sm-core-model, sm-core-modules), Verified compatibility matrix (Maven compiler plugin target 3.13.0)  
**Estimate:** 0.5 person-days  
**Risk:** Low

**Files:**
- `pom.xml` (root) — `<maven.compiler.source>`, `<maven.compiler.target>`, compiler plugin version _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/pom.xml` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/pom.xml` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop-model/pom.xml` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-model/pom.xml` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-modules/pom.xml` _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. In root `pom.xml`, set `<java.version>17</java.version>` (or `<maven.compiler.source>17</maven.compiler.source>` and `<maven.compiler.target>17</maven.compiler.target>`). _(Unverified: no Code Insights evidence ID supplied.)_
2. Update `maven-compiler-plugin` version to `3.13.0` in root `pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
3. Verify each child module inherits or explicitly sets `source`/`target` to 17. _(Unverified: no Code Insights evidence ID supplied.)_
4. Run `mvn clean compile -DskipTests` to confirm compilation succeeds. _(Unverified: no Code Insights evidence ID supplied.)_

**Acceptance Criteria:**
- [ ] `mvn clean compile -DskipTests` exits 0 on all five modules. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] `mvn help:effective-pom | grep "source\|target"` shows `17` for all modules. _(Unverified: no Code Insights evidence ID supplied.)_

**Rollback:** Revert `pom.xml` changes. _(Unverified: no Code Insights evidence ID supplied.)_

**Dependencies:** None (can run in parallel with T-02).

---

### T-04 — Upgrade MapStruct to 1.6.2
**Objective:** Upgrade MapStruct annotation processor for Java 17 compatibility before the Spring Boot upgrade.  
**Evidence:** Q-12 (`ReadableProductMapper` lines 65–691, fan-out 20), Q-13 (`PersistableProductDefinitionMapper` fan-out 16), Verified compatibility matrix (MapStruct 1.3.0.Final → 1.6.2)   _(Unverified: no Code Insights evidence ID supplied.)_
**Estimate:** 1 person-day  
**Risk:** Medium — MapStruct generates code at compile time; generated code must be verified.

**Files:**
- `pom.xml` (root) — `<mapstruct.version>` property _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/pom.xml` — `mapstruct` and `mapstruct-processor` dependency versions _(Unverified: no Code Insights evidence ID supplied.)_

**Affected Symbols:**
- `ReadableProductMapper` (sm-shop/src/main/java/com/salesmanager/shop/mapper/catalog/product/ReadableProductMapper.java, lines 65–691) [Q-12] _(Unverified: no Code Insights evidence ID supplied.)_
- `PersistableProductDefinitionMapper` (sm-shop/src/main/java/com/salesmanager/shop/mapper/catalog/product/PersistableProductDefinitionMapper.java) [Q-13] _(Unverified: no Code Insights evidence ID supplied.)_
- `ReadableOrderProductMapper` (sm-shop/src/main/java/com/salesmanager/shop/mapper/order/ReadableOrderProductMapper.java) _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Update `<mapstruct.version>` to `1.6.2` in root `pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Ensure `mapstruct-processor` is declared in `<annotationProcessorPaths>` of `maven-compiler-plugin` at version `1.6.2`. _(Unverified: no Code Insights evidence ID supplied.)_
3. Run `mvn clean compile -DskipTests` and verify no MapStruct compilation errors. _(Unverified: no Code Insights evidence ID supplied.)_
4. Inspect generated mapper classes in `target/generated-sources/` to confirm correctness. _(Unverified: no Code Insights evidence ID supplied.)_

**Acceptance Criteria:**
- [ ] `mvn clean compile -DskipTests` exits 0. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] Generated mapper classes compile without errors.
- [ ] Existing mapper-related tests pass.

**Rollback:** Revert MapStruct version to `1.3.0.Final`. _(Unverified: no Code Insights evidence ID supplied.)_

**Dependencies:** T-03 (Java 17 compiler must be set first).

---

## Phase 2 — CVE Dependency Refresh

---

### T-05 — Upgrade CVE-Bearing Dependencies (No API Breaks)
**Objective:** Eliminate all critical and high CVEs that do not require API-level code changes.  
**Evidence:** Upstream Tech Analysis (CVE list), Q-02 (4 manifests)  
**Estimate:** 2 person-days  
**Risk:** Low–Medium

**Files:**
- `pom.xml` (root) — `<dependencyManagement>` section _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/pom.xml`, `sm-shop/pom.xml` — direct dependency declarations _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Update `commons-fileupload:commons-fileupload` from `1.3.3` to `1.5` (fixes CVE-2023-24998, CVE-2016-1000031). _(Unverified: no Code Insights evidence ID supplied.)_
2. Update `commons-io:commons-io` from `2.7` to `2.15.1` (fixes CVE-2021-29425). _(Unverified: no Code Insights evidence ID supplied.)_
3. Update `com.google.guava:guava` from `27.1-jre` to `33.2.1-jre` (fixes CVE-2023-2976). _(Unverified: no Code Insights evidence ID supplied.)_
4. Update `org.apache.httpcomponents:httpclient` from `4.5.2` to `4.5.14` (fixes CVE-2020-13956). _(Unverified: no Code Insights evidence ID supplied.)_
5. Update `commons-validator:commons-validator` from `1.5.1` to `1.8.0`. _(Unverified: no Code Insights evidence ID supplied.)_
6. Update `org.apache.commons:commons-collections4` from `4.1` to `4.4`. _(Unverified: no Code Insights evidence ID supplied.)_
7. Update `org.apache.commons:commons-lang3` from `3.5` to `3.14.0`. _(Unverified: no Code Insights evidence ID supplied.)_
8. Update `org.owasp.antisamy:antisamy` from `1.6.7` to `1.7.5`. _(Unverified: no Code Insights evidence ID supplied.)_
9. Remove the pinned `elasticsearch` version property `7.5.2` from root `pom.xml`; verify OpenSearch client dependency is correctly declared without the elasticsearch property. _(Unverified: no Code Insights evidence ID supplied.)_
10. Run `mvn dependency:tree` to confirm no transitive pull-back to old versions. _(Unverified: no Code Insights evidence ID supplied.)_
11. Run `mvn test` to confirm all tests pass. _(Unverified: no Code Insights evidence ID supplied.)_

**Acceptance Criteria:**
- [ ] OWASP Dependency-Check reports no CRITICAL or HIGH CVEs for the upgraded dependencies.
- [ ] `mvn dependency:tree` shows no `elasticsearch:7.5.2` property reference. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] All existing tests pass.

**Rollback:** Revert `pom.xml` version changes. _(Unverified: no Code Insights evidence ID supplied.)_

**Dependencies:** T-01 (OWASP plugin must be in place to verify).

---

## Phase 3 — Compatibility Spikes & Pre-Migration Tests

---

### T-06 — Drools & Infinispan Compatibility Spikes
**Objective:** Determine the correct upgrade path for Drools 7.32.0.Final and Infinispan 9.4.18.Final before the Spring Boot upgrade.  
**Evidence:** Q-08 (`DroolsBeanFactory` lines 24–112), Q-09 (Drools consumers: `PromoCodeCalculatorModule`, `ShippingDecisionPreProcessorImpl`, `CustomShippingQuoteRules`), Q-14 (Infinispan: `CmsStaticContentFileManagerImpl`, `CmsImageFileManagerImpl`), Upstream compatibility matrix (both "unverified")  
**Estimate:** 3 person-days  
**Risk:** High — outcome determines whether Phase 4 can proceed on schedule.

**Files:**
- `sm-core/src/main/java/com/salesmanager/core/business/configuration/DroolsBeanFactory.java` (lines 24–112) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/integration/shipping/impl/ShippingDecisionPreProcessorImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/integration/shipping/impl/CustomShippingQuoteRules.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/cms/content/infinispan/CmsStaticContentFileManagerImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/cms/product/infinispan/CmsImageFileManagerImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. **Drools spike:** Create a branch `spike/drools-jakarta`. Attempt to upgrade `drools-core` and `kie-spring` to 8.x in `sm-core/pom.xml`. Compile and run `DroolsBeanFactory` tests. Document result. _(Unverified: no Code Insights evidence ID supplied.)_
2. **Infinispan spike:** Create a branch `spike/infinispan-jakarta`. Attempt to upgrade `infinispan-core` to 14.x in `sm-core/pom.xml`. Compile and run Infinispan-dependent tests. Document result. _(Unverified: no Code Insights evidence ID supplied.)_
3. If either upgrade fails, document the fallback strategy (disable feature / replace with alternative) and estimate additional effort.
4. Record decisions in ADR.

**Acceptance Criteria:**
- [ ] Drools compatibility decision documented (upgrade version or fallback strategy).
- [ ] Infinispan compatibility decision documented (upgrade version or fallback strategy).
- [ ] Spike branches compile without errors under Java 17.
- [ ] Decision gate: Phase 4 may not begin until this task is complete.

**Rollback:** Spike branches are discarded; no changes to main migration branch.

**Dependencies:** T-03, T-04.

---

### T-07 — Write Pre-Migration Integration Tests
**Objective:** Raise test coverage for critical paths before the high-risk namespace migration.  
**Evidence:** Q-03 (37 test modules, `CategoryManagementAPIIntegrationTest` exists), Q-06 (`AuthenticateUserApi`), Q-07 (`JWTTokenUtil`), Q-12 (`ReadableProductMapper`), Q-13 (`OrderFacadeImpl`), Upstream Tech Analysis (sm-core 0 %, sm-shop 4 % coverage)   _(Unverified: no Code Insights evidence ID supplied.)_
**Estimate:** 5 person-days  
**Risk:** Medium — tests must pass on the current (pre-migration) codebase.

**Files:**
- `sm-shop/src/test/java/com/salesmanager/test/shop/integration/auth/AdminAuthenticationIntegrationTest.java` (new) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/test/java/com/salesmanager/test/shop/integration/auth/CustomerAuthenticationIntegrationTest.java` (new) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/test/java/com/salesmanager/test/shop/integration/product/ProductReadIntegrationTest.java` (new) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/test/java/com/salesmanager/test/shop/integration/order/OrderProcessingIntegrationTest.java` (new) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/test/java/com/salesmanager/test/shop/integration/category/CategoryManagementAPIIntegrationTest.java` (extend existing) _(Unverified: no Code Insights evidence ID supplied.)_

**Affected Symbols:**
- `AuthenticateUserApi` (sm-shop, lines 38–128) [Q-06] _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTTokenUtil` (sm-shop, lines 26–193) [Q-07] _(Unverified: no Code Insights evidence ID supplied.)_
- `AuthenticateCustomerApi` (sm-shop, lines 57–246) _(Unverified: no Code Insights evidence ID supplied.)_
- `ReadableProductMapper` (sm-shop, lines 65–691) [Q-12] _(Unverified: no Code Insights evidence ID supplied.)_
- `OrderFacadeImpl` (sm-shop, lines 113–1648) [Q-13] _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Write `AdminAuthenticationIntegrationTest`: POST to admin login endpoint, assert HTTP 200 and non-null JWT token. _(Unverified: no Code Insights evidence ID supplied.)_
2. Write `CustomerAuthenticationIntegrationTest`: POST to customer login endpoint, assert HTTP 200 and non-null JWT token. _(Unverified: no Code Insights evidence ID supplied.)_
3. Write `ProductReadIntegrationTest`: GET product by ID, assert HTTP 200 and correct product fields. _(Unverified: no Code Insights evidence ID supplied.)_
4. Write `OrderProcessingIntegrationTest`: create order, assert order ID returned. _(Unverified: no Code Insights evidence ID supplied.)_
5. Extend `CategoryManagementAPIIntegrationTest` with additional CRUD coverage. _(Unverified: no Code Insights evidence ID supplied.)_
6. Run `mvn test` and verify JaCoCo interim thresholds (sm-core ≥ 10 %, sm-shop ≥ 10 %). _(Unverified: no Code Insights evidence ID supplied.)_

**Acceptance Criteria:**
- [ ] All new tests pass on the pre-migration codebase.
- [ ] JaCoCo line coverage for `sm-core` ≥ 10 % (interim). _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] JaCoCo line coverage for `sm-shop` ≥ 10 % (interim). _(Unverified: no Code Insights evidence ID supplied.)_

**Rollback:** Remove new test files (no production code changes).

**Dependencies:** T-05 (CVE refresh should be complete to avoid test interference).

---

## Phase 4 — Spring Boot 3.3.6 + javax→jakarta + Security 6 + Hibernate 6

---

### T-08 — Upgrade spring-boot-starter-parent to 3.3.6
**Objective:** Upgrade the Spring Boot parent POM, transitively upgrading Spring Framework 6.1, Spring Security 6.3, Hibernate 6.5, Spring MVC 6.1.  
**Evidence:** Q-02 (root pom.xml confirmed), Verified compatibility matrix (Spring Boot 2.5.12 → 3.3.6)  
**Estimate:** 1 person-day  
**Risk:** High — this is the trigger for all transitive breaking changes.

**Files:**
- `pom.xml` (root) — `<parent><version>` from `2.5.12` to `3.3.6` _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Change `<parent><artifactId>spring-boot-starter-parent</artifactId><version>2.5.12</version>` to `<version>3.3.6</version>`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Run `mvn clean compile -DskipTests` — expect compilation failures (to be fixed in T-09 through T-12). _(Unverified: no Code Insights evidence ID supplied.)_
3. Document all compilation errors as input to subsequent tasks.

**Acceptance Criteria:**
- [ ] `pom.xml` parent version is `3.3.6`. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] Compilation errors are catalogued for T-09–T-12.

**Rollback:** Revert parent version to `2.5.12`. _(Unverified: no Code Insights evidence ID supplied.)_

**Dependencies:** T-06 (Drools/Infinispan decisions must be known), T-07 (pre-migration tests must be in place).

---

### T-09 — Run OpenRewrite javax→jakarta Namespace Migration
**Objective:** Migrate all `javax.*` imports to `jakarta.*` across all five modules.   _(Unverified: no Code Insights evidence ID supplied.)_
**Evidence:** Q-03 (1,210 Java files, 5 modules), Upstream blocker (javax→jakarta touches every module)  
**Estimate:** 2 person-days  
**Risk:** High — touches all 1,210 Java files.

**Files:** All Java source files in:
- `sm-core/src/main/java/` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop-model/src/main/java/` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-model/src/main/java/` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-modules/src/main/java/` _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Add OpenRewrite Maven plugin to root `pom.xml` with recipe `org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_3`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Run `mvn rewrite:run` from the root. _(Unverified: no Code Insights evidence ID supplied.)_
3. Review diff for any `javax.mail` or `javax.xml` usages that should NOT be migrated (OQ-4). _(Unverified: no Code Insights evidence ID supplied.)_
4. Run `grep -r "import javax\." src/` to verify no remaining `javax.*` imports (except intentional exclusions). _(Unverified: no Code Insights evidence ID supplied.)_
5. Run `mvn clean compile -DskipTests` and fix any remaining compilation errors. _(Unverified: no Code Insights evidence ID supplied.)_

**Acceptance Criteria:**
- [ ] `grep -r "import javax\." src/` returns 0 matches (or only intentional exclusions). _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] `mvn clean compile -DskipTests` exits 0. _(Unverified: no Code Insights evidence ID supplied.)_

**Rollback:** `git revert` the OpenRewrite commit; restore from `pre-sb3-migration` tag. _(Unverified: no Code Insights evidence ID supplied.)_

**Dependencies:** T-08.

---

### T-10 — Rewrite Spring Security Configuration for Security 6
**Objective:** Rewrite `MultipleEntryPointsSecurityConfig.java` and related security classes for Spring Security 6.3.   _(Unverified: no Code Insights evidence ID supplied.)_
**Evidence:** Q-10 (blast radius: `AuthenticationTokenFilter`, `CredentialsServiceImpl`, `JWTAdminAuthenticationProvider`, `JWTCustomerAuthenticationProvider`, `ServicesAuthenticationSuccessHandler`, `UserAuthenticationSuccessHandler`), Upstream blocker (Spring Security 6 removes deprecated APIs)   _(Unverified: no Code Insights evidence ID supplied.)_
**Estimate:** 3 person-days  
**Risk:** Critical — authentication failure would block all API access.

**Files:**
- `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/AuthenticationTokenFilter.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/admin/JWTAdminAuthenticationProvider.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/customer/JWTCustomerAuthenticationProvider.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/ServicesAuthenticationSuccessHandler.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/admin/security/UserAuthenticationSuccessHandler.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/resources/application.properties` (or `application.yml`) _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Remove `extends WebSecurityConfigurerAdapter` from `MultipleEntryPointsSecurityConfig`; replace with `@Bean SecurityFilterChain` methods. _(Unverified: no Code Insights evidence ID supplied.)_
2. Replace `configure(HttpSecurity http)` overrides with `SecurityFilterChain` beans. _(Unverified: no Code Insights evidence ID supplied.)_
3. Replace `configure(AuthenticationManagerBuilder auth)` with `AuthenticationManager` bean. _(Unverified: no Code Insights evidence ID supplied.)_
4. Update `AuthenticationTokenFilter` to use `jakarta.servlet.*` (post T-09) and Spring Security 6 filter chain. _(Unverified: no Code Insights evidence ID supplied.)_
5. Update `JWTAdminAuthenticationProvider` and `JWTCustomerAuthenticationProvider` for Security 6 API. _(Unverified: no Code Insights evidence ID supplied.)_
6. Add Actuator management port restriction to `application.properties`: _(Unverified: no Code Insights evidence ID supplied.)_
   ```
   management.server.port=8081
   management.endpoints.web.exposure.include=health,info
   management.endpoint.health.show-details=when-authorized
   ```
7. Run authentication integration tests (from T-07).

**Acceptance Criteria:**
- [ ] `mvn clean package` exits 0. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] Admin login returns HTTP 200 with JWT token (AC-6).
- [ ] Customer login returns HTTP 200 with JWT token (AC-7).
- [ ] Actuator health on management port only (AC-9).

**Rollback:** Revert security config files to pre-T-10 state.

**Dependencies:** T-09.

---

### T-11 — Hibernate 6 Query Audit and Migration
**Objective:** Audit and update all JPQL/HQL queries and JPA annotations for Hibernate 6.5 compatibility.  
**Evidence:** Q-14 (module dependency graph: `CategoryServiceImpl`, `OrderServiceImpl`, `ProductServiceImpl`, `ShippingServiceImpl`, `PaymentServiceImpl` all depend on `ServiceException`), Q-03 (`AuditSection` fan-in 31, `Transaction` fan-in 22), Upstream blocker (Hibernate 5→6 breaking changes)   _(Unverified: no Code Insights evidence ID supplied.)_
**Estimate:** 3 person-days  
**Risk:** High — incorrect HQL can cause runtime failures.

**Files:**
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/category/CategoryServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/shipping/ShippingServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/services/payments/PaymentServiceImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-model/src/main/java/com/salesmanager/core/model/common/audit/AuditSection.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core-model/src/main/java/com/salesmanager/core/model/payments/Transaction.java` _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Search all service classes for `createCriteria()`, `createQuery()`, and native HQL strings. _(Unverified: no Code Insights evidence ID supplied.)_
2. Replace deprecated `Session.createCriteria()` with JPA `CriteriaBuilder` API. _(Unverified: no Code Insights evidence ID supplied.)_
3. Update any HQL that uses Hibernate 5-specific syntax (e.g., implicit joins, `elements()`, `indices()`). _(Unverified: no Code Insights evidence ID supplied.)_
4. Verify `@Entity`, `@Table`, `@Column` annotations on `AuditSection` and `Transaction` are correct under `jakarta.persistence.*`. _(Unverified: no Code Insights evidence ID supplied.)_
5. Run `mvn test` and fix any `HibernateException` or `QueryException` failures. _(Unverified: no Code Insights evidence ID supplied.)_

**Acceptance Criteria:**
- [ ] `mvn clean package` exits 0. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] All persistence-related tests pass.
- [ ] No `HibernateException` in application startup logs. _(Unverified: no Code Insights evidence ID supplied.)_

**Rollback:** Revert service and entity files.

**Dependencies:** T-09.

---

### T-12 — Apply Drools/Infinispan Migration (Spike Outcome)
**Objective:** Apply the upgrade or replacement strategy determined in T-06.  
**Evidence:** Q-08 (`DroolsBeanFactory`), Q-09 (Drools consumers), Q-14 (Infinispan classes)   _(Unverified: no Code Insights evidence ID supplied.)_
**Estimate:** 2 person-days (may increase based on T-06 outcome)  
**Risk:** High — outcome-dependent.

**Files:** (determined by T-06 spike outcome)
- `sm-core/src/main/java/com/salesmanager/core/business/configuration/DroolsBeanFactory.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/integration/shipping/impl/ShippingDecisionPreProcessorImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/integration/shipping/impl/CustomShippingQuoteRules.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/cms/content/infinispan/CmsStaticContentFileManagerImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/main/java/com/salesmanager/core/business/modules/cms/product/infinispan/CmsImageFileManagerImpl.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/pom.xml` — Drools and Infinispan dependency versions _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Apply Drools upgrade (to version determined in T-06) or implement fallback.
2. Apply Infinispan upgrade (to version determined in T-06) or implement fallback.
3. Run `mvn clean package` and fix compilation errors. _(Unverified: no Code Insights evidence ID supplied.)_
4. Run shipping and promo code tests.

**Acceptance Criteria:**
- [ ] `mvn clean package` exits 0. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] Shipping quote and promo code tests pass.
- [ ] CMS content and image manager tests pass.

**Rollback:** Revert to pre-T-12 state; apply fallback strategy.

**Dependencies:** T-06 (spike must be complete), T-09.

---

## Phase 5 — JJWT 0.12.6 + Springfox→springdoc

---

### T-13 — Migrate JJWT from 0.8.0 to 0.12.6
**Objective:** Replace the critically vulnerable JJWT 0.8.0 with the split-artifact 0.12.6 model.  
**Evidence:** Q-07 (`JWTTokenUtil` lines 26–193, blast radius 55 symbols), Q-06 (`AuthenticationTokenFilter`, `JWTAdminAuthenticationManager`, `JWTCustomerAuthenticationManager`), Upstream Tech Analysis (CVE-2022-45688), Verified compatibility matrix   _(Unverified: no Code Insights evidence ID supplied.)_
**Estimate:** 2 person-days  
**Risk:** High — JWT token format or signing algorithm changes may invalidate existing tokens.

**Files:**
- `pom.xml` (root or `sm-shop/pom.xml`) — remove `io.jsonwebtoken:jjwt:0.8.0`; add `jjwt-api:0.12.6`, `jjwt-impl:0.12.6` (runtime), `jjwt-jackson:0.12.6` (runtime) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/JWTTokenUtil.java` (lines 26–193) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/AuthenticationTokenFilter.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/admin/JWTAdminAuthenticationManager.java` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/security/customer/JWTCustomerAuthenticationManager.java` _(Unverified: no Code Insights evidence ID supplied.)_

**Affected Symbols:**
- `JWTTokenUtil.generateToken`, `JWTTokenUtil.validateToken`, `JWTTokenUtil.getAllClaimsFromToken`, `JWTTokenUtil.doGenerateToken` [Q-07] _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTAdminAuthenticationManager` [Q-06] _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTCustomerAuthenticationManager` [Q-06] _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Remove `<dependency><groupId>io.jsonwebtoken</groupId><artifactId>jjwt</artifactId><version>0.8.0</version></dependency>`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Add three new dependencies: `jjwt-api:0.12.6` (compile), `jjwt-impl:0.12.6` (runtime), `jjwt-jackson:0.12.6` (runtime). _(Unverified: no Code Insights evidence ID supplied.)_
3. In `JWTTokenUtil.java`: _(Unverified: no Code Insights evidence ID supplied.)_
   - Replace `Jwts.builder()...signWith(SignatureAlgorithm.HS512, secret)` with `Jwts.builder()...signWith(Keys.hmacShaKeyFor(secret.getBytes()))`. _(Unverified: no Code Insights evidence ID supplied.)_
   - Replace `Jwts.parser().setSigningKey(secret).parseClaimsJws(token)` with `Jwts.parser().verifyWith(key).build().parseSignedClaims(token)`. _(Unverified: no Code Insights evidence ID supplied.)_
   - Replace `Claims` usage with `Jws<Claims>` where needed. _(Unverified: no Code Insights evidence ID supplied.)_
4. Update `AuthenticationTokenFilter`, `JWTAdminAuthenticationManager`, `JWTCustomerAuthenticationManager` for new API. _(Unverified: no Code Insights evidence ID supplied.)_
5. Run authentication integration tests (from T-07).
6. Validate token round-trip: generate token, parse token, assert claims match.

**Acceptance Criteria:**
- [ ] `mvn dependency:tree` shows no `io.jsonwebtoken:jjwt:0.8.0` (AC-14). _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] Admin login returns HTTP 200 with valid JWT (AC-6).
- [ ] Customer login returns HTTP 200 with valid JWT (AC-7).
- [ ] Token round-trip test passes.

**Rollback:** Revert JJWT dependency and `JWTTokenUtil.java` to pre-T-13 state. _(Unverified: no Code Insights evidence ID supplied.)_

**Dependencies:** T-10 (Spring Security 6 must be in place).

---

### T-14 — Replace Springfox with springdoc-openapi 2.5.0
**Objective:** Remove the abandoned Springfox Swagger2 library and replace with springdoc-openapi 2.5.0.  
**Evidence:** Q-03 (`ShopApplicationConfiguration` confirmed), Upstream Tech Analysis (Springfox abandoned, incompatible with Spring Boot 3.x), Verified compatibility matrix   _(Unverified: no Code Insights evidence ID supplied.)_
**Estimate:** 3 person-days  
**Risk:** Medium — annotation replacement is mechanical but voluminous.

**Files:**
- `pom.xml` (root or `sm-shop/pom.xml`) — remove `io.springfox:springfox-swagger2:2.9.2`, `springfox-swagger-ui`; add `org.springdoc:springdoc-openapi-starter-webmvc-ui:2.5.0` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/application/config/ShopApplicationConfiguration.java` (lines 39–151) _(Unverified: no Code Insights evidence ID supplied.)_
- All `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**/*.java` — annotation replacement _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v2/**/*.java` — annotation replacement _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/main/resources/application.properties` — springdoc configuration _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Remove `io.springfox:springfox-swagger2` and `springfox-swagger-ui` from `pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Add `org.springdoc:springdoc-openapi-starter-webmvc-ui:2.5.0`. _(Unverified: no Code Insights evidence ID supplied.)_
3. Remove `@EnableSwagger2` annotation and `Docket` bean from `ShopApplicationConfiguration.java`. _(Unverified: no Code Insights evidence ID supplied.)_
4. Add `@OpenAPIDefinition` to `ShopApplicationConfiguration.java` or a new `OpenApiConfig` class. _(Unverified: no Code Insights evidence ID supplied.)_
5. Replace annotations across all API controllers:
   - `@Api(tags = "...")` → `@Tag(name = "...")` _(Unverified: no Code Insights evidence ID supplied.)_
   - `@ApiOperation(value = "...")` → `@Operation(summary = "...")` _(Unverified: no Code Insights evidence ID supplied.)_
   - `@ApiParam(...)` → `@Parameter(...)` _(Unverified: no Code Insights evidence ID supplied.)_
   - `@ApiResponse(...)` → `@io.swagger.v3.oas.annotations.responses.ApiResponse(...)` _(Unverified: no Code Insights evidence ID supplied.)_
6. Add springdoc properties to `application.properties`: _(Unverified: no Code Insights evidence ID supplied.)_
   ```
   springdoc.api-docs.path=/api-docs
   springdoc.swagger-ui.path=/swagger-ui.html
   ```
7. Verify `/swagger-ui.html` returns HTTP 200. _(Unverified: no Code Insights evidence ID supplied.)_

**Acceptance Criteria:**
- [ ] `mvn dependency:tree` shows no `io.springfox` artifacts (AC-13). _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] `GET /swagger-ui.html` returns HTTP 200 (AC-8). _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] All API endpoints appear in the OpenAPI UI.

**Rollback:** Revert springdoc dependency and annotation changes; restore Springfox.

**Dependencies:** T-08 (Spring Boot 3.3.6 must be in place; Springfox is incompatible with it).

---

## Phase 6 — Coverage Gates & Final Hardening

---

### T-15 — Raise JaCoCo Coverage Thresholds and Final Validation
**Objective:** Raise JaCoCo line coverage thresholds to 20 % for `sm-core` and `sm-shop`; run full regression suite.   _(Unverified: no Code Insights evidence ID supplied.)_
**Evidence:** Q-03 (37 test modules), Upstream Tech Analysis (sm-core 0 %, sm-shop 4 %), Selected upgrade option (raise to 20 %)  
**Estimate:** 2 person-days  
**Risk:** Low

**Files:**
- `sm-core/pom.xml` — JaCoCo `<minimum>` line coverage from current value to `0.20` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/pom.xml` — JaCoCo `<minimum>` line coverage from current value to `0.20` _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-shop/src/test/java/` — additional tests if needed to meet threshold _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/test/java/` — additional tests if needed to meet threshold _(Unverified: no Code Insights evidence ID supplied.)_
- `README.md` — update to reflect Spring Boot 3.3.6, Java 17, springdoc-openapi _(Unverified: no Code Insights evidence ID supplied.)_

**Implementation Actions:**
1. Run `mvn test` and check current JaCoCo coverage for `sm-core` and `sm-shop`. _(Unverified: no Code Insights evidence ID supplied.)_
2. Write additional unit/integration tests for uncovered paths until ≥ 20 % line coverage is achieved.
3. Update JaCoCo `<minimum>` threshold to `0.20` in `sm-core/pom.xml` and `sm-shop/pom.xml`. _(Unverified: no Code Insights evidence ID supplied.)_
4. Run full `mvn clean verify` and confirm all 14 acceptance criteria pass. _(Unverified: no Code Insights evidence ID supplied.)_
5. Generate final OWASP Dependency-Check report.
6. Update `README.md` with new Java version, Spring Boot version, and API documentation URL. _(Unverified: no Code Insights evidence ID supplied.)_

**Acceptance Criteria:**
- [ ] JaCoCo line coverage ≥ 20 % for `sm-core` (AC-3). _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] JaCoCo line coverage ≥ 20 % for `sm-shop` (AC-4). _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] All 14 acceptance criteria (AC-1 through AC-14) pass.
- [ ] CircleCI pipeline green on `feature/sb3-migration` branch. _(Unverified: no Code Insights evidence ID supplied.)_
- [ ] OWASP report shows no CRITICAL or HIGH CVEs (AC-5).

**Rollback:** Revert JaCoCo threshold changes (does not affect production code).

**Dependencies:** T-13, T-14 (all migration tasks must be complete).

---

## Task Dependency Summary

```
T-01 (OWASP CI)
T-02 (Dockerfile)  ─────────────────────────────────────────────────────────┐
T-03 (Java 17 compiler) ──────────────────────────────────────────────────┐ │
T-04 (MapStruct 1.6.2) ← T-03                                             │ │
T-05 (CVE refresh) ← T-01                                                 │ │
T-06 (Drools/Infinispan spike) ← T-03, T-04                               │ │
T-07 (Pre-migration tests) ← T-05                                         │ │
T-08 (Spring Boot 3.3.6) ← T-06, T-07                                     │ │
T-09 (javax→jakarta) ← T-08                                               │ │
T-10 (Spring Security 6) ← T-09                                           │ │
T-11 (Hibernate 6 audit) ← T-09                                           │ │
T-12 (Drools/Infinispan apply) ← T-06, T-09                               │ │
T-13 (JJWT 0.12.6) ← T-10                                                 │ │
T-14 (springdoc) ← T-08                                                   │ │
T-15 (Coverage + final) ← T-13, T-14, T-11, T-12 ←────────────────────────┘─┘
```

## Effort Summary

| Phase | Tasks | Estimate |
|-------|-------|----------|
| Phase 0 | T-01 | 0.5 pd |
| Phase 1 | T-02, T-03, T-04 | 2 pd |
| Phase 2 | T-05 | 2 pd |
| Phase 3 | T-06, T-07 | 8 pd |
| Phase 4 | T-08, T-09, T-10, T-11, T-12 | 11 pd |
| Phase 5 | T-13, T-14 | 5 pd |
| Phase 6 | T-15 | 2 pd |
| **Total** | **15 tasks** | **30.5 pd** |

*Remaining 4.5 person-days from the 35 pd budget are reserved for Drools/Infinispan escalation (T-06/T-12 overrun) and unexpected compilation issues in Phase 4.*