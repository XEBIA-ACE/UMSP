# Tasks: Full Integration Testing and Migration Validation — Shopizer-3.2.5

## BCM Scope Notice
⚠️ **Standing Compliance Gap (GR-08)**: No BCM subsystem was provided. All tasks are application-wide.

---

## Phase 1: Build Configuration and Test Infrastructure

### Task 1.1 — Verify Multi-Module Build
**Description**: Confirm all 5 Maven modules build cleanly.
**Files**: `sm-core-model/pom.xml`, `sm-core/pom.xml`, `sm-core-modules/pom.xml`, `sm-shop-model/pom.xml`, `sm-shop/pom.xml`
**Steps**:
1. Run `mvn clean verify` from root
2. Confirm all 5 modules pass
3. Document any existing test failures as baseline
**CAST Evidence**: 5 maven-wrapper.properties files confirmed (IDs: 8497, 8528, 12906, 13264, 13347) ✅
**Acceptance**: `mvn clean verify` exits 0 for all modules

### Task 1.2 — Configure Test Database Profiles
**Description**: Validate all 13 database.properties profile variants are functional.
**Files**:
- `sm-shop/src/main/resources/database.properties` (ID: 7318)
- `sm-shop/src/main/resources/profiles/docker/database.properties` (ID: 6643)
- `sm-shop/src/main/resources/profiles/dependency/database.properties` (ID: 6661)
- `sm-shop/src/main/resources/profiles/cloud/database.properties` (ID: 7067)
- `sm-shop/src/main/resources/profiles/mysql/database.properties` (ID: 25016)
- `sm-shop/src/main/resources/profiles/local/database.properties` (ID: 25042)
- `sm-shop/src/main/resources/profiles/gcp/database.properties` (ID: 25069)
- `sm-shop/src/test/resources/database.properties` (ID: 25111)
- `sm-core/src/test/resources/database.properties` (ID: 9485)
- (plus 4 additional database.properties files)
**Steps**:
1. Verify each profile connects to its target database
2. Confirm H2/in-memory database is configured for test profiles
**Acceptance**: All 13 database.properties files load without errors in their respective profiles

### Task 1.3 — Configure Test Application Properties
**Description**: Validate test-specific properties files.
**Files**:
- `sm-shop/src/test/resources/application-test.properties` (ID: 25112)
- `sm-shop/src/main/resources/application.properties` (ID: 8412)
- `sm-core/src/test/resources/application.properties` (ID: 9513)
**Steps**:
1. Confirm `spring.profiles.active=test` activates `application-test.properties`
2. Verify test properties override production values correctly
**Acceptance**: Test context loads with test properties

---

## Phase 2: Security Remediation

### Task 2.1 — Remediate XSS via API Requests (73 objects)
**Description**: Fix 73 objects violating CAST rule 8482 (cross-site scripting through API requests).
**CAST Rule**: 8482 — "Avoid cross-site scripting through API requests"
**Affected Count**: 73 objects ✅ (Source: CAST MCP — quality_insights / rule 8482)
**Files**: Spring MVC controllers in `sm-shop/src/main/java/com/salesmanager/shop/store/api/`
**Steps**:
1. Run CAST quality_insights for rule 8482 to get the specific object list
2. For each affected object, apply output encoding using `StringEscapeUtils.escapeHtml4()` (per CAST remediation sample)
3. Add `jakarta.servlet.http.HttpServletResponse` output encoding where applicable
4. Write unit tests for each remediated method
**Acceptance**: CAST re-scan shows 0 violations for rule 8482

### Task 2.2 — Remediate Reflected XSS (2 objects)
**Description**: Fix 2 objects violating CAST rule 8408 (reflected cross-site scripting).
**CAST Rule**: 8408 — "Avoid reflected cross-site scripting (non persistent)"
**Affected Count**: 2 objects ✅ (Source: CAST MCP — quality_insights / rule 8408)
**Steps**:
1. Run CAST quality_insights for rule 8408 to get the specific object list
2. Apply HTML entity encoding to all user-controlled input before output
3. Write unit tests for each remediated method
**Acceptance**: CAST re-scan shows 0 violations for rule 8408

### Task 2.3 — Remediate Empty Catch Blocks (2 objects)
**Description**: Fix 2 methods violating CAST rule 1060020 (empty catch blocks with high fan-in).
**CAST Rule**: 1060020 — "Avoid empty catch blocks for methods with high fan-in"
**Affected Count**: 2 objects ✅ (Source: CAST MCP — quality_insights / rule 1060020)
**Steps**:
1. Run CAST quality_insights for rule 1060020 to get the specific object list
2. Add proper exception handling (logging at minimum, re-throw if appropriate)
3. Write unit tests covering the exception paths
**Acceptance**: CAST re-scan shows 0 violations for rule 1060020

---

## Phase 3: JPA Entity Integration Tests

### Task 3.1 — Order Domain Entity Tests (11 entities)
**Description**: Write CRUD integration tests for all Order domain JPA entities.
**Entities and CAST IDs**:
- Order (ID: 6168) — `sm-core-model/.../order/Order.java`
- OrderTotal (ID: 6141) — `sm-core-model/.../order/OrderTotal.java`
- OrderProduct (ID: 17266) — `sm-core-model/.../order/orderproduct/OrderProduct.java`
- OrderProductAttribute (ID: 17203) — `sm-core-model/.../order/orderproduct/OrderProductAttribute.java`
- OrderProductDownload (ID: 16579) — `sm-core-model/.../order/orderproduct/OrderProductDownload.java`
- OrderProductPrice (ID: 16251) — `sm-core-model/.../order/orderproduct/OrderProductPrice.java`
- OrderStatusHistory (ID: 16233) — `sm-core-model/.../order/orderstatus/OrderStatusHistory.java`
- OrderAttribute (ID: 17848) — `sm-core-model/.../order/attributes/OrderAttribute.java`
- OrderAccount (ID: 17730) — `sm-core-model/.../order/orderaccount/OrderAccount.java`
- OrderAccountProduct (ID: 17672) — `sm-core-model/.../order/orderaccount/OrderAccountProduct.java`
- FileHistory (ID: 17761) — `sm-core-model/.../order/filehistory/FileHistory.java`
**Steps**:
1. Create `OrderRepositoryIntegrationTest` in `sm-core/src/test/java/`
2. Test create, read, update, delete for each entity
3. Test relationships between Order → OrderProduct → OrderProductPrice
**Acceptance**: All 11 entity CRUD tests pass

### Task 3.2 — Customer Domain Entity Tests (9 entities)
**Description**: Write CRUD integration tests for all Customer domain JPA entities.
**Entities and CAST IDs**:
- Customer (ID: 7189) — `sm-core-model/.../customer/Customer.java`
- CustomerAttribute (ID: 17830)
- CustomerOption (ID: 17677)
- CustomerOptionDescription (ID: 17662)
- CustomerOptionSet (ID: 17786)
- CustomerOptionValue (ID: 17771)
- CustomerOptionValueDescription (ID: 17755)
- CustomerReview (ID: 17519)
- CustomerReviewDescription (ID: 16902)
**Steps**:
1. Create `CustomerRepositoryIntegrationTest` in `sm-core/src/test/java/`
2. Test CRUD for each entity
3. Test Customer → CustomerAttribute relationship
**Acceptance**: All 9 entity CRUD tests pass

### Task 3.3 — Catalog/Product Domain Entity Tests (23 entities)
**Description**: Write CRUD integration tests for all Catalog domain JPA entities.
**Entities and CAST IDs**:
- Product (ID: 17941), ProductAttribute (ID: 17940), ProductAvailability (ID: 17934)
- ProductDescription (ID: 17933), ProductImage (ID: 17948), ProductImageDescription (ID: 17947)
- ProductOption (ID: 17939), ProductOptionDescription (ID: 17938), ProductOptionSet (ID: 17937)
- ProductOptionValue (ID: 17936), ProductOptionValueDescription (ID: 17935)
- ProductPrice (ID: 17930), ProductPriceDescription (ID: 17929)
- ProductRelationship (ID: 17928), ProductReview (ID: 17927), ProductReviewDescription (ID: 17926)
- DigitalProduct (ID: 17932), Manufacturer (ID: 17946), ManufacturerDescription (ID: 17931)
- Catalog (ID: 17945), CatalogCategoryEntry (ID: 17944)
- Category (ID: 17943), CategoryDescription (ID: 17942)
**Steps**:
1. Create `ProductRepositoryIntegrationTest` and `CatalogRepositoryIntegrationTest`
2. Test CRUD for each entity
3. Test Product → ProductAvailability → ProductPrice chain
**Acceptance**: All 23 entity CRUD tests pass

### Task 3.4 — Merchant/System Domain Entity Tests (10 entities)
**Description**: Write CRUD integration tests for Merchant and System domain JPA entities.
**Entities and CAST IDs**:
- MerchantStore (ID: 6285) — `sm-core-model/.../merchant/MerchantStore.java`
- MerchantConfiguration (ID: 14867)
- MerchantLog (ID: 14673)
- IntegrationModule (ID: 14882)
- Optin (ID: 17886)
- CustomerOptin (ID: 17901)
- SystemConfiguration (no ID returned — `sm-core-model/.../system/SystemConfiguration.java`)
- SystemNotification (no ID returned — `sm-core-model/.../system/SystemNotification.java`)
- Permission (ID: 17916)
- Group (ID: 17917)
**Steps**:
1. Create `MerchantRepositoryIntegrationTest` and `SystemRepositoryIntegrationTest`
2. Test CRUD for each entity
**Acceptance**: All 10 entity CRUD tests pass

### Task 3.5 — Reference Domain Entity Tests (10 entities)
**Description**: Write CRUD integration tests for Reference domain JPA entities.
**Entities and CAST IDs**:
- Country (ID: 16017), CountryDescription (ID: 16000)
- Currency (ID: 17724)
- GeoZone (ID: 17698), GeoZoneDescription (ID: 17647)
- Language (ID: 17544)
- User (no ID returned — `sm-core-model/.../user/User.java`)
- TaxRate (no ID returned — `sm-core-model/.../tax/taxrate/TaxRate.java`)
- Transaction (no ID returned — `sm-core-model/.../payments/Transaction.java`)
- CustomerOptin (ID: 17901)
**Steps**:
1. Create `ReferenceRepositoryIntegrationTest`
2. Test CRUD for each entity
**Acceptance**: All 10 entity CRUD tests pass

---

## Phase 4: API Integration Tests

### Task 4.1 — Checkout Flow Integration Tests (Highest Priority)
**Description**: Integration tests for the two checkout endpoints (largest call graphs).
**Endpoints**:
- `POST api/v1/cart/{}/checkout/` (transaction ID: 232211, full-graph: 3,281 objects) ✅
- `POST api/v1/auth/cart/{}/checkout/` (transaction ID: 232212, full-graph: 3,264 objects) ✅
**Files**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderApi.java`
**Steps**:
1. Create `CheckoutApiIntegrationTest` in `sm-shop/src/test/java/`
2. Test anonymous checkout (`api/v1/cart/{}/checkout/`)
3. Test authenticated checkout (`api/v1/auth/cart/{}/checkout/`)
4. Test with valid cart, payment, and shipping data
5. Verify Order entity (ID: 6168) is persisted after checkout
**Acceptance**: Both checkout endpoints return 200/201 with valid order response

### Task 4.2 — Customer Registration Integration Tests
**Description**: Integration tests for customer registration (3rd largest call graph).
**Endpoint**: `POST api/v1/customer/register/` (transaction ID: 232221, full-graph: 3,093 objects) ✅
**File**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/AuthenticateCustomerApi.java`
**Steps**:
1. Create `CustomerRegistrationIntegrationTest`
2. Test successful registration
3. Test duplicate email rejection
4. Test invalid input validation
5. Verify Customer entity (ID: 7189) is persisted
**Acceptance**: Registration endpoint returns 201 for valid input, 4xx for invalid

### Task 4.3 — Category API Integration Tests
**Description**: Integration tests for category listing endpoints (large call graphs).
**Endpoints**:
- `GET api/v1/category/` (transaction ID: 232387, full-graph: 2,972) ✅
- `GET api/v1/category/{}/` (transaction ID: 232390, full-graph: 2,936) ✅
- `GET api/v1/category/product/{}/` (transaction ID: 232386, full-graph: 2,935) ✅
- `GET api/v1/category/{}/manufacturer/` (transaction ID: 232321, full-graph: 2,933) ✅
**File**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/CategoryApi.java`
**Steps**:
1. Create `CategoryApiIntegrationTest`
2. Test all 4 category GET endpoints
3. Verify Category (ID: 17943) and Product (ID: 17941) data is returned
**Acceptance**: All category endpoints return 200 with valid JSON

### Task 4.4 — Shopping Cart API Integration Tests
**Description**: Integration tests for shopping cart operations.
**Endpoints** (from ShoppingCartApi.java):
- `POST api/v1/cart/` (transaction ID: 232152)
- `GET api/v1/cart/{}/` (transaction ID: 232293)
- `PUT api/v1/cart/{}/` (transaction ID: 232119)
- `DELETE api/v1/cart/{}/product/{}/` (transaction ID: 232407)
- `POST api/v1/cart/{}/multi/` (transaction ID: 232173)
- `POST api/v1/cart/{}/promo/{}/` (transaction ID: 232174)
**File**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java`
**Steps**:
1. Create `ShoppingCartApiIntegrationTest`
2. Test full cart lifecycle: create → add items → update → checkout
**Acceptance**: All cart endpoints return expected HTTP status codes

### Task 4.5 — Authentication Integration Tests
**Description**: Integration tests for JWT authentication flows.
**Endpoints**:
- `POST api/v1/private/login/` (AuthenticateUserApi)
- `POST api/v1/customer/login/` (AuthenticateCustomerApi)
- `GET api/v1/auth/refresh/` (transaction ID: 232275)
- `GET api/v1/auth/customer/refresh/` (transaction ID: 232366)
**Files**:
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/user/AuthenticateUserApi.java` (bean ID: 21326)
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/AuthenticateCustomerApi.java`
- `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java`
**Steps**:
1. Create `AuthenticationIntegrationTest`
2. Test admin login → JWT token → authenticated request
3. Test customer login → JWT token → authenticated request
4. Test token refresh
5. Test invalid credentials rejection
**Acceptance**: Authentication flows return valid JWT tokens; protected endpoints reject unauthenticated requests

### Task 4.6 — Product API Integration Tests
**Description**: Integration tests for product management endpoints.
**Files**: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductApi.java`
**Key endpoints**: `POST api/v1/auth/products/`, `PUT api/v1/auth/product/{}/`, `DELETE api/v1/auth/product/{}/`
**Steps**:
1. Create `ProductApiIntegrationTest`
2. Test product create, update, delete
3. Test product image upload (`POST api/v1/auth/product/{}/image/`)
4. Verify Product entity (ID: 17941) persistence
**Acceptance**: Product CRUD endpoints return expected responses

### Task 4.7 — Remaining API Integration Tests (v0, v1 remaining, v2)
**Description**: Integration tests for all remaining 324 - (covered above) endpoints.
**Files**: All remaining API files in `sm-shop/src/main/java/com/salesmanager/shop/store/api/`
**Steps**:
1. Create test classes for each remaining API controller
2. Cover: TaxClassApi, TaxRatesApi, ShippingConfigurationApi, ShippingExpeditionApi, PaymentApi, MerchantStoreApi, UserApi, ContentApi, ContentAdministrationApi
3. Cover v2 APIs: ProductApiV2, ProductVariantApi, ProductVariantGroupApi, ProductVariationApi
4. Cover v0 legacy APIs: SystemRESTController, StoreContactRESTController
**Acceptance**: All 324 Spring MVC endpoints have at least one integration test

---

## Phase 5: Cloud Integration Tests

### Task 5.1 — AWS S3 Integration Tests
**Description**: Validate AWS S3 asset management beans.
**Spring Beans**:
- awsAssetsManager (ID: 21259) — `sm-core/src/main/resources/spring/shopizer-core-cms.xml`
- awsContentAssetsManager (ID: 21147) — `sm-core/src/main/resources/spring/shopizer-core-cms.xml`
- awsDownloadsManager (ID: 21129) — `sm-core/src/main/resources/spring/shopizer-core-cms.xml`
- awsProductAssetsManager (ID: 21164) — `sm-core/src/main/resources/spring/shopizer-core-cms.xml`
**Properties**: `sm-core/src/main/resources/profiles/aws/shopizer-core.properties` (ID: 12570)
**Steps**:
1. Create `AWSS3IntegrationTest` using test S3 bucket or LocalStack
2. Test file upload, download, delete for each asset manager bean
3. Validate `Java AWS S3 Bucket` and `Java AWS Unknown S3 Bucket` element types ✅
**Acceptance**: All 4 AWS S3 beans pass upload/download/delete tests

### Task 5.2 — Google Cloud Storage Integration Tests
**Description**: Validate GCP storage integration.
**Properties**: `sm-core/src/main/resources/profiles/gcp/shopizer-core.properties` (ID: 10244)
**Steps**:
1. Create `GCPStorageIntegrationTest` using test GCS bucket or emulator
2. Test file operations for GCP storage beans
3. Validate `Java GCP Cloud Storage Bucket` element type ✅
**Acceptance**: GCP storage beans pass integration tests

### Task 5.3 — AWS SES Email Integration Tests
**Description**: Validate AWS SES email sending.
**Spring Bean**: sesEmailSender (ID: 21237) — `sm-core/.../modules/email/SESEmailSenderImpl.java`
**Properties**: `sm-core/src/main/resources/email.properties` (ID: 12588)
**Steps**:
1. Create `SESEmailIntegrationTest` using SES sandbox or mock
2. Test email send via sesEmailSender bean
3. Compare with defaultEmailSender (ID: 21239) behavior
**Acceptance**: sesEmailSender sends email without errors in test environment

---

## Phase 6: Namespace/Framework Migration (Conditional)

> ⚠️ **Execute only after SME confirms target framework version.**

### Task 6.1 — Audit javax.* Usage (Pre-Migration)
**Description**: Identify all files using `javax.*` imports before migration.
**Steps**:
1. Run CAST objects query: `annotation:contains:javax` or `fullname:contains:javax`
2. Count affected files per category (javax.persistence, javax.servlet, javax.validation, etc.)
3. Document exact count — do not proceed with migration until count is confirmed
**Acceptance**: Exact count of javax.* usages documented per category

### Task 6.2 — JPA Entity Namespace Migration (If Spring Boot 3.x)
**Description**: Migrate `javax.persistence.*` → `jakarta.persistence.*` in all 63 JPA entity files.
**Files**: All 63 JPA entity files in `sm-core-model/src/main/java/com/salesmanager/core/model/`
**Steps**:
1. For each of the 63 JPA entity files, replace `import javax.persistence.*` with `import jakarta.persistence.*`
2. Run `mvn compile` on `sm-core-model` module after each batch
3. Run JPA entity integration tests (Tasks 3.1–3.5) after all replacements
**Acceptance**: All 63 JPA entities compile and pass CRUD tests with jakarta.* imports

### Task 6.3 — Spring MVC Controller Namespace Migration (If Spring Boot 3.x)
**Description**: Migrate `javax.servlet.*` → `jakarta.servlet.*` in Spring MVC controllers.
**Files**: All Spring MVC controller files in `sm-shop/src/main/java/com/salesmanager/shop/store/api/`
**Steps**:
1. Replace `import javax.servlet.*` with `import jakarta.servlet.*` in all controller files
2. Run `mvn compile` on `sm-shop` module
3. Run API integration tests (Tasks 4.1–4.7) after all replacements
**Acceptance**: All 324 Spring MVC endpoints compile and pass integration tests with jakarta.* imports

### Task 6.4 — Build File Updates (If Version Upgrade)
**Description**: Update dependency versions in all 5 pom.xml files.
**Files**: `sm-core-model/pom.xml`, `sm-core/pom.xml`, `sm-core-modules/pom.xml`, `sm-shop-model/pom.xml`, `sm-shop/pom.xml`
**Steps**:
1. Update Spring Boot parent version (version TBD by SME)
2. Update Hibernate version if required
3. Update AWS SDK version if required
4. Update Google Cloud Storage SDK version if required
5. Run `mvn dependency:tree` to check for conflicts
6. Run full `mvn clean verify` across all 5 modules
**Acceptance**: All 5 modules build and all tests pass with updated dependencies

---

## Dependency Order

```
Task 1.1 → Task 1.2 → Task 1.3
                ↓
Task 2.1, 2.2, 2.3 (parallel)
                ↓
Task 3.1, 3.2, 3.3, 3.4, 3.5 (parallel)
                ↓
Task 4.1, 4.2, 4.3 (parallel, highest priority)
Task 4.4, 4.5, 4.6, 4.7 (parallel)
                ↓
Task 5.1, 5.2, 5.3 (parallel)
                ↓
[SME confirmation required]
                ↓
Task 6.1 → Task 6.2 → Task 6.3 → Task 6.4
```
