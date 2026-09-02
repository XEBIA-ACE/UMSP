## Authoritative Input Provenance
- Repository ID: `be3b144d-3b1d-4954-9ef6-6bdb87e8d763/afe6da7b-f274-4d6c-be69-db56bcdd26a8`
- Expected branch: `3.2.7`
- Code Insights grounded: `True`
- Index status: grounded context available
- Current-state source: Tech Analysis
- Target-state source: explicit Selected Upgrade Option changes only

### Evidence Gaps
- No verified target was supplied for Java (current: `11`); it is omitted from Target State.
- No verified target was supplied for JVM (current: `11`); it is omitted from Target State.
- No verified target was supplied for Build tool (current: `Maven`); it is omitted from Target State.
- No verified target was supplied for Package manager (current: `Maven`); it is omitted from Target State.
- The target `6.5.x (managed by Spring Boot 3.3.x BOM)` for Hibernate ORM is non-specific; exact version selection and compatibility verification are required.
- The target `6.3.x (managed by Spring Boot 3.3.x BOM)` for Spring Security is non-specific; exact version selection and compatibility verification are required.
- The target `6.1.x (managed by Spring Boot 3.3.x BOM)` for Spring Framework is non-specific; exact version selection and compatibility verification are required.
- The target `3.3.x (transitively upgrades Spring Framework 5.3→6.1, Spring Security 5.5→6.3, Hibernate 5.4→6.5, Spring MVC 5.3→6.1)` for Upgrade spring-boot-starter-parent is non-specific; exact version selection and compatibility verification are required.

---

# Research: Shopizer Spring Boot 3.3 Migration

## 1. Repository Identity

| Field | Value |
|-------|-------|
| Scoped repo ID | `be3b144d-3b1d-4954-9ef6-6bdb87e8d763/afe6da7b-f274-4d6c-be69-db56bcdd26a8` | _(Unverified: no Code Insights evidence ID supplied.)_
| Repository URL | `https://github.com/shopizer-ecommerce/shopizer` | _(Unverified: no Code Insights evidence ID supplied.)_
| Ref | `3.2.7` | _(Unverified: no Code Insights evidence ID supplied.)_
| Last commit SHA | `6a4a0a65a3408ee8f62597b51d1b3aac24b77dee` | _(Unverified: no Code Insights evidence ID supplied.)_
| Index state | `succeeded` | _(Unverified: no Code Insights evidence ID supplied.)_
| Index job ID | `39d7ed17-4ac5-4926-9e10-8969a8dc7232` | _(Unverified: no Code Insights evidence ID supplied.)_
| Index started | `2026-08-31T11:05:26Z` | _(Unverified: no Code Insights evidence ID supplied.)_
| Index finished | `2026-08-31T11:48:36Z` | _(Unverified: no Code Insights evidence ID supplied.)_

**Grounding decision:** The repository identity is confirmed by Code Insights `list_repos` (Q-01) and `list_index_jobs` (Q-02). The ref `3.2.7` and commit SHA match the expected target. All structural claims in spec.md, plan.md, and tasks.md are grounded in Code Insights tool output unless explicitly labelled as "Upstream Tech Analysis" or "Upstream compatibility matrix". _(Unverified: no Code Insights evidence ID supplied.)_

---

## 2. Index Status

| Metric | Value |
|--------|-------|
| Node count | 17,804 |
| Edge count | 10,959 |
| Java files | 1,210 |
| Manifests | 4 (`pom.xml`, `sm-core-model/pom.xml`, `sm-core/pom.xml`, `sm-shop/pom.xml`) | _(Unverified: no Code Insights evidence ID supplied.)_
| Total CVE count (index) | 5 |
| Total dep count (index) | 18 |
| Languages | java (1,210), sql (1), json (7), yaml (1), markdown (3) |

---

## 3. Technology & Architecture Findings

### 3.1 Module Structure (Code Insights — Q-03)
| Module | Element Count | Cohesion |
|--------|--------------|---------|
| sm-core | 358 | 0.574 |
| sm-shop | 326 | 0.733 |
| sm-shop-model | 323 | 1.000 |
| sm-core-model | 187 | 1.000 |
| sm-core-modules | 15 | 1.000 |

### 3.2 Application Entry Point (Code Insights — Q-03)
- `sm-shop/src/main/java/com/salesmanager/shop/application/ShopApplication.java` (kind: main) _(Unverified: no Code Insights evidence ID supplied.)_

### 3.3 Architectural Layers (Code Insights — Q-03)
- core (535 modules), api (76), test (37), utils (31), common (4), services (3)

### 3.4 Hotspots by Fan-In (Code Insights — Q-03)
| Symbol | Fan-In | File |
|--------|--------|------|
| ServiceRuntimeException | 215 | sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/ServiceRuntimeException.java |
| ServiceException | 153 | sm-core-model/src/main/java/com/salesmanager/core/business/exception/ServiceException.java |
| ResourceNotFoundException | 135 | sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/ResourceNotFoundException.java |
| UnauthorizedException | 47 | sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/UnauthorizedException.java |
| clone | 43 | sm-core-model/src/main/java/com/salesmanager/core/utils/CloneUtils.java |
| ConversionException | 41 | sm-core-model/src/main/java/com/salesmanager/core/business/exception/ConversionException.java |
| IntegrationException | 41 | sm-core-modules/src/main/java/com/salesmanager/core/modules/integration/IntegrationException.java |
| ConversionRuntimeException | 39 | sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/ConversionRuntimeException.java |
| AuditSection | 31 | sm-core-model/src/main/java/com/salesmanager/core/model/common/audit/AuditSection.java |
| Transaction | 22 | sm-core-model/src/main/java/com/salesmanager/core/model/payments/Transaction.java |

---

## 4. Affected Components

### 4.1 JWT / Security Layer (Code Insights — Q-06, Q-07, Q-10)
- `JWTTokenUtil` — `sm-shop/src/main/java/com/salesmanager/shop/store/security/JWTTokenUtil.java` (lines 26–193) _(Unverified: no Code Insights evidence ID supplied.)_
- `AuthenticationTokenFilter` — `sm-shop/src/main/java/com/salesmanager/shop/store/security/AuthenticationTokenFilter.java` (lines 24–145) _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTAdminAuthenticationManager` — `sm-shop/src/main/java/com/salesmanager/shop/store/security/admin/JWTAdminAuthenticationManager.java` (lines 23–94) _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTCustomerAuthenticationManager` — `sm-shop/src/main/java/com/salesmanager/shop/store/security/customer/JWTCustomerAuthenticationManager.java` (lines 24–92) _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTAdminAuthenticationProvider` — `sm-shop/src/main/java/com/salesmanager/shop/store/security/admin/JWTAdminAuthenticationProvider.java` (lines 21–71) _(Unverified: no Code Insights evidence ID supplied.)_
- `JWTCustomerAuthenticationProvider` — `sm-shop/src/main/java/com/salesmanager/shop/store/security/customer/JWTCustomerAuthenticationProvider.java` (lines 19–74) _(Unverified: no Code Insights evidence ID supplied.)_
- `AuthenticateUserApi` — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/user/AuthenticateUserApi.java` (lines 38–128) _(Unverified: no Code Insights evidence ID supplied.)_
- `AuthenticateCustomerApi` — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/AuthenticateCustomerApi.java` (lines 57–246) _(Unverified: no Code Insights evidence ID supplied.)_
- `MultipleEntryPointsSecurityConfig.java` — blast radius: 7 impacted symbols, risk score 11 (LOW band, but test_gap factor 1.0) _(Unverified: no Code Insights evidence ID supplied.)_

### 4.2 Drools Layer (Code Insights — Q-08, Q-09)
- `DroolsBeanFactory` — `sm-core/src/main/java/com/salesmanager/core/business/configuration/DroolsBeanFactory.java` (lines 24–112); blast radius 28 symbols, risk score 16 (LOW band) _(Unverified: no Code Insights evidence ID supplied.)_
- Consumers: `PromoCodeCalculatorModule`, `ShippingDecisionPreProcessorImpl`, `CustomShippingQuoteRules` _(Unverified: no Code Insights evidence ID supplied.)_

### 4.3 Infinispan Layer (Code Insights — Q-14)
- `CmsStaticContentFileManagerImpl` — `sm-core/src/main/java/com/salesmanager/core/business/modules/cms/content/infinispan/CmsStaticContentFileManagerImpl.java` (weight 14 in module dependency graph) _(Unverified: no Code Insights evidence ID supplied.)_
- `CmsImageFileManagerImpl` — `sm-core/src/main/java/com/salesmanager/core/business/modules/cms/product/infinispan/CmsImageFileManagerImpl.java` (weight 14) _(Unverified: no Code Insights evidence ID supplied.)_

### 4.4 Mapper Layer (Code Insights — Q-12, Q-13)
- `ReadableProductMapper` — `sm-shop/src/main/java/com/salesmanager/shop/mapper/catalog/product/ReadableProductMapper.java` (lines 65–691, fan-out 20); blast radius 11 impacted symbols, amplifier: `ConversionRuntimeException` (fan-in 56) _(Unverified: no Code Insights evidence ID supplied.)_
- `PersistableProductDefinitionMapper` — fan-out 16 _(Unverified: no Code Insights evidence ID supplied.)_
- `OrderFacadeImpl` — `sm-shop/src/main/java/com/salesmanager/shop/store/controller/order/facade/OrderFacadeImpl.java` (lines 113–1648, fan-out 22) — highest complexity class _(Unverified: no Code Insights evidence ID supplied.)_

### 4.5 Application Configuration (Code Insights — Q-03)
- `ShopApplicationConfiguration` — `sm-shop/src/main/java/com/salesmanager/shop/application/config/ShopApplicationConfiguration.java` (lines 39–151) — Springfox Docket bean location _(Unverified: no Code Insights evidence ID supplied.)_

---

## 5. Test Infrastructure (Code Insights — Q-03)
- 37 test modules total
- `sm-shop/src/test/java/com/salesmanager/test/shop/integration/category/CategoryManagementAPIIntegrationTest.java` (lines 37–468, fan-out 16) — existing integration test _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/test/java/com/salesmanager/test/shoppingcart/ShoppingCartTest.java` (fan-out 20) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/test/java/com/salesmanager/test/order/OrderTest.java` (fan-out 29) _(Unverified: no Code Insights evidence ID supplied.)_
- `sm-core/src/test/java/com/salesmanager/test/catalog/ProductTest.java` (fan-out 31) _(Unverified: no Code Insights evidence ID supplied.)_
- Upstream Tech Analysis: sm-core 0 % line coverage, sm-shop 4 % line coverage

---

## 6. Risk & Complexity Findings

### 6.1 Cyclomatic Complexity (Code Insights — Q-13)
| Function | Fan-Out | File |
|----------|---------|------|
| getBoxPackagesDetails | 34 | sm-core/.../DefaultPackagingImpl.java |
| testCreateProduct | 31 | sm-core/test/.../ProductTest.java |
| getMerchantOrders | 29 | sm-core/test/.../OrderTest.java |
| getShippingQuotes (USPS) | 24 | sm-core/.../USPSShippingQuote.java |
| processOrder | 22 | sm-shop/.../OrderFacadeImpl.java |
| processOrderModel | 21 | sm-shop/.../OrderFacadeImpl.java |
| populate (ReadableProductPopulator) | 21 | sm-shop/.../ReadableProductPopulator.java |

### 6.2 Dead Code (Code Insights — Q-11)
- No dead code candidates found at confidence ≥ 0.9. All symbols appear reachable.

### 6.3 Blast Radius Summary _(Unverified: no Code Insights evidence ID supplied.)_
| Target | Risk Score | Band | Impacted Symbols | Test Gap |
|--------|-----------|------|-----------------|---------|
| JWTTokenUtil (class) | 21 | LOW | 55 (all internal) | 1.0 |
| MultipleEntryPointsSecurityConfig (file) | 11 | LOW | 7 | 1.0 |
| ReadableProductMapper (file) | 16 | LOW | 11 | 1.0 |
| DroolsBeanFactory (class) | 16 | LOW | 28 (all internal) | 1.0 |

**Note:** All blast radius scores show `test_gap: 1.0`, confirming the upstream finding of near-zero test coverage for affected components. This is the primary risk amplifier for the migration. _(Unverified: no Code Insights evidence ID supplied.)_

---

## 7. Dependency Report
The Code Insights `get_dependency_report` tool returned 0 dependencies and 0 CVEs for all four scanned manifests (Q-15). This is inconsistent with the upstream Tech Analysis which identifies 18 dependencies and 5 CVEs in the index job stats. The discrepancy is likely due to the dependency report tool not resolving transitive dependencies from the BOM-managed parent. **All CVE and dependency version facts in this document are sourced from the upstream Tech Analysis, not from the Code Insights dependency report.** _(Unverified: no Code Insights evidence ID supplied.)_

---

## 8. Numbered Query Log

| Q-ID | Tool | Parameters | Result Count | Finding | Disposition |
|------|------|-----------|-------------|---------|-------------|
| Q-01 | `list_repos` | project_id: `be3b144d-...` | 20 repos | Confirmed repo `afe6da7b-f274-4d6c-be69-db56bcdd26a8`, URL `https://github.com/shopizer-ecommerce/shopizer`, ref `3.2.7`, commit `6a4a0a65a3408ee8f62597b51d1b3aac24b77dee` | Used for repo identity verification | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-02 | `list_index_jobs` | repo_id: `be3b144d-.../afe6da7b-...` | 1 job | State: succeeded; 17,804 nodes, 10,959 edges, 1,210 Java files, 4 manifests, 5 CVEs, 18 deps | Used for index status and manifest count | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-03 | `architecture_overview` | repo_id: `be3b144d-.../afe6da7b-...` | Full overview | 5 modules, 6 layers, 10 hotspots, 37 test modules, entry point `ShopApplication.java` | Used for module structure, hotspots, test infrastructure | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-04 | `find_symbol` (JWT) | query: "JWT", repo_id | 30 symbols | `JWTTokenUtil`, `JWTAdminAuthenticationManager`, `JWTCustomerAuthenticationManager`, `AuthenticateUserApi`, `AuthenticateCustomerApi`, `MultipleEntryPointsSecurityConfig` variables | Used to identify JWT implementation files | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-05 | `find_symbol` (Security class) | kind: class, query: "Security" | 0 results | No class named "Security" found | Not used | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-06 | `find_symbol` (AuthenticationTokenFilter) | query: "AuthenticationTokenFilter" | 4 symbols | `AuthenticationTokenFilter` class at lines 24–145; also referenced in `MultipleEntryPointsSecurityConfig` | Used for security layer mapping | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-07 | `get_symbol` (JWTTokenUtil) | symbol_id: `f890b22e479ee52d` | 1 symbol | `JWTTokenUtil` class, lines 26–193, sm-shop | Used for JWT class location | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-08 | `find_symbol` (Drools) | query: "Drools" | 4 symbols | `DroolsBeanFactory` (lines 24–112), 3 consumer variables | Used for Drools usage mapping | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-09 | `get_symbol` (DroolsBeanFactory) | symbol_id: `f113923d684c7270` | 1 symbol | `DroolsBeanFactory`, sm-core, lines 24–112 | Used for Drools class location | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-10 | `get_blast_radius` (MultipleEntryPointsSecurityConfig) | file_path, kind: file | 7 impacted symbols | `AuthenticationTokenFilter`, `CredentialsServiceImpl`, `JWTAdminAuthenticationProvider`, `JWTCustomerAuthenticationProvider`, `ServicesAuthenticationSuccessHandler`, `UserAuthenticationSuccessHandler`, `CredentialsService`; risk score 11 | Used for security config blast radius | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-11 | `find_dead_code` | min_confidence: 0.9, limit: 30 | 0 candidates | No dead code at high confidence | Used to confirm no cleanup opportunities at high confidence | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-12 | `find_symbol` (ReadableProductMapper) | query: "ReadableProductMapper" | 3 symbols | `ReadableProductMapper` class at lines 65–691, fan-out 20 | Used for mapper complexity | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-13 | `cyclomatic_complexity` | limit: 20 | 20 symbols | Top: `getBoxPackagesDetails` (34), `processOrder` (22), `processOrderModel` (21), `populate` (21) | Used for complexity hotspot identification | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-14 | `module_dependency_graph` | limit: 50 | 50 edges | Infinispan classes confirmed (`CmsStaticContentFileManagerImpl`, `CmsImageFileManagerImpl`); `PaymentServiceImpl`, `CategoryServiceImpl`, `OrderServiceImpl`, `ProductServiceImpl`, `ShippingServiceImpl` all depend on `ServiceException` | Used for Infinispan and service layer mapping | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-15 | `get_dependency_report` | min_severity: HIGH | 0 CVEs, 0 deps | Tool returned empty results for all 4 manifests — inconsistent with index stats | Discarded; CVE facts sourced from upstream Tech Analysis | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-16 | `get_blast_radius` (JWTTokenUtil class) | id: `f890b22e479ee52d`, kind: class | 55 impacted symbols | All internal to JWTTokenUtil.java; test_gap 1.0; risk score 21 | Used for JWT blast radius | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-17 | `get_blast_radius` (DroolsBeanFactory class) | id: `f113923d684c7270`, kind: class | 28 impacted symbols | All internal to DroolsBeanFactory.java; test_gap 1.0; risk score 16 | Used for Drools blast radius | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-18 | `get_blast_radius` (ReadableProductMapper file) | file_path, kind: file | 11 impacted symbols | Amplifier: `ConversionRuntimeException` (fan-in 56); test_gap 1.0; risk score 16 | Used for mapper blast radius | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-19 | `find_symbol` (Infinispan) | query: "Infinispan" | 0 results | No symbol named "Infinispan" — Infinispan usage confirmed via module dependency graph (Q-14) | Infinispan confirmed via Q-14 | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-20 | `find_symbol` (ShopApplication) | query: "ShopApplication" | 2 symbols | `ShopApplication` (entry point), `ShopApplicationConfiguration` (lines 39–151) | Used for entry point and Springfox config location | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-21 | `find_dead_code` | min_confidence: 0.9 | 0 candidates | Confirmed no dead code at high confidence | Used for cleanup assessment | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-22 | `find_symbol` (AuthenticateCustomerApi) | query: "AuthenticateCustomerApi" | 1 symbol | Lines 57–246, sm-shop | Used for customer auth endpoint location | _(Unverified: no Code Insights evidence ID supplied.)_
| Q-23 | `find_symbol` (CategoryManagementAPIIntegrationTest) | query: "CategoryManagementAPIIntegrationTest" | 1 symbol | Lines 37–468, sm-shop/test | Used for existing test infrastructure | _(Unverified: no Code Insights evidence ID supplied.)_

---

## 9. Evidence Gaps

| Gap | Description | Impact | Resolution |
|-----|-------------|--------|-----------|
| EG-1 | Maven compiler plugin current version unknown | Cannot confirm current version; target is 3.13.0 | Run `mvn help:effective-pom` on the repository | _(Unverified: no Code Insights evidence ID supplied.)_
| EG-2 | Drools target version unverified | No confirmed compatible Drools version for Spring Boot 3.x | Spike T-06 required |
| EG-3 | Infinispan target version unverified | No confirmed compatible Infinispan version for Spring Boot 3.x | Spike T-06 required |
| EG-4 | `get_dependency_report` returned 0 results | Cannot confirm CVE details from Code Insights; all CVE facts from upstream Tech Analysis | Upstream Tech Analysis used as authoritative source | _(Unverified: no Code Insights evidence ID supplied.)_
| EG-5 | `iac_index` returned 502 error | Cannot confirm Dockerfile contents, CircleCI config structure from Code Insights | Upstream Tech Analysis used for Dockerfile and CI facts | _(Unverified: no Code Insights evidence ID supplied.)_ **Finding**: Inconclusive; the query returned no usable evidence, so no absence, risk, or coverage conclusion can be drawn.
| EG-6 | `search_code` returned 404 | Cannot search raw file contents for `javax.` imports, Springfox annotations, or pom.xml version strings | Upstream Tech Analysis used; manual verification required | _(Unverified: no Code Insights evidence ID supplied.)_
| EG-7 | No HTTP routes detected by Code Insights | Route nodes not present in graph; cannot enumerate all REST endpoints | API controllers enumerated via `find_symbol` on known class names | _(Unverified: no Code Insights evidence ID supplied.)_
| EG-8 | JWT token format compatibility between 0.8.0 and 0.12.6 | Unknown whether existing tokens remain valid after upgrade | Validate in T-13 integration tests |

---

## 10. Conflicts Between Code Insights and Upstream Tech Analysis

| Item | Upstream Tech Analysis | Code Insights Finding | Resolution |
|------|----------------------|----------------------|-----------|
| CVE count | 5 CVEs in index stats | `get_dependency_report` returned 0 CVEs | Upstream Tech Analysis used; Code Insights dependency report tool appears to not resolve BOM-managed transitive dependencies | _(Unverified: no Code Insights evidence ID supplied.)_
| Dependency count | 18 deps in index stats | `get_dependency_report` returned 0 deps | Same as above | _(Unverified: no Code Insights evidence ID supplied.)_
| Springfox version | 2.9.2 | Not directly confirmed by Code Insights (no `search_code` available) | Upstream Tech Analysis used; labelled as upstream evidence | _(Unverified: no Code Insights evidence ID supplied.)_
| JJWT version | 0.8.0 | Not directly confirmed by Code Insights | Upstream Tech Analysis used; labelled as upstream evidence |
| Infinispan version | 9.4.18.Final | Infinispan usage confirmed via module dependency graph (Q-14); version not confirmed | Upstream Tech Analysis used for version; Code Insights confirms usage |

---

## 11. Grounding Decision

All structural claims about module names, file paths, class names, line numbers, fan-in/fan-out values, blast radius scores, and test module counts are grounded in Code Insights tool output (queries Q-01 through Q-23). All dependency version claims, CVE identifiers, and framework version claims are sourced from the upstream Tech Analysis and verified compatibility matrix, as the Code Insights dependency report tool returned empty results for this repository. This distinction is maintained throughout spec.md, plan.md, and tasks.md. _(Unverified: no Code Insights evidence ID supplied.)_