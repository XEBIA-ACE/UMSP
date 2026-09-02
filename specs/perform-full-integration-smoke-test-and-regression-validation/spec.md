# Shopizer — Full Integration Smoke Test and Regression Validation Spec

## ⚠️ BCM Compliance Gap (GR-08)
No Business Capability Model (BCM) scope was provided with this requirement. All queries were executed application-wide against the "Shopizer" CAST snapshot (delivery: 2026-07-10). This is a standing compliance gap per GR-08 and must be resolved before this spec is used to gate a production release. A second CAST snapshot, "Shopizer-3.2.5" (delivery: 2026-07-30), was also available and used for structural comparison.

---

## 1. Purpose

This specification defines the scope, entry points, data flows, and acceptance criteria for a full integration smoke test and regression validation suite for the Shopizer e-commerce application. It is intended to be complete enough for a code-generation agent or QA automation engineer to implement the test suite without additional discovery.

---

## 2. Current State

### 2.1 Application Identity
- **Application name**: Shopizer (primary snapshot); Shopizer-3.2.5 (comparison snapshot)
- **Language**: Java (Source: CAST MCP — technologies list includes "java")
- **Frameworks**: Spring, Spring Web Services, Hibernate, JPA, JEE/Java EE (Source: CAST MCP — stats query)
- **Cloud integrations**: AWS S3, Azure SDK for Java, GCP Storage (Source: CAST MCP — stats query)
- **Additional technologies**: Java Server Pages (Source: CAST MCP — stats query)
- **Build tool**: Not available in CAST MCP — query attempted (packages query returned no results; Java Properties File type query returned no results)
- **Language version**: Not available in CAST MCP — query attempted
- **Runtime version**: Not available in CAST MCP — query attempted
- **Upgrade urgency**: Medium (Source: Requirement Document)

### 2.2 Application Size
- **Lines of code**: 91,162 (Source: CAST MCP — stats)
- **Total elements**: 16,468 (Shopizer snapshot) / 16,572 (Shopizer-3.2.5 snapshot) (Source: CAST MCP — stats)
- **Total interactions**: 72,524 (Shopizer) / 72,325 (Shopizer-3.2.5) (Source: CAST MCP — stats)

### 2.3 Module Structure
Source files are organized under the following Maven-style module paths (Source: CAST MCP — object filePaths):
- `sm-core-model/` — JPA entity model classes
- `sm-core/` — Business services, Spring configuration, Spring XML beans
- `sm-shop/` — REST API controllers, facades, security configuration, application configuration

### 2.4 Entry Points (Spring MVC Operations)
CAST identified **150+ Spring MVC operations** across three pages of results (50 per page). These are the primary integration test entry points. They are organized into the following API namespaces:

**Public / Customer-facing APIs** (`/api/v1/` prefix, no auth):
- Cart management: POST/GET/PUT/DELETE `/api/v1/cart/`, `/api/v1/cart/{}/`, `/api/v1/cart/{}/multi/`, `/api/v1/cart/{}/promo/{}/`, `/api/v1/cart/{}/product/{}/`
- Checkout: POST `/api/v1/cart/{}/checkout/`, `/api/v1/auth/cart/{}/checkout/`
- Payment init: POST `/api/v1/cart/{}/payment/init/`
- Shipping: GET/POST `/api/v1/cart/{}/shipping/`
- Order totals: GET `/api/v1/cart/{}/total/`
- Category browsing: GET `/api/v1/category/`, `/api/v1/category/{}/`, `/api/v1/category/name/{}/`, `/api/v1/category/product/{}/`
- Product browsing: GET `/api/v1/product/{}/`, `/api/v1/product/friendly/{}/`, `/api/v1/product/slug/{}/`
- Customer registration/login: POST `/api/v1/customer/register/`, `/api/v1/customer/login/`
- Password reset: POST/GET `/api/v1/customer/password/reset/request/`, `/api/v1/customer/{}/password/{}/`, `/api/v1/customer/{}/reset/{}/`
- References: GET `/api/v1/country/`, `/api/v1/currency/`
- Content: GET `/api/v1/content/boxes/`, `/api/v1/content/pages/`, `/api/v1/content/images/`
- Contact: POST `/api/v1/contact/`
- Config: GET `/api/v1/config/`

**Authenticated Customer APIs** (`/api/v1/auth/` prefix):
- Customer profile: GET/ANY `/api/v1/auth/customer/`, `/api/v1/auth/customer/profile/`, `/api/v1/auth/customer/address/`
- Customer cart: GET `/api/v1/auth/customer/cart/`, `/api/v1/auth/customer/{}/cart/`
- Orders: GET `/api/v1/auth/orders/`, `/api/v1/auth/orders/{}/`
- Product management: POST/PUT/DELETE `/api/v1/auth/products/`, `/api/v1/auth/product/{}/`
- Reviews: POST/PUT/DELETE `/api/v1/auth/products/{}/reviews/`, `/api/v1/auth/products/{}/reviews/{}/`
- Token refresh: GET `/api/v1/auth/refresh/`, `/api/v1/auth/customer/refresh/`

**Private / Admin APIs** (`/api/v1/private/` prefix):
- Admin login: POST `/api/v1/private/login/`
- Store management: POST/GET/PUT/DELETE `/api/v1/private/store/`, `/api/v1/private/store/{}/`, `/api/v1/private/stores/`
- Product administration: POST/GET/PUT/DELETE `/api/v1/private/product/`, `/api/v1/private/products/`
- Customer administration: POST/GET/PUT/DELETE `/api/v1/private/customer/`, `/api/v1/private/customers/`
- Order administration: GET/PUT `/api/v1/private/orders/`, `/api/v1/private/orders/{}/`
- Payment modules: GET/POST `/api/v1/private/modules/payment/`
- Shipping modules: GET/POST `/api/v1/private/modules/shipping/`
- Tax: POST/GET/PUT/DELETE `/api/v1/private/tax/class/`, `/api/v1/private/tax/rate/`
- User management: POST/GET/PUT/DELETE `/api/v1/private/user/`, `/api/v1/private/users/`
- Content administration: POST/GET/PUT/DELETE `/api/v1/private/content/`
- Manufacturer: POST/GET/PUT/DELETE `/api/v1/private/manufacturer/`
- Marketplace: GET `/api/v1/private/marketplace/{}/`
- Cache: DELETE `/api/v1/auth/cache/store/{}/clear/`

**Legacy / Non-versioned**:
- Root: GET `/`
- File downloads: ANY `/admin/files/downloads/{}/{}/`

### 2.5 JPA Entities (Data Layer)
CAST identified **70 JPA Entity objects** across the `sm-core-model` module. Key entities include (full list in Technical Appendix):
- **Catalog domain**: Catalog, CatalogCategoryEntry, Category, CategoryDescription, Product, ProductAttribute, ProductAvailability, ProductImage, ProductOption, ProductOptionSet, ProductOptionValue, ProductPrice, ProductRelationship, ProductReview, ProductType, ProductVariant, ProductVariantGroup, ProductVariation, Manufacturer, ManufacturerDescription, DigitalProduct
- **Order domain**: Order, OrderAccount, OrderAccountProduct, OrderAttribute, OrderProduct, OrderProductAttribute, OrderProductDownload, OrderProductPrice, OrderStatusHistory, OrderTotal, FileHistory, Transaction
- **Customer domain**: Customer, CustomerAttribute, CustomerOption, CustomerOptionDescription, CustomerOptionSet, CustomerOptionValue, CustomerOptionValueDescription, CustomerReview, CustomerReviewDescription, CustomerOptin
- **Merchant domain**: MerchantStore, MerchantConfiguration, MerchantLog, IntegrationModule, SystemConfiguration, SystemNotification
- **Reference domain**: Country, CountryDescription, Currency, GeoZone, GeoZoneDescription, Language, Zone
- **Shopping domain**: ShoppingCart, ShoppingCartAttributeItem, ShoppingCartItem, Quote, ShippingOrigin
- **User domain**: User, Group, Permission
- **Tax domain**: TaxRate
- **Optin domain**: Optin

### 2.6 Spring Beans
CAST identified **100+ Spring Beans** across `sm-core` and `sm-shop` modules, including service implementations, facade implementations, mapper/populator beans, security configuration beans, and XML-defined beans in `shopizer-core-cms.xml`, `shopizer-core-modules.xml`, `shopizer-core-config.xml`, and `shopizer-servlet-context.xml`.

### 2.7 Transactions
CAST identified **150+ transactions** (Spring MVC entry points with full call graphs). The largest transactions by full call graph size include:
- `api/v1/cart/{}/checkout/` (fullSize: 3,254 objects) — most complex transaction
- `api/v1/auth/cart/{}/checkout/` (fullSize: 3,237 objects)
- `api/v1/customer/register/` (fullSize: 3,065 objects)
- `api/v1/private/store/{}/` PUT (fullSize: 3,085 objects)
- `api/v1/category/` GET (fullSize: 2,944 objects)

### 2.8 Quality Findings
- **Structural flaws**: 2 rules triggered
  - "Avoid running SQL queries inside a loop" — 3 objects affected
  - "Avoid empty catch blocks for methods with high fan-in" — 2 objects affected
- **CVE**: Not available in CAST MCP — scanning not configured
- **Cloud readiness blockers**: 23 findings across cloud-detection-patterns, including:
  - 29 objects: "Use of an unsecured data string" (Critical)
  - 11 objects: "Access to environment variable"
  - 10 objects: "Avoid using hardcoded URLs (HTTP protocol)"
  - 9 objects: "Use of unsecured network protocols or URI libraries"
  - 9 objects: "Using in-memory caching libraries" (High)
  - 5 objects: "Using stateful session" (High)

---

## 3. Proposed Changes

This spec covers the **integration smoke test and regression validation** work item. No framework version upgrade or namespace migration is specified in the Requirement Document. The work is purely test coverage and validation.

### 3.1 Smoke Test Scope
A smoke test suite must verify that the application starts and that all critical API paths return expected HTTP status codes. The following entry points are designated as smoke test targets based on their transaction complexity and business criticality:

| Priority | Endpoint | HTTP Method | Rationale |
|----------|----------|-------------|-----------|
| P1 | `/api/v1/cart/{}/checkout/` | POST | Largest transaction (3,254 objects) |
| P1 | `/api/v1/customer/register/` | POST | 3,065 objects; customer onboarding |
| P1 | `/api/v1/private/store/{}/` | PUT | 3,085 objects; store configuration |
| P1 | `/api/v1/category/` | GET | 2,944 objects; catalog browsing |
| P1 | `/api/v1/private/login/` | POST | Admin authentication |
| P1 | `/api/v1/customer/login/` | POST | Customer authentication |
| P2 | `/api/v1/auth/orders/` | GET | Order history |
| P2 | `/api/v1/private/orders/` | GET | Admin order management |
| P2 | `/api/v1/cart/` | POST | Cart creation |
| P2 | `/api/v1/auth/products/` | POST | Product creation |

### 3.2 Regression Validation Scope
Regression tests must cover all 150+ Spring MVC operations. Tests must be organized by API namespace (public, auth, private) and HTTP method (GET, POST, PUT, DELETE, ANY).

### 3.3 Breaking Changes Table
No framework upgrade is specified in the Requirement Document. The following structural issues from CAST represent existing risks that regression tests must detect:

| Category | Rule | Affected Objects | Risk |
|----------|------|-----------------|------|
| Structural Flaw | SQL queries inside a loop | 3 | Performance regression under load |
| Structural Flaw | Empty catch blocks (high fan-in) | 2 | Silent failure in high-traffic paths |
| Cloud Blocker | Unsecured data strings | 29 | Security regression |
| Cloud Blocker | In-memory caching | 9 | State management regression |
| Cloud Blocker | Stateful sessions | 5 | Scalability regression |
| Cloud Blocker | Hardcoded URLs (HTTP) | 10 | Environment-specific failures |

---

## 4. Acceptance Criteria

1. **Smoke test pass rate**: All P1 endpoints return HTTP 2xx or expected redirect codes within 5 seconds of application startup.
2. **Regression coverage**: All 150+ Spring MVC operations have at least one automated test case.
3. **JPA entity coverage**: All 70 JPA entities have at least one CRUD operation exercised through the API layer.
4. **Structural flaw regression**: Tests must detect the 3 SQL-in-loop violations and 2 empty-catch-block violations identified by CAST.
5. **No new structural flaws**: The post-test CAST scan must not introduce new structural-flaw violations beyond the 5 currently identified.
6. **Transaction integrity**: The checkout transaction (`api/v1/cart/{}/checkout/`) must complete end-to-end without error in the test environment.
7. **Authentication flows**: Both customer login (`/api/v1/customer/login/`) and admin login (`/api/v1/private/login/`) must succeed and return valid JWT tokens.
8. **Cloud readiness**: The 29 "unsecured data string" findings must be documented as known issues; no new instances may be introduced.
9. **BCM gap resolution**: Before production sign-off, a BCM scope must be defined and queries re-run against the scoped subsystem.
