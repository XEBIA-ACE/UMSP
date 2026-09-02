# Shopizer — CAST MCP Research Findings

## ⚠️ BCM Compliance Gap (GR-08)
No BCM scope was provided. All queries ran application-wide against the "Shopizer" CAST snapshot. This is a standing compliance gap.

---

## Query Log

**CAST Snapshot ID/Date**: Not available in CAST MCP — tool does not expose snapshot ID directly. Delivery dates confirmed: Shopizer = 2026-07-10T13:02:00; Shopizer-3.2.5 = 2026-07-30T17:29:00.

| # | Tool/Query Type | Scope Filter | Raw Result Count | Disposition |
|---|----------------|-------------|-----------------|-------------|
| Q1 | `applications` | none | 9 applications | run-returned |
| Q2 | `stats` | application=Shopizer | 1 record | run-returned |
| Q3 | `stats` | application=Shopizer-3.2.5 | 1 record | run-returned |
| Q4 | `objects` | application=Shopizer, type:contains:JPA Entity | 50 items (page 1) | run-returned |
| Q5 | `objects` | application=Shopizer, type:contains:Spring Bean | 50 items (page 1) | run-returned |
| Q6 | `objects` | application=Shopizer, type:contains:Spring MVC | 50 items (page 1) | run-returned |
| Q7 | `objects` | application=Shopizer, type:contains:Spring MVC, page=2 | 50 items (page 2) | run-returned |
| Q8 | `transactions` | application=Shopizer | 50 items (page 1) | run-returned |
| Q9 | `packages` | application=Shopizer | 0 items | run-returned (empty) |
| Q10 | `objects` | application=Shopizer, type:contains:JPA Entity, page=2 | 50 items (page 2) | run-returned |
| Q11 | `objects` | application=Shopizer, type:contains:Spring Bean, page=2 | 50 items (page 2) | run-returned |
| Q12 | `quality_insights` | application=Shopizer, nature=structural-flaws | 2 rules | run-returned |
| Q13 | `quality_insights` | application=Shopizer, nature=cve | 0 items | run-returned (empty — scanning not configured) |
| Q14 | `transactions` | application=Shopizer, page=2 | 50 items (page 2) | run-returned |
| Q15 | `quality_insights` | application=Shopizer, nature=cloud-detection-patterns | 23 findings | run-returned |
| Q16 | `transactions` | application=Shopizer, page=3 | 50 items (page 3) | run-returned |
| Q17 | `objects` | application=Shopizer, name:contains:pom, type:contains:Java Properties | 0 items | run-returned (empty) |
| Q18 | `objects` | application=Shopizer, type:contains:Java Properties File | 0 items | run-returned (empty) |
| Q19 | `objects` | application=Shopizer-3.2.5, type:contains:JPA Entity | 50 items (page 1) | run-returned |

**Unqueried types (out of scope for this use case):**
- Batch/scheduled jobs: Out of scope for this use case — not queried
- Message listeners (JMS/Kafka): Out of scope for this use case — not queried
- ISO 5055 quality insights: Out of scope for this use case — not queried
- Green detection patterns: Out of scope for this use case — not queried
- Data graphs: Out of scope for this use case — not queried
- Object intra/inward/outward graphs: Out of scope for this use case — not queried

---

## Confirmed Facts (✅ direct CAST result)

### Application Inventory
✅ Two Shopizer snapshots exist in CAST:
- "Shopizer" (delivery: 2026-07-10T13:02:00, snapshot name: Onboarding-202607101302)
- "Shopizer-3.2.5" (delivery: 2026-07-30T17:29:00, snapshot name: Onboarding-202607301729)

### Technology Stack
✅ Technologies confirmed by CAST stats query for "Shopizer":
`aws s3`, `azure sdk for java`, `gcp storage`, `hibernate`, `java`, `java ee`, `java server pages`, `jee`, `jpa`, `spring`, `spring web services`

✅ Technologies confirmed by CAST stats query for "Shopizer-3.2.5":
`aws sdk s3 for java`, `google cloud storage for java`, `hibernate`, `java`, `java ee`, `java properties`, `java server pages`, `jee`, `jpa`, `spring`, `spring web services`

### Application Size
✅ Shopizer: 91,162 LOC, 16,468 elements, 72,524 interactions
✅ Shopizer-3.2.5: 91,162 LOC, 16,572 elements, 72,325 interactions

### CRUD Operations
✅ Both snapshots support: select, delete, insert, update

### Build Tool
❌ Query ran (Q9, Q17, Q18), no result — packages query returned no results; Java Properties File type query returned no results. Build tool type not confirmed by CAST.

---

## Technical Appendix

### A1. JPA Entities (Q4, Q10 — type:contains:JPA Entity, application=Shopizer)

**JPA Entity objects (type=JPA Entity):**
- Catalog (CAST ID: 17800) — `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/catalog/Catalog.java`
- CatalogCategoryEntry (CAST ID: 17799) — `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/catalog/CatalogCategoryEntry.java`
- Category (CAST ID: 17798) — `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/category/Category.java`
- CategoryDescription (CAST ID: 17797) — `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/category/CategoryDescription.java`
- Content (CAST ID: 16727) — `sm-core-model/src/main/java/com/salesmanager/core/model/content/Content.java`
- ContentDescription (CAST ID: 17804) — `sm-core-model/src/main/java/com/salesmanager/core/model/content/ContentDescription.java`
- Country (CAST ID: 10528) — `sm-core-model/src/main/java/com/salesmanager/core/model/reference/country/Country.java`
- CountryDescription (CAST ID: 10307) — `sm-core-model/src/main/java/com/salesmanager/core/model/reference/country/CountryDescription.java`
- Currency (CAST ID: 6643) — `sm-core-model/src/main/java/com/salesmanager/core/model/reference/currency/Currency.java`
- Customer (CAST ID: 4951) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/Customer.java`
- CustomerAttribute (CAST ID: 16708) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/attribute/CustomerAttribute.java`
- CustomerOptin (CAST ID: 16902) — `sm-core-model/src/main/java/com/salesmanager/core/model/system/optin/CustomerOptin.java`
- CustomerOption (CAST ID: 16621) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/attribute/CustomerOption.java`
- CustomerOptionDescription (CAST ID: 16603) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/attribute/CustomerOptionDescription.java`
- CustomerOptionSet (CAST ID: 14154) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/attribute/CustomerOptionSet.java`
- CustomerOptionValue (CAST ID: 14117) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/attribute/CustomerOptionValue.java`
- CustomerOptionValueDescription (CAST ID: 17764) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/attribute/CustomerOptionValueDescription.java`
- CustomerReview (CAST ID: 15706) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/review/CustomerReview.java`
- CustomerReviewDescription (CAST ID: 15587) — `sm-core-model/src/main/java/com/salesmanager/core/model/customer/review/CustomerReviewDescription.java`
- DigitalProduct (CAST ID: 17790) — `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/file/DigitalProduct.java`
- FileHistory (CAST ID: 13284) — `sm-core-model/src/main/java/com/salesmanager/core/model/order/filehistory/FileHistory.java`
- GeoZone (CAST ID: 6412) — `sm-core-model/src/main/java/com/salesmanager/core/model/reference/geozone/GeoZone.java`
- GeoZoneDescription (CAST ID: 17179) — `sm-core-model/src/main/java/com/salesmanager/core/model/reference/geozone/GeoZoneDescription.java`
- Group (CAST ID: 17130) — `sm-core-model/src/main/java/com/salesmanager/core/model/user/Group.java`
- IntegrationModule (CAST ID: 16639) — `sm-core-model/src/main/java/com/salesmanager/core/model/system/IntegrationModule.java`
- Language (CAST ID: 17482) — `sm-core-model/src/main/java/com/salesmanager/core/model/reference/language/Language.java`
- Manufacturer (CAST ID: 17787) — `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/manufacturer/Manufacturer.java`
- ManufacturerDescription (CAST ID: 17786) — `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/manufacturer/ManufacturerDescription.java`
- MerchantConfiguration (CAST ID: 16372) — `sm-core-model/src/main/java/com/salesmanager/core/model/system/MerchantConfiguration.java`
- MerchantLog (CAST ID: 17757) — `sm-core-model/src/main/java/com/salesmanager/core/model/system/MerchantLog.java`
- MerchantStore (CAST ID: 15393) — `sm-core-model/src/main/java/com/salesmanager/core/model/merchant/MerchantStore.java`
- Optin (CAST ID: 17658) — `sm-core-model/src/main/java/com/salesmanager/core/model/system/optin/Optin.java`
- Order (CAST ID: 15360) — `sm-core-model/src/main/java/com/salesmanager/core/model/order/Order.java`
- OrderAccount (CAST ID: 12767) — `sm-core-model/src/main/java/com/salesmanager/core/model/order/orderaccount/OrderAccount.java`
- OrderAccountProduct (CAST ID: 12081) — `sm-core-model/src/main/java/com/salesmanager/core/model/order/orderaccount/OrderAccountProduct.java`
- OrderAttribute (CAST ID: 14135) — `sm-core-model/src/main/java/com/salesmanager/core/model/order/attributes/OrderAttribute.java`
- OrderProduct (CAST ID: 11791) — `sm-core-model/src/main/java/com/salesmanager/core/model/order/orderproduct/OrderProduct.java`
- ShippingOrigin (CAST ID: 17599) — `sm-core-model/src/main/java/com/salesmanager/core/model/shipping/ShippingOrigin.java`
- ShoppingCart (CAST ID: 17570) — `sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/ShoppingCart.java`
- ShoppingCartAttributeItem (CAST ID: 16900) — `sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/ShoppingCartAttributeItem.java`
- ShoppingCartItem (CAST ID: 16844) — `sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/ShoppingCartItem.java`
- SystemConfiguration (CAST ID: 17731) — `sm-core-model/src/main/java/com/salesmanager/core/model/system/SystemConfiguration.java`
- SystemNotification (CAST ID: 17707) — `sm-core-model/src/main/java/com/salesmanager/core/model/system/SystemNotification.java`

(Source: CAST MCP — objects query: type:contains:JPA Entity / application=Shopizer / pages 1-2)

**Additional JPA Entity objects confirmed from page 2 (Select operations):**
- Zone (no separate entity ID returned — confirmed via JPA Entity Operation)
- TaxRate (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductVariation (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductVariantGroup (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductType (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductReview (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductPrice (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductImage (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductVariant (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductAvailability (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductOptionSet (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductAttribute (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductRelationship (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductOption (no separate entity ID returned — confirmed via JPA Entity Operation)
- ProductOptionValue (no separate entity ID returned — confirmed via JPA Entity Operation)
- Product (no separate entity ID returned — confirmed via JPA Entity Operation)
- OrderTotal (no separate entity ID returned — confirmed via JPA Entity Operation)
- OrderStatusHistory (no separate entity ID returned — confirmed via JPA Entity Operation)
- OrderProductDownload (no separate entity ID returned — confirmed via JPA Entity Operation)
- OrderProduct (CAST ID: 11791 — entity; Select operation ID: 13139)
- Transaction (no separate entity ID returned — confirmed via JPA Entity Operation)
- Quote (no separate entity ID returned — confirmed via JPA Entity Operation)
- User (no separate entity ID returned — confirmed via JPA Entity Operation)
- Permission (no separate entity ID returned — confirmed via JPA Entity Operation)

(Source: CAST MCP — objects query: type:contains:JPA Entity / application=Shopizer / page 2)

### A2. Key Spring Beans (Q5, Q11 — type:contains:Spring Bean, application=Shopizer)

Selected key beans with CAST IDs:
- `OrderTotalService` (CAST ID: 21126) — `sm-core/src/main/java/com/salesmanager/core/business/services/order/ordertotal/OrderTotalServiceImpl.java`
- `apiAdminAuthenticationEntryPoint` (CAST ID: 21083) — `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java`
- `apiCustomerAuthenticationEntryPoint` (CAST ID: 21082) — `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java`
- `authenticateUserApi` (CAST ID: 21264) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/user/AuthenticateUserApi.java`
- `authenticationProvider` (CAST ID: 21084) — `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java`
- `authenticationTokenFilter` (CAST ID: 21093) — `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java`
- `catalogFacade` (CAST ID: 21243) — `sm-shop/src/main/java/com/salesmanager/shop/store/facade/catalog/CatalogFacadeImpl.java`
- `catalogService` (CAST ID: 21170) — `sm-shop/src/main/java/com/salesmanager/shop/store/facade/catalog/CatalogServiceImpl.java`
- `categoryFacade` (CAST ID: 21242) — `sm-shop/src/main/java/com/salesmanager/shop/store/facade/category/CategoryFacadeImpl.java`
- `categoryService` (CAST ID: 21169) — `sm-shop/src/main/java/com/salesmanager/core/business/services/catalog/category/CategoryServiceImpl.java`
- `contentFacade` (CAST ID: 21237) — `sm-shop/src/main/java/com/salesmanager/shop/store/facade/content/ContentFacadeImpl.java`
- `contentService` (CAST ID: 21142) — `sm-shop/src/main/java/com/salesmanager/core/business/services/content/ContentServiceImpl.java`
- `coreConfiguration` (CAST ID: 20544) — `sm-core/src/main/java/com/salesmanager/core/business/utils/CoreConfiguration.java`
- `corsFilter` (CAST ID: 20990) — `sm-shop/src/main/java/com/salesmanager/shop/application/config/ShopApplicationConfiguration.java`
- `customerFacade` (CAST ID: 21259) — `sm-shop/src/main/java/com/salesmanager/shop/store/controller/customer/facade/CustomerFacadeImpl.java`
- `customerFacadev1` (CAST ID: 21241) — `sm-shop/src/main/java/com/salesmanager/shop/store/facade/customer/CustomerFacadeImpl.java`
- `customerService` (CAST ID: 21141) — `sm-shop/src/main/java/com/salesmanager/core/business/services/customer/CustomerServiceImpl.java`
- `manufacturerFacade` (CAST ID: 21227) — `sm-shop/src/main/java/com/salesmanager/shop/store/facade/manufacturer/ManufacturerFacadeImpl.java`
- `merchantService` (CAST ID: 21130) — `sm-shop/src/main/java/com/salesmanager/core/business/services/merchant/MerchantStoreServiceImpl.java`
- `orderFacade` (CAST ID: 21253) — `sm-shop/src/main/java/com/salesmanager/shop/store/controller/order/facade/OrderFacadeImpl.java`
- `orderFacadev1` (CAST ID: 20673) — `sm-shop/src/main/java/com/salesmanager/shop/store/facade/order/OrderFacadeImpl.java`
- `orderService` (CAST ID: 21129) — `sm-shop/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java`
- `passwordEncoder` (CAST ID: 21091) — `sm-shop/src/main/java/com/salesmanager/shop/application/config/MultipleEntryPointsSecurityConfig.java`
- `paymentConfigurationFacade` (CAST ID: 21226) — `sm-shop/src/main/java/com/salesmanager/shop/store/facade/payment/PaymentConfigurationFacadeImpl.java`
- `paymentService` (CAST ID: 21125) — `sm-shop/src/main/java/com/salesmanager/core/business/services/payments/PaymentServiceImpl.java`

(Source: CAST MCP — objects query: type:contains:Spring Bean / application=Shopizer / pages 1-2)

### A3. Key Spring MVC Operations (Q6, Q7 — type:contains:Spring MVC, application=Shopizer)

Selected key operations with CAST IDs:
- `/` GET (CAST ID: 13098) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/DefaultController.java`
- `admin/files/downloads/{}/{}/` ANY (CAST ID: 12964) — `sm-shop/src/main/java/com/salesmanager/shop/controller/FilesController.java`
- `api/v1/auth/cart/{}/checkout/` POST (CAST ID: 5933) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderApi.java`
- `api/v1/auth/cart/{}/payment/init/` POST (CAST ID: 12935) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderPaymentApi.java`
- `api/v1/auth/cart/{}/shipping/` GET (CAST ID: 13055) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderShippingApi.java`
- `api/v1/auth/customer/` ANY (CAST ID: 12435) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/CustomerApi.java`
- `api/v1/auth/customer/` DELETE (CAST ID: 24949) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/CustomerApi.java`
- `api/v1/auth/customer/cart/` GET (CAST ID: 13006) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java`
- `api/v1/auth/orders/` GET (CAST ID: 8595) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderApi.java`
- `api/v1/auth/products/` POST (CAST ID: 12927) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductApi.java`
- `api/v1/cart/` POST (CAST ID: 12835) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java`
- `api/v1/cart/{}/checkout/` POST (CAST ID: 5830) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/order/OrderApi.java`
- `api/v1/category/` GET (CAST ID: 13089) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/CategoryApi.java`
- `api/v1/customer/login/` POST (CAST ID: 236432 — transaction; operation ID not separately returned)
- `api/v1/customer/register/` POST (CAST ID: 236433 — transaction; operation ID not separately returned)
- `api/v1/private/login/` POST (CAST ID: 12904) — `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/user/AuthenticateUserApi.java`

(Source: CAST MCP — objects query: type:contains:Spring MVC / application=Shopizer / pages 1-2)

### A4. Key Transactions (Q8, Q14, Q16 — transactions, application=Shopizer)

Top transactions by fullSize:
- `api/v1/cart/{}/checkout/` POST (CAST ID: 236423, fullSize: 3,254, reducedSize: 154) — stack: aws s3, gcp storage, hibernate, java, java ee, spring, spring web services
- `api/v1/auth/cart/{}/checkout/` POST (CAST ID: 236424, fullSize: 3,237, reducedSize: 155) — stack: aws s3, gcp storage, hibernate, java, java ee, spring, spring web services
- `api/v1/private/store/{}/` PUT (CAST ID: 236340, fullSize: 3,085, reducedSize: 148)
- `api/v1/private/store/` POST (CAST ID: 236385, fullSize: 3,075, reducedSize: 141)
- `api/v1/customer/register/` POST (CAST ID: 236433, fullSize: 3,065, reducedSize: 139)
- `api/v1/category/` GET (CAST ID: 236586, fullSize: 2,944, reducedSize: 187)
- `api/v1/category/{}/` GET (CAST ID: 236589, fullSize: 2,908, reducedSize: 185)
- `api/v1/category/product/{}/` GET (CAST ID: 236585, fullSize: 2,907, reducedSize: 178)
- `api/v1/category/{}/manufacturer/` GET (CAST ID: 236524, fullSize: 2,905, reducedSize: 180)

(Source: CAST MCP — transactions query / application=Shopizer / pages 1-3)

### A5. Structural Quality Findings (Q12 — quality_insights, nature=structural-flaws)

- Rule: "Avoid running SQL queries inside a loop" (CAST rule ID: 1025056, category: AIP-CWE-1050, factor: Efficiency) — 3 objects affected
- Rule: "Avoid empty catch blocks for methods with high fan-in" (CAST rule ID: 1060020, category: AIP-CWE-1069, factor: Reliability) — 2 objects affected

(Source: CAST MCP — quality_insights: structural-flaws / application=Shopizer / count=2 rules, 5 total objects)

### A6. Cloud Detection Patterns (Q15 — quality_insights, nature=cloud-detection-patterns)

| Finding | CAST ID | Objects | Criticality | Contribution |
|---------|---------|---------|-------------|-------------|
| CloudReady - Use of an unsecured data string | platform-migration:1200056 | 29 | Critical | Blocker |
| CloudReady - Access to environment variable | platform-migration:1200001 | 11 | Low | Blocker |
| CloudReady - Avoid using hardcoded URLs (HTTP protocol) | platform-migration:1200031 | 10 | Low | Blocker |
| CloudReady - Use of unsecured network protocols or URI libraries | platform-migration:1200042 | 9 | Low | Blocker |
| CloudReady - Using in-memory caching libraries | platform-migration:1200372 | 9 | High | Blocker |
| CloudReady - Perform Directory Manipulation | platform-migration:1200006 | 6 | Low | Blocker |
| CloudReady - Using stateful session (i.e. Socket / Servlet) | platform-migration:1200052 | 5 | High | Blocker |
| CloudReady - Using a temporary local file or directory | platform-migration:1200027 | 4 | Low | Blocker |
| CloudReady - Perform File Manipulation | platform-migration:1200007 | 4 | Low | Blocker |
| CloudReady - Using a Cloud-based data storage | platform-migration:1200077 | 4 | None | Booster |
| CloudReady - Using a Cloud-based data storage | platform-migration:1200087 | 4 | None | Booster |
| CloudReady - Using Hardcoded Network Addresses | platform-migration:1200029 | 3 | Low | Blocker |
| CloudReady - Using file system | platform-migration:1200025 | 2 | Low | Blocker |
| CloudReady - Use of sendmail utility on Paas | platform-migration:1200123 | 2 | Medium | Blocker |

(Source: CAST MCP — quality_insights: cloud-detection-patterns / application=Shopizer / count=23 findings)

### A7. CVE Findings (Q13)
Not available in CAST MCP — CVE scanning was not configured for this application.

### A8. Packages (Q9)
Not available in CAST MCP — packages query returned no results for application=Shopizer.

### A9. Shopizer-3.2.5 Comparison (Q3, Q19)
- Elements: 16,572 (vs. 16,468 in Shopizer) — 104 more elements
- Interactions: 72,325 (vs. 72,524 in Shopizer) — 199 fewer interactions
- JPA Entity count: Same entity names confirmed in Shopizer-3.2.5 (Q19 returned same entity list)
- Source path prefix in Shopizer-3.2.5: `§{main_sources}§/shopizer-3.2.5/` (vs. `§{main_sources}§/` in Shopizer)
- Additional technology in Shopizer-3.2.5: `java properties` (not present in Shopizer snapshot)

(Source: CAST MCP — stats query: application=Shopizer-3.2.5; objects query: type:contains:JPA Entity / application=Shopizer-3.2.5 / page 1)
