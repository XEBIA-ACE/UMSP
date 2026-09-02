# Shopizer — Integration Smoke Test & Regression Validation: Task List

## ⚠️ BCM Compliance Gap
All tasks are scoped application-wide. BCM scope must be defined before production gate.

---

## Phase 1: Build Configuration & Test Infrastructure

### Task 1.1 — Confirm Build Tool
- **Action**: Inspect source root for `pom.xml` or `build.gradle` files in `sm-core-model/`, `sm-core/`, `sm-shop/`
- **CAST context**: Build tool not available in CAST MCP — packages query returned no results; Java Properties File query returned no results
- **Deliverable**: Confirmed build tool type and count of build manifest files
- **Dependency**: None

### Task 1.2 — Add Test Dependencies to Build Manifest
- **Action**: Add JUnit 5, Spring Boot Test, RestAssured/MockMvc, and Testcontainers to the build manifest of `sm-shop` module
- **CAST context**: ⚠️ Build tool not confirmed — SME must validate before executing
- **Deliverable**: Updated build manifest with test dependencies
- **Dependency**: Task 1.1

### Task 1.3 — Create Base Test Configuration Class
- **Action**: Create `src/test/java/com/salesmanager/shop/test/BaseIntegrationTest.java` in `sm-shop` module
- **Configuration**: `@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)`
- **CAST context**: Spring Boot application entry point is in `sm-shop/src/main/java/com/salesmanager/shop/` (Source: CAST MCP — Spring Bean filePaths)
- **Deliverable**: Base test class with Spring context loading
- **Dependency**: Task 1.2

---

## Phase 2: Smoke Tests

### Task 2.1 — Spring Context Load Test
- **Action**: Create `ApplicationContextSmokeTest.java` that asserts Spring context loads without errors
- **Scope**: Exercises all 100+ Spring Beans including:
  - `ShopApplicationConfiguration` (CAST ID: beans in `sm-shop/src/main/java/com/salesmanager/shop/application/config/ShopApplicationConfiguration.java`)
  - `MultipleEntryPointsSecurityConfig` (CAST ID: beans in `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java`)
  - XML beans: `shopizer-core-cms.xml`, `shopizer-core-modules.xml`, `shopizer-core-config.xml`, `shopizer-servlet-context.xml`
- **Deliverable**: Passing context load test
- **Dependency**: Task 1.3

### Task 2.2 — Admin Authentication Smoke Test
- **Action**: Create `AdminAuthSmokeTest.java`
- **Target endpoint**: POST `/api/v1/private/login/` (CAST transaction ID: 236377, fullSize: 68)
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/user/AuthenticateUserApi.java`
- **Spring Bean**: `authenticateUserApi` (CAST ID: 21264)
- **Assertion**: HTTP 200, response body contains JWT token field
- **Dependency**: Task 2.1

### Task 2.3 — Customer Authentication Smoke Test
- **Action**: Create `CustomerAuthSmokeTest.java`
- **Target endpoint**: POST `/api/v1/customer/login/` (CAST transaction ID: 236432, fullSize: 63)
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/AuthenticateCustomerApi.java`
- **Assertion**: HTTP 200, response body contains JWT token field
- **Dependency**: Task 2.1

### Task 2.4 — Catalog Browsing Smoke Test
- **Action**: Create `CatalogBrowsingSmokeTest.java`
- **Target endpoint**: GET `/api/v1/category/` (CAST transaction ID: 236586, fullSize: 2,944, reducedSize: 187)
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/CategoryApi.java`
- **Spring Bean**: `categoryFacade` (CAST ID: 21242)
- **Assertion**: HTTP 200, response body is non-empty JSON array
- **Dependency**: Task 2.1

### Task 2.5 — Cart Creation Smoke Test
- **Action**: Create `CartCreationSmokeTest.java`
- **Target endpoint**: POST `/api/v1/cart/` (CAST transaction ID: 236389, fullSize: 1,085, reducedSize: 59)
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java`
- **Assertion**: HTTP 200 or 201, response body contains cart identifier
- **Dependency**: Task 2.1

### Task 2.6 — Checkout Smoke Test
- **Action**: Create `CheckoutSmokeTest.java`
- **Target endpoint**: POST `/api/v1/cart/{}/checkout/` (CAST transaction ID: 236423, fullSize: 3,254, reducedSize: 154)
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderApi.java`
- **Spring Bean**: `orderFacadev1` (CAST ID: 20673)
- **Prerequisite**: Valid cart must be created first (depends on Task 2.5)
- **Assertion**: HTTP 200 or 400 (with valid error body), not 500
- **Dependency**: Task 2.5

### Task 2.7 — Customer Registration Smoke Test
- **Action**: Create `CustomerRegistrationSmokeTest.java`
- **Target endpoint**: POST `/api/v1/customer/register/` (CAST transaction ID: 236433, fullSize: 3,065, reducedSize: 139)
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/AuthenticateCustomerApi.java`
- **Spring Bean**: `customerFacadev1` (CAST ID: 21241)
- **Assertion**: HTTP 200 or 201, no 500 errors
- **Dependency**: Task 2.1

### Task 2.8 — Store Configuration Smoke Test
- **Action**: Create `StoreConfigSmokeTest.java`
- **Target endpoint**: GET `/api/v1/private/store/{}/` (CAST transaction ID: 236503, fullSize: 501, reducedSize: 37)
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/store/MerchantStoreApi.java`
- **Spring Bean**: `merchantService` (CAST ID: 21130)
- **Prerequisite**: Admin JWT from Task 2.2
- **Assertion**: HTTP 200, response body contains store details
- **Dependency**: Task 2.2

---

## Phase 3: Regression Tests — Public APIs

### Task 3.1 — Cart API Regression Tests
- **Action**: Create `CartApiRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java`
- **Operations to cover** (6 operations, CAST IDs: 12835, 12662, 13008, 12788, 12824, 24926):
  - POST `/api/v1/cart/`
  - PUT `/api/v1/cart/{}/`
  - GET `/api/v1/cart/{}/`
  - POST `/api/v1/cart/{}/multi/`
  - POST `/api/v1/cart/{}/promo/{}/`
  - DELETE `/api/v1/cart/{}/product/{}/`
- **Dependency**: Task 2.5

### Task 3.2 — Category API Regression Tests
- **Action**: Create `CategoryApiRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/CategoryApi.java`
- **Operations to cover** (4 operations, CAST IDs: 13089, 13091, 13088, 13092):
  - GET `/api/v1/category/`
  - GET `/api/v1/category/name/{}/`
  - GET `/api/v1/category/product/{}/`
  - GET `/api/v1/category/{}/`
- **Dependency**: Task 2.4

### Task 3.3 — Product Browsing Regression Tests
- **Action**: Create `ProductBrowsingRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductApi.java`
- **Operations to cover** (CAST IDs: 236545, 236543, 236544, 236546):
  - GET `/api/v1/product/{}/`
  - GET `/api/v1/product/friendly/{}/`
  - GET `/api/v1/product/slug/{}/`
  - GET `/api/v1/products/` (search)
- **Dependency**: Task 2.1

### Task 3.4 — Customer Auth Regression Tests
- **Action**: Create `CustomerAuthRegressionTest.java`
- **Source files**: `AuthenticateCustomerApi.java`, `ResetCustomerPasswordApi.java`
- **Operations to cover** (CAST IDs: 236432, 236427, 236433, 236426, 236559):
  - POST `/api/v1/customer/login/`
  - POST `/api/v1/customer/register/`
  - POST `/api/v1/customer/password/reset/request/`
  - POST `/api/v1/customer/{}/password/{}/`
  - GET `/api/v1/customer/{}/reset/{}/`
- **Dependency**: Task 2.3

### Task 3.5 — Reference Data Regression Tests
- **Action**: Create `ReferenceDataRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/references/ReferencesApi.java`
- **Operations to cover** (CAST IDs: 236322, 236320):
  - GET `/api/v1/country/`
  - GET `/api/v1/currency/`
- **Dependency**: Task 2.1

### Task 3.6 — Content API Regression Tests
- **Action**: Create `ContentApiRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/content/ContentApi.java`
- **Operations to cover** (CAST IDs: 13079, 13070, 13069, 13082, 13074, 13072, 13089, 236577):
  - GET `/api/v1/content/boxes/`, `/api/v1/content/boxes/{}/`
  - GET `/api/v1/content/images/`
  - GET `/api/v1/content/pages/`, `/api/v1/content/pages/{}/`, `/api/v1/content/pages/name/{}/`
  - GET `/api/v1/content/summary/`
- **Dependency**: Task 2.1

---

## Phase 4: Regression Tests — Authenticated Customer APIs

### Task 4.1 — Authenticated Customer Profile Regression Tests
- **Action**: Create `AuthCustomerProfileRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/CustomerApi.java`
- **Operations to cover** (CAST IDs: 12435, 24949, 12959, 13064):
  - ANY `/api/v1/auth/customer/`
  - DELETE `/api/v1/auth/customer/`
  - ANY `/api/v1/auth/customer/address/`
  - GET `/api/v1/auth/customer/profile/`
- **Prerequisite**: Customer JWT from Task 2.3
- **Dependency**: Task 2.3

### Task 4.2 — Authenticated Order Regression Tests
- **Action**: Create `AuthOrderRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderApi.java`
- **Operations to cover** (CAST IDs: 236329, 236556):
  - GET `/api/v1/auth/orders/`
  - GET `/api/v1/auth/orders/{}/`
- **Prerequisite**: Customer JWT from Task 2.3
- **Dependency**: Task 2.3

### Task 4.3 — Authenticated Product Management Regression Tests
- **Action**: Create `AuthProductRegressionTest.java`
- **Source files**: `ProductApi.java`, `ProductImageApi.java`, `ProductReviewApi.java`
- **Operations to cover** (CAST IDs: 9294, 7715, 24945, 12927, 12917, 7561, 5867, 12665, 24929, 12818, 12796):
  - POST/PUT/DELETE/ANY `/api/v1/auth/product/{}/`
  - POST `/api/v1/auth/products/`
  - POST/DELETE `/api/v1/auth/product/{}/image/`
  - POST/PUT/DELETE `/api/v1/auth/products/{}/reviews/`
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

---

## Phase 5: Regression Tests — Private Admin APIs

### Task 5.1 — Store Management Regression Tests
- **Action**: Create `StoreManagementRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/store/MerchantStoreApi.java`
- **Spring Bean**: `merchantService` (CAST ID: 21130)
- **JPA Entity**: `MerchantStore` (CAST ID: 15393)
- **Operations to cover** (CAST transaction IDs: 236385, 236495, 236604, 236503, 236340, 236498, 236384, 236605, 236383, 236501, 236500, 236497, 236502):
  - POST/GET/PUT/DELETE `/api/v1/private/store/`
  - GET/PUT/DELETE `/api/v1/private/store/{}/`
  - GET/POST `/api/v1/private/store/{}/marketing/`
  - POST/DELETE `/api/v1/private/store/{}/marketing/logo/`
  - GET `/api/v1/private/stores/`, `/api/v1/private/stores/names/`
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

### Task 5.2 — Product Administration Regression Tests
- **Action**: Create `ProductAdminRegressionTest.java`
- **Source files**: `ProductApi.java`, `ProductAttributeOptionApi.java`, `ProductInventoryApi.java`, `ProductPriceApi.java`, `ProductImageApi.java`, `ProductGroupApi.java`
- **JPA Entities**: Product (no ID returned), ProductAttribute (no ID returned), ProductAvailability (no ID returned), ProductPrice (no ID returned), ProductImage (no ID returned)
- **Operations to cover**: All private product endpoints (15+ operations)
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

### Task 5.3 — Customer Administration Regression Tests
- **Action**: Create `CustomerAdminRegressionTest.java`
- **Source files**: `CustomerApi.java`, `CustomerReviewApi.java`
- **JPA Entity**: `Customer` (CAST ID: 4951)
- **Spring Bean**: `customerService` (CAST ID: 21141)
- **Operations to cover** (CAST transaction IDs: 236430, 236562, 236630, 236563, 236358, 236460, 236564, 236428, 236627, 236356):
  - POST/GET/PUT/DELETE `/api/v1/private/customer/`
  - GET/PUT/DELETE `/api/v1/private/customer/{}/`
  - ANY `/api/v1/private/customer/{}/address/`
  - GET `/api/v1/private/customers/`
  - POST/PUT/DELETE `/api/v1/private/customers/{}/reviews/`
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

### Task 5.4 — Order Administration Regression Tests
- **Action**: Create `OrderAdminRegressionTest.java`
- **Source files**: `OrderApi.java`, `OrderPaymentApi.java`, `OrderStatusHistoryApi.java`
- **JPA Entities**: `Order` (CAST ID: 15360), `Transaction` (CAST ID: no ID returned), `OrderStatusHistory` (no ID returned)
- **Spring Bean**: `orderService` (CAST ID: 21129)
- **Operations to cover** (CAST transaction IDs: 236558, 236330, 236553, 236557, 236418, 236420, 236457, 236551, 236416, 236555, 236554, 236419, 236355):
  - GET `/api/v1/private/orders/`, `/api/v1/private/orders/customers/{}/`
  - GET/PUT `/api/v1/private/orders/{}/`
  - POST `/api/v1/private/orders/{}/authorize/`, `/api/v1/private/orders/{}/capture/`, `/api/v1/private/orders/{}/refund/`
  - GET/POST `/api/v1/private/orders/{}/history/`
  - GET `/api/v1/private/orders/{}/payment/nextTransaction/`, `/api/v1/private/orders/{}/payment/transactions/`
  - PUT `/api/v1/private/orders/{}/status/`
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

### Task 5.5 — Tax Administration Regression Tests
- **Action**: Create `TaxAdminRegressionTest.java`
- **Source files**: `TaxClassApi.java`, `TaxRatesApi.java`
- **JPA Entity**: `TaxRate` (CAST ID: 236744 — JPA Entity Operation; entity ID not returned separately)
- **Spring Bean**: `taxService` (no ID returned — not found in Spring Bean query results)
- **Operations to cover** (CAST transaction IDs: 236492, 236379, 236493, 236603, 236491, 236339, 236378, 236490, 236602, 236488, 236338, 236489):
  - GET/POST/PUT/DELETE `/api/v1/private/tax/class/`
  - GET/POST/PUT/DELETE `/api/v1/private/tax/rate/`
  - GET `/api/v1/private/tax/rates/`
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

### Task 5.6 — User Management Regression Tests
- **Action**: Create `UserManagementRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/user/UserApi.java`
- **JPA Entity**: `User` (CAST ID: 236738 — JPA Entity Operation; entity ID: 17130 for Group)
- **Spring Bean**: `userService` (no ID returned — not found in Spring Bean query results)
- **Operations to cover** (CAST transaction IDs: 236374, 236483, 236373, 236601, 236337, 236449, 236450, 236484, 236485):
  - POST/GET/PUT/DELETE `/api/v1/private/user/`
  - GET/PUT/DELETE `/api/v1/private/user/{}/`
  - ANY `/api/v1/private/user/{}/enabled/`, `/api/v1/private/user/{}/password/`
  - GET `/api/v1/private/users/`, `/api/v1/private/users/{}/`
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

### Task 5.7 — Payment & Shipping Module Regression Tests
- **Action**: Create `PaymentShippingModuleRegressionTest.java`
- **Source files**: `PaymentApi.java`, `ShippingConfigurationApi.java`, `ShippingExpeditionApi.java`
- **Spring Beans**: `paymentService` (CAST ID: 21125), `paymentConfigurationFacade` (CAST ID: 21226)
- **Operations to cover** (CAST transaction IDs: 236548, 236415, 236547, 236511, 236391, 236510, 236509, 236390, 236514, 236393, 236392, 236607, 236512, 236342, 236513):
  - GET/POST `/api/v1/private/modules/payment/`
  - GET `/api/v1/private/modules/payment/{}/`
  - GET/POST `/api/v1/private/modules/shipping/`
  - GET `/api/v1/private/modules/shipping/{}/`
  - GET/POST `/api/v1/private/shipping/expedition/`
  - GET/POST `/api/v1/private/shipping/origin/`
  - GET/POST/PUT/DELETE `/api/v1/private/shipping/package/`
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

### Task 5.8 — Manufacturer Regression Tests
- **Action**: Create `ManufacturerRegressionTest.java`
- **Source file**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductManufacturerApi.java`
- **JPA Entity**: `Manufacturer` (CAST ID: 17787)
- **Spring Bean**: `manufacturerFacade` (CAST ID: 21227)
- **Operations to cover** (CAST transaction IDs: 236401, 236525, 236613, 236348, 236527):
  - POST/GET/PUT/DELETE `/api/v1/private/manufacturer/`
  - GET `/api/v1/private/manufacturer/unique/`
  - GET `/api/v1/private/manufacturers/`
- **Prerequisite**: Admin JWT from Task 2.2
- **Dependency**: Task 2.2

---

## Phase 6: Structural Flaw Regression Tests

### Task 6.1 — SQL-in-Loop Detection Test
- **Action**: Create `SqlInLoopRegressionTest.java`
- **CAST rule**: "Avoid running SQL queries inside a loop" (rule ID: 1025056, 3 affected objects)
- **Approach**: Instrument the 3 affected objects with a JDBC query counter; execute the API paths that trigger them; assert query count does not exceed a defined threshold per request
- **Deliverable**: Test that fails if SQL-in-loop count increases beyond 3 objects
- **Dependency**: Task 1.3

### Task 6.2 — Empty Catch Block Detection Test
- **Action**: Create `EmptyCatchBlockRegressionTest.java`
- **CAST rule**: "Avoid empty catch blocks for methods with high fan-in" (rule ID: 1060020, 2 affected objects)
- **Approach**: Trigger the 2 affected code paths; assert that exceptions are not silently swallowed (verify via log output or exception propagation)
- **Deliverable**: Test that detects silent failure in high-fan-in methods
- **Dependency**: Task 1.3

---

## Phase 7: Cloud Readiness Validation

### Task 7.1 — Environment Variable Configuration Test
- **Action**: Create `EnvironmentConfigTest.java`
- **CAST finding**: 11 objects access environment variables (cloud-detection-patterns ID: platform-migration:1200001)
- **Approach**: Start application with required environment variables set; assert no startup failures
- **Dependency**: Task 2.1

### Task 7.2 — Hardcoded URL Audit Test
- **Action**: Create `HardcodedUrlAuditTest.java`
- **CAST finding**: 10 objects use hardcoded HTTP URLs (cloud-detection-patterns ID: platform-migration:1200031)
- **Approach**: Static analysis scan or grep for hardcoded `http://` strings; assert count does not exceed 10
- **Dependency**: Task 1.1

### Task 7.3 — Unsecured Data String Documentation
- **Action**: Create `SecurityFindingsReport.md` documenting all 29 "unsecured data string" objects
- **CAST finding**: 29 objects (cloud-detection-patterns ID: platform-migration:1200056, Critical)
- **Deliverable**: Documented known issues list; baseline for future regression
- **Dependency**: None

---

## Phase 8: Test Reporting & BCM Gap Resolution

### Task 8.1 — Test Coverage Report
- **Action**: Generate test coverage report showing all 150+ Spring MVC operations covered
- **Deliverable**: Coverage matrix mapping each CAST transaction ID to at least one test case
- **Dependency**: All Phase 2–6 tasks

### Task 8.2 — BCM Scope Definition
- **Action**: Work with business stakeholders to define BCM scope for Shopizer
- **CAST gap**: No BCM provided — all queries ran application-wide (GR-08 compliance gap)
- **Deliverable**: BCM scope document; re-run CAST queries against scoped subsystem
- **Dependency**: None (parallel track)

### Task 8.3 — Post-Test CAST Scan
- **Action**: Run CAST analysis after test suite implementation; compare structural flaw counts against baseline
- **Baseline**: Shopizer snapshot (delivery: 2026-07-10) — 2 structural flaw rules, 5 total objects
- **Comparison**: Shopizer-3.2.5 snapshot (delivery: 2026-07-30) — 16,572 elements vs. 16,468
- **Deliverable**: CAST scan report confirming no new structural flaws introduced
- **Dependency**: Task 8.1
