# Shopizer — Integration Smoke Test & Regression Validation: Implementation Plan

## ⚠️ BCM Compliance Gap
No BCM scope was provided. This plan covers the full application. Flag for resolution before production gate.

---

## Phase 1: Test Infrastructure Setup

### 1.1 Test Framework Selection
⚠️ Build tool not confirmed by CAST (packages query returned no results). The source path structure (`sm-core-model/`, `sm-core/`, `sm-shop/`) is consistent with a Maven multi-module layout. SME validation required to confirm Maven vs. Gradle.

Recommended test stack (⚠️ proposal — not confirmed by CAST):
- JUnit 5 for unit/integration test runner
- Spring Boot Test (`@SpringBootTest`) for integration context loading
- RestAssured or MockMvc for HTTP-layer testing
- Testcontainers for database isolation

### 1.2 Module Scope
✅ Three source modules confirmed by CAST file paths:
- `sm-core-model` — entity layer (70 JPA entities)
- `sm-core` — service layer (100+ Spring Beans)
- `sm-shop` — API layer (150+ Spring MVC operations)

Test classes should mirror this module structure.

---

## Phase 2: Smoke Test Implementation

### 2.1 Application Context Smoke Test
Verify Spring context loads without errors. This exercises all 100+ Spring Beans registered in:
- ✅ `sm-shop/src/main/java/com/salesmanager/shop/application/config/ShopApplicationConfiguration.java`
- ✅ `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java`
- ✅ `sm-core/src/main/resources/spring/shopizer-core-cms.xml`
- ✅ `sm-core/src/main/resources/spring/shopizer-core-modules.xml`
- ✅ `sm-core/src/main/resources/spring/shopizer-core-config.xml`
- ✅ `sm-shop/src/main/resources/spring/shopizer-servlet-context.xml`

### 2.2 Critical Path Smoke Tests
Execute HTTP calls against the 10 P1/P2 endpoints identified in the spec. Expected outcomes:

| Endpoint | Expected Status | Notes |
|----------|----------------|-------|
| POST `/api/v1/private/login/` | 200 | Returns JWT |
| POST `/api/v1/customer/login/` | 200 | Returns JWT |
| GET `/api/v1/category/` | 200 | Catalog listing |
| POST `/api/v1/cart/` | 200 or 201 | Cart creation |
| GET `/api/v1/config/` | 200 | Public config |
| GET `/api/v1/country/` | 200 | Reference data |
| POST `/api/v1/cart/{}/checkout/` | 200 or 400 | Requires valid cart |
| POST `/api/v1/customer/register/` | 200 or 201 | Customer creation |
| GET `/api/v1/private/orders/` | 200 | Admin orders |
| PUT `/api/v1/private/store/{}/` | 200 | Store update |

---

## Phase 3: Regression Test Implementation

### 3.1 API Namespace Coverage
Organize regression tests by namespace. All 150+ Spring MVC operations must be covered:

**Public APIs** (~30 operations):
- Cart CRUD: 6 operations
- Checkout: 2 operations
- Category browsing: 5 operations
- Product browsing: 5 operations
- Customer auth: 5 operations
- References: 2 operations
- Content: 8 operations
- Contact/Config: 2 operations

**Authenticated Customer APIs** (~25 operations):
- Customer profile/address: 4 operations
- Cart: 3 operations
- Orders: 3 operations
- Products/Reviews: 8 operations
- Token refresh: 2 operations

**Private Admin APIs** (~95+ operations):
- Store management: 8 operations
- Product administration: 15+ operations
- Customer administration: 8 operations
- Order administration: 12 operations
- Payment/Shipping modules: 8 operations
- Tax: 10 operations
- User management: 8 operations
- Content administration: 12 operations
- Manufacturer: 6 operations
- Marketplace: 1 operation
- Cache: 1 operation

### 3.2 JPA Entity Coverage
All 70 JPA entities must be exercised through the API layer. Key entity-to-API mappings:

| Entity Domain | Entities | Primary API Path |
|--------------|----------|-----------------|
| Catalog | 21 entities | `/api/v1/product/`, `/api/v1/category/` |
| Order | 12 entities | `/api/v1/auth/orders/`, `/api/v1/private/orders/` |
| Customer | 10 entities | `/api/v1/customer/`, `/api/v1/auth/customer/` |
| Merchant | 6 entities | `/api/v1/private/store/` |
| Reference | 7 entities | `/api/v1/country/`, `/api/v1/currency/` |
| Shopping | 5 entities | `/api/v1/cart/` |
| User | 3 entities | `/api/v1/private/user/` |
| Tax | 1 entity | `/api/v1/private/tax/` |
| Optin | 2 entities | `/api/v1/private/optin/` |

### 3.3 Structural Flaw Regression Tests
✅ CAST identified 2 structural flaw rules with 5 total affected objects:
- **SQL in loop** (3 objects): Write performance tests that detect N+1 query patterns. Use query counting interceptors.
- **Empty catch blocks** (2 objects): Write tests that trigger the code paths containing empty catch blocks and verify that errors are not silently swallowed.

---

## Phase 4: Cloud Readiness Validation

### 4.1 Security Regression
✅ CAST identified 29 objects with "unsecured data string" (Critical). Tests must:
- Document all 29 as known issues in a test report
- Assert no new instances are introduced by running CAST scan post-test

### 4.2 Environment Configuration Tests
✅ CAST identified 11 objects accessing environment variables and 10 objects with hardcoded HTTP URLs. Tests must:
- Verify application starts correctly with environment variables set
- Verify no hardcoded URLs cause failures in non-default environments

---

## Rollback Strategy

⚠️ No deployment pipeline details available from CAST. The following is a proposal:
1. Tag the current CAST snapshot (Shopizer, delivery 2026-07-10) as the regression baseline
2. If any smoke test fails post-deployment, revert to the baseline snapshot
3. Re-run CAST analysis after any rollback to confirm structural flaw counts have not increased
4. The Shopizer-3.2.5 snapshot (delivery 2026-07-30) serves as the forward-looking comparison baseline

---

## Dependency Upgrade Table
Not applicable — no framework upgrade is specified in the Requirement Document. (Source: Requirement Document — "Tech debt: [none specified]")
