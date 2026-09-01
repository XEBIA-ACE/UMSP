# Tasks: Post-Migration Smoke Testing — Shopizer

---

## ⚠️ BCM Scope Gap (GR-08)
No BCM subsystem was provided. All tasks cover the full application. SME validation required before execution.

---

## Phase 0: Pre-Test Setup

### Task 0.1 — Deploy Shopizer-3.2.5 to Test Environment
**Dependency**: None
**Files**: `§{main_sources}§/shopizer-3.2.5/sm-shop/` (Spring Boot application module)
**Steps**:
1. Build the `sm-shop` module from the Shopizer-3.2.5 source tree
2. Deploy to isolated test environment
3. Configure test database (H2 or equivalent) with Hibernate schema auto-create
4. Configure AWS S3 test bucket credentials
5. Configure GCP Storage test bucket credentials
6. Confirm no Azure SDK credentials are required (Azure removed in migration)

### Task 0.2 — Verify Spring Context Initialization
**Dependency**: Task 0.1
**Files**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/application/config/ShopApplicationConfiguration.java` (Spring Bean: ShopApplicationConfiguration, no ID captured)
**Steps**:
1. Start application and capture startup logs
2. Verify no `NoSuchBeanDefinitionException` or `BeanCreationException`
3. Verify Spring Security configuration loads: `MultipleEntryPointsSecurityConfig.java` (beans: apiAdminAuthenticationEntryPoint/21159, apiCustomerAuthenticationEntryPoint/21158, authenticationProvider/21160, authenticationTokenFilter/21169)
4. Verify database configuration loads: `DbConfig.java` (bean: dbCredentials/21252)

### Task 0.3 — Verify JPA Schema Validation
**Dependency**: Task 0.2
**Files**: All 65 JPA entity files in `§{main_sources}§/shopizer-3.2.5/sm-core-model/src/main/java/com/salesmanager/core/model/`
**Steps**:
1. Enable Hibernate `validate` or `create` DDL mode
2. Confirm all 65 JPA entities map to database tables without errors:
   - Customer (7189), Order (6168), OrderTotal (6141), MerchantStore (6285)
   - Product (17941), Category (17943), Catalog (17945)
   - ShoppingCart (no ID — truncated in query), Transaction (no ID — truncated)
3. Log any schema validation failures as blockers

---

## Phase 1: Authentication Smoke Tests

### Task 1.1 — Customer Login
**Dependency**: Task 0.3
**Endpoint**: `POST /api/v1/customer/login/`
**CAST Transaction**: Shopizer-3.2.5 ID 232220, full graph=63
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/AuthenticateCustomerApi.java`
**Steps**:
1. POST valid customer credentials to `/api/v1/customer/login/`
2. Assert HTTP 200 response
3. Assert JWT token returned in response body
4. Store token for subsequent authenticated tests

### Task 1.2 — Admin/User Login
**Dependency**: Task 0.3
**Endpoint**: `POST /api/v1/private/login/`
**CAST Transaction**: Shopizer-3.2.5 (page 2, no ID captured), full graph=68
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/user/AuthenticateUserApi.java` (Spring Bean: authenticateUserApi/21326)
**Steps**:
1. POST valid admin credentials to `/api/v1/private/login/`
2. Assert HTTP 200 response
3. Assert JWT token returned
4. Store admin token for subsequent admin tests

### Task 1.3 — Token Refresh
**Dependency**: Task 1.1
**Endpoints**: `GET /api/v1/auth/refresh/` (232275), `GET /api/v1/auth/customer/refresh/` (232366)
**Steps**:
1. Call refresh endpoint with valid token
2. Assert HTTP 200 and new token returned

### Task 1.4 — Customer Registration
**Dependency**: Task 0.3
**Endpoint**: `POST /api/v1/customer/register/`
**CAST Transaction**: Shopizer-3.2.5 ID 232221, full graph=3,093 (P1 — largest auth flow)
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/AuthenticateCustomerApi.java`
**JPA Entities exercised**: Customer (7189), CustomerAttribute (17830), MerchantStore (6285)
**Steps**:
1. POST new customer registration payload
2. Assert HTTP 201 or 200
3. Assert customer record created (verify via GET /api/v1/auth/customer/profile/)
4. Assert Customer (7189) entity persisted in database

---

## Phase 2: Core Business Flow Tests

### Task 2.1 — Shopping Cart Creation
**Dependency**: Task 1.1
**Endpoint**: `POST /api/v1/cart/`
**CAST Transaction**: Shopizer-3.2.5 ID 232152, full graph=1,113, reduced=59
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java`
**JPA Entities exercised**: ShoppingCart (no ID — truncated), ShoppingCartItem (no ID — truncated), Product (17941)
**Steps**:
1. POST cart creation with product ID
2. Assert HTTP 200/201
3. Assert cart ID returned
4. Store cart ID for checkout test

### Task 2.2 — Shopping Cart Checkout (P1 — Highest Risk)
**Dependency**: Task 2.1
**Endpoint**: `POST /api/v1/cart/{cartId}/checkout/`
**CAST Transaction**: Shopizer-3.2.5 ID 232211, full graph=3,281, reduced=154
**Technologies**: aws sdk s3 for java, google cloud storage for java, hibernate, java, java ee, spring web services
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderApi.java`
**JPA Entities exercised**: Order (6168), OrderProduct (17266), OrderTotal (6141), Customer (7189), MerchantStore (6285)
**Steps**:
1. POST checkout payload with payment info to `/api/v1/cart/{cartId}/checkout/`
2. Assert HTTP 200/201
3. Assert order ID returned
4. Verify Order (6168) entity persisted
5. Verify OrderProduct (17266) entity persisted
6. Verify OrderTotal (6141) entity persisted

### Task 2.3 — Authenticated Checkout (P1)
**Dependency**: Task 1.1, Task 2.1
**Endpoint**: `POST /api/v1/auth/cart/{cartId}/checkout/`
**CAST Transaction**: Shopizer-3.2.5 ID 232212, full graph=3,264, reduced=155
**Steps**: Same as Task 2.2 but with authenticated customer token

### Task 2.4 — Store Management (P1)
**Dependency**: Task 1.2
**Endpoints**: `POST /api/v1/private/store/`, `PUT /api/v1/private/store/{storeCode}/`
**CAST Transactions**: (page 3 of Shopizer-3.2.5 transactions), full graphs=3,075/3,085
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/store/MerchantStoreApi.java`
**JPA Entities exercised**: MerchantStore (6285), MerchantConfiguration (14867), Language (17544)
**Steps**:
1. POST new store creation payload
2. Assert HTTP 201
3. Assert store code returned
4. PUT store update payload
5. Assert HTTP 200
6. Verify MerchantStore (6285) entity updated

### Task 2.5 — Product Catalog Browse (P2)
**Dependency**: Task 0.3
**Endpoints**: `GET /api/v1/category/` (232387), `GET /api/v1/category/{id}/` (232390)
**Full graphs**: 2,972 / 2,936
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/CategoryApi.java`
**JPA Entities exercised**: Category (17943), CategoryDescription (17942), Product (17941)
**Steps**:
1. GET /api/v1/category/ — assert HTTP 200, assert category list returned
2. GET /api/v1/category/{id}/ — assert HTTP 200, assert category details returned
3. GET /api/v1/category/product/{id}/ (232386) — assert products in category returned

### Task 2.6 — Order History
**Dependency**: Task 1.1, Task 2.2
**Endpoints**: `GET /api/v1/auth/orders/` (232356), `GET /api/v1/auth/orders/{id}/` (232353)
**JPA Entities exercised**: Order (6168), OrderProduct (17266), OrderStatusHistory (16233)
**Steps**:
1. GET /api/v1/auth/orders/ — assert HTTP 200, assert order list contains created order
2. GET /api/v1/auth/orders/{orderId}/ — assert HTTP 200, assert order details correct

---

## Phase 3: Cloud Storage Integration Tests

### Task 3.1 — AWS S3 File Upload (SDK Migration Validation)
**Dependency**: Task 0.1 (S3 credentials configured)
**Endpoint**: `POST /api/v1/private/file/`
**CAST Transaction**: (page 2 of Shopizer-3.2.5 transactions), full graph=219
**Technologies**: aws sdk s3 for java (migrated from aws s3)
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/content/ContentApi.java`
**Spring Beans**: awsAssetsManager (21259), awsContentAssetsManager (21147), awsProductAssetsManager (21164)
**Steps**:
1. POST multipart file upload to `/api/v1/private/file/`
2. Assert HTTP 200
3. Assert file stored in S3 test bucket
4. Verify no `aws s3` (old SDK) class references at runtime

### Task 3.2 — AWS S3 Content List
**Dependency**: Task 3.1
**Endpoint**: `GET /api/v1/private/content/list/`
**CAST Transaction**: Shopizer-3.2.5 (page 2), full graph=269
**Technologies**: aws sdk s3 for java
**Steps**:
1. GET /api/v1/private/content/list/
2. Assert HTTP 200
3. Assert uploaded file appears in list

### Task 3.3 — GCP Storage Image Serving (SDK Migration Validation)
**Dependency**: Task 0.1 (GCP credentials configured)
**Endpoints**: `GET /static/products/{}/{}/{}/` (232250), `GET /static/files/{}/{}/` (232255)
**Technologies**: google cloud storage for java (migrated from gcp storage)
**File**: `§{main_sources}§/shopizer-3.2.5/sm-shop/src/main/java/com/salesmanager/shop/controller/ImagesController.java`
**Steps**:
1. Upload a test product image via POST /api/v1/auth/product/{id}/image/ (232191)
2. GET /static/products/{storeCode}/{productId}/{imageName}
3. Assert HTTP 200 and image bytes returned
4. Verify no `gcp storage` (old SDK) class references at runtime

### Task 3.4 — Azure SDK Absence Validation
**Dependency**: Task 0.1
**Context**: Pre-migration shipping transaction (236552) used `azure sdk for java`. Post-migration equivalent (232349) does not.
**Endpoint**: `GET /api/v1/auth/cart/{}/shipping/` (232349)
**Steps**:
1. GET /api/v1/auth/cart/{cartId}/shipping/ with valid cart
2. Assert HTTP 200 and shipping options returned
3. Assert no `com.azure.*` classes loaded at runtime
4. ⚠️ SME validation required: confirm shipping functionality is not degraded by Azure SDK removal

---

## Phase 4: JPA Entity Full Coverage

### Task 4.1 — Verify All 65 JPA Entities Are Exercised
**Dependency**: Tasks 2.1–2.6, 3.1–3.4
**Steps**:
1. After all smoke tests complete, query test database to confirm records exist for each entity
2. Entities requiring explicit test coverage (not covered by other tasks):
   - TaxRate (no ID — truncated): via `POST /api/v1/private/tax/rate/`
   - GeoZone (17698): via `GET /api/v1/country/` (232308)
   - Language (17544): via `GET /api/v1/country/` (returns language data)
   - Currency (17724): via `GET /api/v1/currency/` (232306)
   - Permission (17916): via `POST /api/v1/private/user/` (page 3)
   - Group (17917): via `POST /api/v1/private/user/`
   - Manufacturer (17946): via `POST /api/v1/private/manufacturer/` (page 2)
   - ProductVariant entities: via `POST /api/v2/private/product/{}/variant/` (232159)

---

## Phase 5: Security Finding Triage

### Task 5.1 — Triage XSS Findings (73 objects, rule 8482)
**Dependency**: None (can run in parallel)
**CAST Finding**: rule 8482 "Avoid cross-site scripting through API requests" — 73 objects in Shopizer-3.2.5
**Steps**:
1. Export the 73 affected objects from CAST (query: `quality_insights` / application=Shopizer-3.2.5 / nature=structural-flaws)
2. For each affected object, determine if the XSS path was present in pre-migration Shopizer (rule 8482 was absent from pre-migration findings)
3. ⚠️ SME validation required: determine if these are newly introduced vulnerabilities or newly detected pre-existing issues
4. If newly introduced: block production deployment until remediated
5. If pre-existing: document as known risk and create remediation backlog items

### Task 5.2 — Triage Reflected XSS Findings (2 objects, rule 8408)
**Dependency**: None
**CAST Finding**: rule 8408 "Avoid reflected cross-site scripting (non-persistent)" — 2 objects in Shopizer-3.2.5
**Steps**:
1. Identify the 2 affected objects
2. Determine if these are in the migrated code path or pre-existing
3. Apply output encoding remediation per CAST remediation guidance (use `StringEscapeUtils.escapeHtml4()` or equivalent)

### Task 5.3 — Verify SQL-in-Loop Remediation
**Dependency**: None
**Context**: Pre-migration Shopizer had 3 objects violating rule 1025056 (SQL in loop). Post-migration Shopizer-3.2.5 does not show this finding.
**Steps**:
1. Confirm rule 1025056 is absent from Shopizer-3.2.5 structural flaws
2. ⚠️ SME validation required: confirm this is due to code remediation, not a change in detection scope

---

## Phase 6: Regression Validation

### Task 6.1 — Element Count Delta Investigation
**Dependency**: Tasks 2.1–4.1
**Context**: Element count increased from 16,468 (Shopizer) to 16,572 (Shopizer-3.2.5), a delta of +104 elements
**Steps**:
1. ⚠️ SME validation required: identify which 104 new elements were added
2. Confirm new elements are intentional (new features, not migration artifacts)
3. Document findings

### Task 6.2 — Interaction Count Delta Investigation
**Dependency**: Tasks 2.1–4.1
**Context**: Interaction count decreased from 72,524 (Shopizer) to 72,325 (Shopizer-3.2.5), a delta of −199 interactions
**Steps**:
1. ⚠️ SME validation required: identify which 199 interactions were removed
2. Confirm removed interactions are intentional (Azure SDK removal accounts for some)
3. Document findings

### Task 6.3 — Full Regression Test Suite Execution
**Dependency**: All Phase 1–5 tasks
**Steps**:
1. Execute all 324 transaction smoke tests
2. Record pass/fail for each transaction
3. Acceptance threshold: 100% of P1 transactions pass, ≥95% of all transactions pass
4. Document any failures with CAST transaction IDs for root cause analysis

---

## Task Dependency Order

```
0.1 → 0.2 → 0.3
0.3 → 1.1 → 1.3
0.3 → 1.2
0.3 → 1.4
1.1 → 2.1 → 2.2 → 2.3
1.2 → 2.4
0.3 → 2.5
1.1 + 2.2 → 2.6
0.1 → 3.1 → 3.2
0.1 → 3.3
0.1 → 3.4
2.1–2.6 + 3.1–3.4 → 4.1
5.1, 5.2, 5.3 (parallel)
4.1 + 5.1–5.3 → 6.1 → 6.2 → 6.3
```
