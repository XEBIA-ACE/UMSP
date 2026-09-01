# Implementation Plan: Full Integration Testing and Migration Validation — Shopizer-3.2.5

## BCM Scope Notice
⚠️ **Standing Compliance Gap (GR-08)**: No BCM subsystem was provided. All planning is application-wide.

---

## 1. Overview

This plan establishes a phased approach to full integration testing and migration validation for Shopizer-3.2.5. The application is a multi-module Maven Java e-commerce platform with 91,162 LOC, 16,572 elements, 324 REST endpoints, 63 JPA entities, and confirmed integrations with AWS S3, Google Cloud Storage, and AWS SES. ✅

The Requirement Document specifies medium upgrade urgency with no specific target version. This plan addresses the current structural state and prepares the application for any future migration.

---

## 2. Phased Migration Strategy

### Phase 1: Baseline Assessment and Test Infrastructure (Weeks 1–2)

**Objective**: Establish test infrastructure and baseline quality metrics.

**Actions**:
1. Set up integration test environment for all 5 Maven modules ✅ (sm-core-model, sm-core, sm-core-modules, sm-shop-model, sm-shop)
2. Configure test profiles using the 42 confirmed properties files ✅
3. Establish baseline CAST quality scores for the 3 confirmed structural flaw rules ✅
4. Set up CI pipeline with `mvn verify` across all modules

**Deliverables**:
- Working test environment for all 5 modules
- Baseline quality report (3 structural flaw rules, 77 total violations)

### Phase 2: Security Remediation (Weeks 2–4)

**Objective**: Address the 77 confirmed security violations before migration.

**Actions**:
1. Remediate 73 XSS-via-API-requests violations (rule 8482) across Spring MVC controllers ✅
2. Remediate 2 reflected XSS violations (rule 8408) ✅
3. Remediate 2 empty catch block violations (rule 1060020) ✅
4. Re-run CAST analysis to confirm remediation

**Priority files** (from CAST quality findings):
- Spring MVC controllers in `sm-shop/src/main/java/com/salesmanager/shop/store/api/`
- Focus on controllers with user-input handling

### Phase 3: JPA Entity Integration Tests (Weeks 3–5)

**Objective**: Full CRUD test coverage for all 63 JPA entities.

**Actions**:
1. Write repository integration tests for all 63 JPA entities ✅
2. Priority order (by business criticality):
   - Order domain: Order (6168), OrderProduct (17266), OrderTotal (6141), OrderProductPrice (16251)
   - Customer domain: Customer (7189), CustomerReview (17519)
   - Catalog domain: Product (17941), ProductAvailability (17934), ProductPrice (17930)
   - Merchant domain: MerchantStore (6285), MerchantConfiguration (14867)
3. Validate CRUD interactions (select, insert, update, delete confirmed) ✅
4. Test all 13 database.properties profile variants ✅

### Phase 4: API Integration Tests (Weeks 4–8)

**Objective**: Integration test coverage for all 324 Spring MVC endpoints.

**Actions**:
1. Prioritize by transaction complexity (full-graph size):
   - `api/v1/cart/{}/checkout/` (transaction 232211, full-graph 3,281) ✅
   - `api/v1/auth/cart/{}/checkout/` (transaction 232212, full-graph 3,264) ✅
   - `api/v1/customer/register/` (transaction 232221, full-graph 3,093) ✅
   - `api/v1/category/` (transaction 232387, full-graph 2,972) ✅
2. Test all 3 API versions (v0, v1, v2)
3. Test authentication flows (JWT via AuthenticateUserApi, AuthenticateCustomerApi)
4. Test multi-entry-point security (MultipleEntryPointsSecurityConfig) ✅

**API test groupings** (by controller file):
- Order APIs: OrderApi, OrderPaymentApi, OrderShippingApi, OrderTotalApi, OrderStatusHistoryApi
- Product APIs: ProductApi, ProductImageApi, ProductReviewApi, ProductManufacturerApi, ProductInventoryApi, ProductPriceApi, ProductGroupApi
- Customer APIs: CustomerApi, AuthenticateCustomerApi, CustomerReviewApi, ResetCustomerPasswordApi
- Cart APIs: ShoppingCartApi
- Category APIs: CategoryApi
- Content APIs: ContentApi, ContentAdministrationApi
- Store APIs: MerchantStoreApi
- User APIs: UserApi, AuthenticateUserApi
- Tax APIs: TaxClassApi, TaxRatesApi
- Shipping APIs: ShippingConfigurationApi, ShippingExpeditionApi
- Payment APIs: PaymentApi
- V2 APIs: ProductApiV2, ProductVariantApi, ProductVariantGroupApi, ProductVariationApi

### Phase 5: Cloud Integration Tests (Weeks 6–8)

**Objective**: Validate AWS S3, Google Cloud Storage, and AWS SES integrations.

**Actions**:
1. Test AWS S3 beans: awsAssetsManager (21259), awsContentAssetsManager (21147), awsDownloadsManager (21129), awsProductAssetsManager (21164) ✅
2. Test Google Cloud Storage beans (GCP profile) ✅
3. Test AWS SES email: sesEmailSender (21237) ✅
4. Validate all cloud-specific properties profiles (aws, gcp, cloud, docker, dependency)

### Phase 6: Namespace/Framework Migration (If Applicable) (Weeks 8–12)

**Objective**: ⚠️ Proposal — Execute only if a specific framework upgrade is confirmed by SME.

**Actions** (⚠️ proposals pending SME confirmation of target version):
1. If Spring Boot 3.x migration: audit all `javax.*` imports across 63 JPA entities and all Spring MVC controllers
2. If Spring Boot 3.x migration: migrate `javax.persistence.*` → `jakarta.persistence.*` in all 63 JPA entity files
3. If Spring Boot 3.x migration: migrate `javax.servlet.*` → `jakarta.servlet.*` in all Spring MVC controllers
4. Update all 5 `pom.xml` files (one per module) with new dependency versions ⚠️
5. Validate all 42 properties files for deprecated configuration keys ⚠️

> **SME Validation Required**: The exact count of files requiring namespace migration cannot be confirmed without a targeted CAST query for `javax` import usage. This was not run in this session.

---

## 3. Dependency Upgrade Table

⚠️ **Not available from CAST MCP** — the `packages` query returned "No packages in this application." Specific dependency versions (Spring Boot, Hibernate, etc.) cannot be confirmed from CAST. SME must provide the current `pom.xml` dependency list.

| Dependency | Current Version | Target Version | Status |
|---|---|---|---|
| Spring Boot | Unknown | Unknown | ⚠️ SME required |
| Hibernate | Confirmed present | Unknown | ⚠️ SME required |
| JPA | Confirmed present | Unknown | ⚠️ SME required |
| AWS SDK S3 | Confirmed present | Unknown | ⚠️ SME required |
| Google Cloud Storage | Confirmed present | Unknown | ⚠️ SME required |

---

## 4. Component Changes (CAST-Derived)

| Component | Change Required | CAST Evidence |
|---|---|---|
| 73 Spring MVC controllers/methods | XSS remediation (rule 8482) | ✅ CAST quality_insights |
| 2 methods | Reflected XSS remediation (rule 8408) | ✅ CAST quality_insights |
| 2 methods | Empty catch block remediation (rule 1060020) | ✅ CAST quality_insights |
| 63 JPA entity files | Integration test coverage | ✅ CAST objects query |
| 324 Spring MVC endpoints | Integration test coverage | ✅ CAST objects query |
| 42 properties files | Environment validation | ✅ CAST objects query |
| 5 Maven modules | Build validation | ✅ CAST file paths |

---

## 5. Rollback Strategy

⚠️ Specific rollback procedures depend on the target version, which was not specified in the Requirement Document. The following general strategy applies:

1. **Git branching**: All migration work on a dedicated branch; main branch remains deployable
2. **Module-by-module**: Migrate and test one Maven module at a time (sm-core-model first, sm-shop last)
3. **Properties file backup**: All 42 properties files backed up before modification
4. **Database schema**: No schema changes expected from integration testing alone; if namespace migration occurs, Hibernate DDL validation required
5. **Rollback trigger**: Any failure in Phase 3 (JPA entity tests) or Phase 4 (API tests) triggers rollback to last known-good state

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| javax→jakarta migration scope unknown | Medium | High | Run targeted CAST query for javax imports before Phase 6 |
| 73 XSS violations require significant refactoring | High | Medium | Prioritize in Phase 2; may require output encoding library |
| Drools integration (droolsBeanFactory) may break on upgrade | Low | Medium | ⚠️ SME validation required |
| Cloud integration tests require live AWS/GCP credentials | High | Medium | Use mock/stub for unit tests; live credentials for integration tests only |
| Spring Boot version unknown | High | High | SME must confirm current and target versions before Phase 6 |
