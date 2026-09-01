# Specification: Full Integration Testing and Migration Validation — Shopizer-3.2.5

## BCM Scope Notice (GR-08)
⚠️ **Standing Compliance Gap**: No BCM (Business Capability Model) subsystem was provided. All queries were executed application-wide across Shopizer-3.2.5. This is flagged as a standing compliance gap per GR-08 and must be resolved before this spec is used for production planning.

---

## 1. Requirement Summary

This specification covers full integration testing and migration validation for the **Shopizer-3.2.5** application. The requirement document provides the following authoritative inputs (Source: Requirement Document):

| Field | Value |
|---|---|
| Language | Unknown (Source: Requirement Document) |
| Language Latest | Unknown (Source: Requirement Document) |
| Runtime | Unknown (Source: Requirement Document) |
| Build Tool | Unknown (Source: Requirement Document) |
| Upgrade Urgency | Medium (Source: Requirement Document) |
| Tech Debt | Not specified (Source: Requirement Document) |

> **Note**: The Requirement Document did not supply specific version numbers, target versions, or explicit migration steps. CAST structural analysis was used to characterize the application's current state. All version-specific migration details are marked ⚠️ as proposals pending SME confirmation.

---

## 2. Current State (CAST-Confirmed)

### 2.1 Application Overview

The Shopizer-3.2.5 application is a Java-based e-commerce platform with the following confirmed structural profile:

- **Lines of Code**: 91,162 ✅
- **Total Elements**: 16,572 ✅
- **Total Interactions**: 72,325 ✅
- **CAST Snapshot**: Onboarding-202607301729 (delivered 2026-07-30T17:29:00) ✅

### 2.2 Technology Stack (CAST-Confirmed)

The following technologies are confirmed present in the CAST analysis:

- Java ✅
- JPA ✅
- Hibernate ✅
- Spring ✅
- Spring Web Services ✅
- Java EE ✅
- JEE ✅
- AWS SDK S3 for Java ✅
- Google Cloud Storage for Java ✅
- Java Server Pages ✅
- Java Properties ✅

### 2.3 Module Structure (CAST-Confirmed)

The application is organized as a multi-module Maven project with the following confirmed modules (inferred from file paths in CAST):

- `sm-core-model` — JPA entity model layer
- `sm-core` — Core business services and configuration
- `sm-core-modules` — Integration modules
- `sm-shop-model` — Shop model layer
- `sm-shop` — Web/API layer (Spring MVC controllers, security, facades)

Each module has its own `.mvn/wrapper/maven-wrapper.properties` file (5 maven-wrapper.properties files confirmed). ✅

### 2.4 Object Type Inventory (CAST-Confirmed)

| Object Type | Count |
|---|---|
| JPA Entity | 63 ✅ |
| JPA Entity Operation | 18 ✅ |
| Spring Bean | ≥200 (3 full pages of 100 items each; exact total not returned in metadata) ✅ |
| Spring MVC Operations (all types) | 324 ✅ |
| — Spring MVC Get Operation | (subset of 324) ✅ |
| — Spring MVC Post Operation | (subset of 324) ✅ |
| — Spring MVC Put Operation | (subset of 324) ✅ |
| — Spring MVC Delete Operation | (subset of 324) ✅ |
| — Spring MVC Any Operation | (subset of 324) ✅ |
| Java Properties File | 42 ✅ |
| J2EE Scoped Bean | 2 ✅ |
| JPQL Query | present (in element_types list) ✅ |
| JPA Unknown SQL Query | present (in element_types list) ✅ |

### 2.5 JPA Entity Catalog (CAST-Confirmed, 63 entities)

All 63 JPA entities reside in `sm-core-model/src/main/java/com/salesmanager/core/model/`:

**Catalog domain**: Catalog, CatalogCategoryEntry, Category, CategoryDescription, Product, ProductAttribute, ProductAvailability, ProductDescription, ProductImage, ProductImageDescription, ProductOption, ProductOptionDescription, ProductOptionSet, ProductOptionValue, ProductOptionValueDescription, ProductPrice, ProductPriceDescription, ProductRelationship, ProductReview, ProductReviewDescription, DigitalProduct, Manufacturer, ManufacturerDescription

**Customer domain**: Customer, CustomerAttribute, CustomerOption, CustomerOptionDescription, CustomerOptionSet, CustomerOptionValue, CustomerOptionValueDescription, CustomerReview, CustomerReviewDescription

**Order domain**: Order, OrderAccount, OrderAccountProduct, OrderAttribute, OrderProduct, OrderProductAttribute, OrderProductDownload, OrderProductPrice, OrderStatusHistory, OrderTotal, FileHistory

**Reference domain**: Country, CountryDescription, Currency, GeoZone, GeoZoneDescription, Language

**Merchant/System domain**: MerchantStore, MerchantConfiguration, MerchantLog, IntegrationModule, SystemConfiguration, SystemNotification, Optin, CustomerOptin, Permission, Group

### 2.6 Spring MVC API Surface (CAST-Confirmed)

The application exposes 324 Spring MVC operations across three API versions:
- **v0** (legacy): `services/private/...` and `services/public/...` endpoints
- **v1** (primary): `api/v1/auth/...`, `api/v1/private/...`, `api/v1/cart/...`, `api/v1/category/...`, `api/v1/customer/...`, `api/v1/content/...`, `api/v1/config/...`, `api/v1/country/...`, `api/v1/currency/...`
- **v2** (extended): `api/v2/private/product/...`, `api/v2/product/...`, `api/v2/products/...`

Key API files confirmed in `sm-shop/src/main/java/com/salesmanager/shop/store/api/`:
- `v1/order/OrderApi.java`, `OrderPaymentApi.java`, `OrderShippingApi.java`, `OrderTotalApi.java`, `OrderStatusHistoryApi.java`
- `v1/product/ProductApi.java`, `ProductImageApi.java`, `ProductReviewApi.java`, `ProductManufacturerApi.java`, `ProductInventoryApi.java`, `ProductPriceApi.java`, `ProductGroupApi.java`
- `v1/customer/CustomerApi.java`, `AuthenticateCustomerApi.java`, `CustomerReviewApi.java`, `ResetCustomerPasswordApi.java`
- `v1/shoppingCart/ShoppingCartApi.java`
- `v1/category/CategoryApi.java`
- `v1/content/ContentApi.java`, `ContentAdministrationApi.java`
- `v1/store/MerchantStoreApi.java`
- `v1/user/UserApi.java`, `AuthenticateUserApi.java`
- `v1/tax/TaxClassApi.java`, `TaxRatesApi.java`
- `v1/shipping/ShippingConfigurationApi.java`, `ShippingExpeditionApi.java`
- `v1/payment/PaymentApi.java`
- `v2/product/ProductApiV2.java`, `ProductVariantApi.java`, `ProductVariantGroupApi.java`, `ProductVariationApi.java`

### 2.7 Security Configuration (CAST-Confirmed)

Security is configured in `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java` with the following confirmed Spring Beans:
- `apiAdminAuthenticationEntryPoint` (ID: 21159)
- `apiCustomerAuthenticationEntryPoint` (ID: 21158)
- `authenticationProvider` (ID: 21160)
- `authenticationTokenFilter` (ID: 21169)
- `passwordEncoder` (ID: 21167)

### 2.8 Configuration Files (CAST-Confirmed)

**42 Java Properties Files** confirmed, including:
- `application.properties` (sm-shop main and test, sm-core test)
- `application-test.properties` (sm-shop test)
- `database.properties` (multiple profiles: docker, dependency, cloud, mysql, local, gcp, plus test variants — 13 database.properties files total)
- `authentication.properties` (sm-core)
- `email.properties` (sm-core)
- `shopizer-core.properties` (multiple profiles: default, mysql, local, gcp, dependency, cloud, aws — 7 shopizer-core.properties files)
- `shopizer-properties.properties` (sm-core test, sm-shop main)
- `maven-wrapper.properties` (5 files, one per module)
- Bundle files: `messages.properties`, `messages_fr.properties`, `payment.properties`, `payment_fr.properties`, `shipping.properties`, `shipping_fr.properties`, `shopizer.properties`, `shopizer_fr.properties`
- `vault.properties` (sm-core test, sm-shop main)
- `log4j.properties` (sm-core test, sm-shop test)
- `hbm2dll.properties` (sm-core test)

### 2.9 Spring XML Configuration Files (CAST-Confirmed)

Spring Beans are defined in both Java configuration classes and XML files. Confirmed XML configuration files:
- `sm-core/src/main/resources/spring/shopizer-core-cms.xml`
- `sm-core/src/main/resources/spring/shopizer-core-modules.xml`
- `sm-core/src/main/resources/spring/shopizer-core-config.xml`
- `sm-core/src/main/resources/spring/shopizer-core-ehcache.xml`
- `sm-core/src/main/resources/spring/processors/shopizer-core-shipping-processors.xml`
- `sm-shop/src/main/resources/spring/shopizer-servlet-context.xml`

### 2.10 Quality Findings (CAST-Confirmed)

Three structural flaw rules triggered:

| Rule ID | Rule Name | Affected Objects |
|---|---|---|
| 1060020 | Avoid empty catch blocks for methods with high fan-in | 2 |
| 8408 | Avoid reflected cross-site scripting (non persistent) | 2 |
| 8482 | Avoid cross-site scripting through API requests | 73 |

CVE scanning: Not available in CAST MCP — query ran, returned "scanning not configured."

### 2.11 Cloud/Storage Integrations (CAST-Confirmed)

- AWS S3 integration: `Java AWS S3 Bucket`, `Java AWS Unknown S3 Bucket` element types present; `awsAssetsManager`, `awsContentAssetsManager`, `awsDownloadsManager`, `awsProductAssetsManager` Spring Beans confirmed
- Google Cloud Storage: `Java GCP Cloud Storage Bucket`, `Java GCP Unknown Cloud Storage Bucket` element types present
- AWS SES email: `sesEmailSender` Spring Bean confirmed

---

## 3. Proposed Changes

> ⚠️ The Requirement Document did not specify a target version, framework upgrade, or specific migration steps. The following section describes the integration testing and migration validation framework required for any future upgrade. All items below are proposals unless marked ✅ as CAST-confirmed current state.

### 3.1 Integration Test Coverage Requirements

Given the application's 324 Spring MVC endpoints and 63 JPA entities, the following integration test coverage is required:

**API Layer Testing**:
- All 324 Spring MVC operations must have integration test coverage
- Priority: checkout flows (`api/v1/cart/{}/checkout/`, `api/v1/auth/cart/{}/checkout/`) — these have the largest call graphs (3,264 and 3,281 full-graph objects respectively) ✅
- Priority: customer registration (`api/v1/customer/register/`) — 3,093 full-graph objects ✅
- Priority: category listing (`api/v1/category/`) — 2,972 full-graph objects ✅

**JPA/Persistence Layer Testing**:
- All 63 JPA entities must be covered by repository-level integration tests
- CRUD operations confirmed for all entities (select, insert, update, delete) ✅

**Security Testing**:
- JWT authentication flows (AuthenticateUserApi, AuthenticateCustomerApi)
- Multi-entry-point security configuration (MultipleEntryPointsSecurityConfig)
- XSS vulnerability remediation for 73 affected objects (rule 8482) ⚠️

### 3.2 Breaking Changes Table

| Category | Description | Affected Object Count | Source |
|---|---|---|---|
| XSS via API requests | 73 objects violate rule 8482 (cross-site scripting through API requests) | 73 | CAST MCP ✅ |
| Reflected XSS | 2 objects violate rule 8408 | 2 | CAST MCP ✅ |
| Empty catch blocks (high fan-in) | 2 methods with empty catch blocks and high fan-in | 2 | CAST MCP ✅ |
| Namespace migration (javax→jakarta) | Not confirmed by CAST — requires SME validation | Unknown | ⚠️ Proposal |
| Spring Boot version upgrade | Not specified in Requirement Document | Unknown | ⚠️ Proposal |

### 3.3 Namespace/Import Migration

⚠️ **SME Validation Required**: The Requirement Document did not specify a Spring Boot version upgrade (e.g., 2→3). The presence of `java ee` and `jee` in the technology stack ✅ indicates Java EE APIs are in use. If a Spring Boot 3.x migration is planned, `javax.*` → `jakarta.*` namespace migration would be required across all 63 JPA entities and all Spring MVC controllers. The exact count of affected files cannot be confirmed without a targeted CAST query for `javax` import usage, which was not run in this session.

---

## 4. Acceptance Criteria

### 4.1 Integration Test Suite
- [ ] All 324 Spring MVC endpoints have at least one integration test
- [ ] All 63 JPA entities have CRUD integration tests
- [ ] Checkout transaction flows (full-graph size 3,264–3,281 objects) pass end-to-end
- [ ] Customer registration flow (full-graph size 3,093 objects) passes end-to-end
- [ ] All 5 Maven modules build successfully with `mvn verify`

### 4.2 Security
- [ ] 73 XSS-via-API-requests violations (rule 8482) are remediated or risk-accepted
- [ ] 2 reflected XSS violations (rule 8408) are remediated or risk-accepted
- [ ] 2 empty catch block violations (rule 1060020) are remediated or risk-accepted
- [ ] JWT authentication flows pass integration tests

### 4.3 Configuration Validation
- [ ] All 42 properties files are validated for correctness in target environment
- [ ] All 13 database.properties profile variants are tested
- [ ] All 7 shopizer-core.properties profile variants are tested
- [ ] Spring XML configuration files load without errors

### 4.4 Cloud Integration
- [ ] AWS S3 integration tests pass (awsAssetsManager, awsContentAssetsManager, awsDownloadsManager, awsProductAssetsManager)
- [ ] Google Cloud Storage integration tests pass
- [ ] AWS SES email integration tests pass (sesEmailSender)

---

## 5. Out of Scope

- GR-12/GR-13 batch/message-listener decomposition: No batch jobs or message listeners were identified in CAST queries. This is logged as out-of-scope, not confirmed absent.
- Message-listener entry points (JMS/MQ/Kafka): Out of scope for this use case — not queried.
- Scheduled jobs: Out of scope for this use case — not queried.
