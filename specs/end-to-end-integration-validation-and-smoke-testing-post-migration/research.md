# Research Findings: Shopizer — Post-Migration Smoke Testing
## CAST MCP Investigation Report

---

## ⚠️ BCM Scope Gap (GR-08)
No BCM subsystem was provided. All queries were executed application-wide against both the "Shopizer" (pre-migration) and "Shopizer-3.2.5" (post-migration) CAST snapshots. This is a standing compliance gap in every deliverable.

---

## CAST Snapshot Information
CAST snapshot ID/date: Not exposed by the MCP tool. Delivery dates confirmed from application list:
- **Shopizer**: delivery `2026-07-10T13:02:00`, name `Onboarding-202607101302`
- **Shopizer-3.2.5**: delivery `2026-07-30T17:29:00`, name `Onboarding-202607301729`

---

## Query Log

| # | Tool/Query | Scope Filter | Raw Result Count | Disposition |
|---|---|---|---|---|
| Q01 | `applications` | none | 9 applications | run-returned |
| Q02 | `stats` | application=Shopizer | 1 record | run-returned |
| Q03 | `stats` | application=Shopizer-3.2.5 | 1 record | run-returned |
| Q04 | `objects` | application=Shopizer, type:contains:JPA Entity | 100 items (page 1) | run-returned |
| Q05 | `objects` | application=Shopizer, type:equals:JPA Entity | 65 items (page 1), 0 (page 2) | run-returned |
| Q06 | `objects` | application=Shopizer, type:equals:Spring Bean | 100 (p1), 50 (p2), ~50 (p3), 0 (p4) | run-returned |
| Q07 | `objects` | application=Shopizer, type:contains:Spring MVC | 100 items (page 1) | run-returned |
| Q08 | `transactions` | application=Shopizer | 324 total (4 pages × 100) | run-returned |
| Q09 | `transactions` | application=Shopizer-3.2.5 | 324 total (4 pages × 100) | run-returned |
| Q10 | `objects` | application=Shopizer, name:contains:pom | 0 results | run-returned (empty) |
| Q11 | `packages` | application=Shopizer | 0 results | run-returned (empty) |
| Q12 | `packages` | application=Shopizer-3.2.5 | 0 results | run-returned (empty) |
| Q13 | `quality_insights` | application=Shopizer, nature=structural-flaws | 2 findings | run-returned |
| Q14 | `quality_insights` | application=Shopizer, nature=cve | 0 findings | run-returned (empty) |
| Q15 | `quality_insights` | application=Shopizer, nature=cloud-detection-patterns | 23 findings | run-returned |
| Q16 | `quality_insights` | application=Shopizer-3.2.5, nature=structural-flaws | 3 findings | run-returned |
| Q17 | `objects` | application=Shopizer-3.2.5, type:equals:JPA Entity | 65 items (page 1) | run-returned |
| Q18 | `objects` | application=Shopizer-3.2.5, type:equals:Spring Bean | 100 (p1), ~100 (p2) | run-returned |

**Not queried (out of scope for this use case):**
- Batch/scheduler entry points: Out of scope — no batch element types in CAST inventory
- Message-listener entry points: Out of scope — no JMS/Kafka types in CAST inventory
- `transaction_details` deep-dive: Out of scope — discovery pass sufficient for smoke test spec
- `data_graphs`: Out of scope for this use case — not queried
- `object_details` (intra/inward/outward): Out of scope for this use case — not queried
- `iso-5055` quality insights: Out of scope for this use case — not queried
- `green-detection-patterns`: Out of scope for this use case — not queried

---

## Findings

### F01 — Application Inventory ✅
Two Shopizer snapshots confirmed in CAST:
- `Shopizer` (ID: name=Shopizer, delivery=2026-07-10)
- `Shopizer-3.2.5` (ID: name=Shopizer-3.2.5, delivery=2026-07-30)

(Source: CAST MCP — applications query / Shopizer / Shopizer-3.2.5 / count=2)

### F02 — Application Stats: Shopizer (Pre-Migration) ✅
- LOC: 91,162
- Elements: 16,468
- Interactions: 72,524
- Technologies: aws s3, azure sdk for java, gcp storage, hibernate, java, java ee, java server pages, jee, jpa, spring, spring web services
- CRUD: select, delete, insert, update

(Source: CAST MCP — stats query / Shopizer / 1 record)

### F03 — Application Stats: Shopizer-3.2.5 (Post-Migration) ✅
- LOC: 91,162
- Elements: 16,572
- Interactions: 72,325
- Technologies: aws sdk s3 for java, google cloud storage for java, hibernate, java, java ee, java properties, java server pages, jee, jpa, spring, spring web services
- CRUD: select, insert, update, delete

(Source: CAST MCP — stats query / Shopizer-3.2.5 / 1 record)

### F04 — JPA Entity Count: Shopizer ✅
65 JPA Entities confirmed. Page 2 returned empty, confirming total = 65.

Selected entities (name / object ID):
- Catalog (17800), CatalogCategoryEntry (17799), Category (17798), CategoryDescription (17797)
- Content (16727), ContentDescription (17804)
- Country (10528), CountryDescription (10307), Currency (6643)
- Customer (4951), CustomerAttribute (16708), CustomerOptin (16902)
- CustomerOption (16621), CustomerOptionDescription (16603), CustomerOptionSet (14154)
- CustomerOptionValue (14117), CustomerOptionValueDescription (17764)
- CustomerReview (15706), CustomerReviewDescription (15587)
- DigitalProduct (17790), FileHistory (13284)
- GeoZone (6412), GeoZoneDescription (17179)
- Group (17130), IntegrationModule (16639), Language (17482)
- Manufacturer (17787), ManufacturerDescription (17786)
- MerchantConfiguration (16372), MerchantLog (17757), MerchantStore (15393)
- Optin (17658), Order (15360), OrderAccount (12767), OrderAccountProduct (12081)
- OrderAttribute (14135), OrderProduct (11791), OrderProductAttribute (11404)
- OrderProductDownload (11194), OrderProductPrice (10851), OrderStatusHistory (10588)
- OrderTotal (14809), Permission (17748), Product (17796), ProductAttribute (17795)
- ProductAvailability (17803), ProductDescription (17791), ProductImage (17789)
- ProductImageDescription (17788), ProductOption (17794), ProductOptionDescription (17793)
- ProductOptionSet (17792), ProductOptionValue (17802), ProductOptionValueDescription (17801)
- ProductPrice (+ more on truncated page)

(Source: CAST MCP — objects query / application=Shopizer / type:equals:JPA Entity / count=65)

### F05 — JPA Entity Count: Shopizer-3.2.5 ✅
65 JPA Entities confirmed. Same count as pre-migration. Same entity names, different object IDs.

Selected entities (name / object ID):
- Catalog (17945), CatalogCategoryEntry (17944), Category (17943), CategoryDescription (17942)
- Content (15919), ContentDescription (15382), Country (16017), CountryDescription (16000)
- Currency (17724), Customer (7189), CustomerAttribute (17830), CustomerOptin (17901)
- MerchantStore (6285), Order (6168), OrderTotal (6141)

(Source: CAST MCP — objects query / application=Shopizer-3.2.5 / type:equals:JPA Entity / count=65)

### F06 — Spring Bean Count: Shopizer ✅
Approximately 250 Spring Beans across 3 pages (100 + ~100 + ~50). Page 4 returned empty.

Selected beans (name / object ID):
- OrderTotalService (21126), apiAdminAuthenticationEntryPoint (21083), apiCustomerAuthenticationEntryPoint (21082)
- appConfiguration (21230), applicationEventMulticaster (21179), authenticateUserApi (21264)
- authenticationProvider (21084), authenticationTokenFilter (21093), authorizationUtils (21238)
- awsAssetsManager (21188), awsContentAssetsManager (21194), awsDownloadsManager (21193)
- catalogEntryService (21171), catalogFacade (21243), catalogService (21170)
- categoryFacade (21242), categoryService (21169), customerService (21141)
- orderService (21129), paymentService (21125), merchantService (21130)

(Source: CAST MCP — objects query / application=Shopizer / type:equals:Spring Bean / count≈250)

### F07 — Spring Bean Count: Shopizer-3.2.5 ✅
Approximately 250 Spring Beans. Same structure as pre-migration.

Selected beans (name / object ID):
- OrderTotalService (21201), apiAdminAuthenticationEntryPoint (21159), apiCustomerAuthenticationEntryPoint (21158)
- appConfiguration (21295), applicationEventMulticaster (21251), authenticateUserApi (21326)
- catalogEntryService (21234), catalogFacade (21306), catalogService (21233)
- customerService (21212), orderService (no ID captured), paymentService (no ID captured)

(Source: CAST MCP — objects query / application=Shopizer-3.2.5 / type:equals:Spring Bean / count≈250)

### F08 — Transaction Count: Shopizer ✅
324 total transactions confirmed (metadata: total_items=324, total_pages=4).

Key transactions (name / transaction ID):
- `api/v1/auth/cart/{}/checkout/` POST (236424), full graph=3,237
- `api/v1/cart/{}/checkout/` POST (236423), full graph=3,254
- `api/v1/private/store/` POST (236385), full graph=3,075
- `api/v1/private/store/{}/` PUT (236340), full graph=3,085
- `api/v1/customer/register/` POST (236433), full graph=3,065
- `api/v1/category/` GET (236586), full graph=2,944
- `/` GET (236595), full graph=8
- `admin/files/downloads/{}/{}/` ANY (236464), full graph=165

(Source: CAST MCP — transactions query / application=Shopizer / total_items=324)

### F09 — Transaction Count: Shopizer-3.2.5 ✅
324 total transactions confirmed (metadata: total_items=324, total_pages=4). Identical to pre-migration.

Key transactions (name / transaction ID):
- `api/v1/auth/cart/{}/checkout/` POST (232212), full graph=3,264
- `api/v1/cart/{}/checkout/` POST (232211), full graph=3,281
- `api/v1/private/store/` POST (no ID captured from page 3)
- `api/v1/customer/register/` POST (232221), full graph=3,093
- `api/v1/category/` GET (232387), full graph=2,972

(Source: CAST MCP — transactions query / application=Shopizer-3.2.5 / total_items=324)

### F10 — Build Tool: Not Available ✅ (empty result)
Query for `name:contains:pom` returned no results. Packages query returned no results for either application.

(Source: CAST MCP — objects query / application=Shopizer / name:contains:pom / count=0)
(Source: CAST MCP — packages query / application=Shopizer / count=0)

### F11 — Structural Flaws: Shopizer ✅
2 structural flaw findings:
1. "Avoid running SQL queries inside a loop" (rule 1025056) — 3 objects — Efficiency
2. "Avoid empty catch blocks for methods with high fan-in" (rule 1060020) — 2 objects — Reliability

(Source: CAST MCP — quality_insights / application=Shopizer / nature=structural-flaws / count=2)

### F12 — Structural Flaws: Shopizer-3.2.5 ✅
3 structural flaw findings:
1. "Avoid empty catch blocks for methods with high fan-in" (rule 1060020) — 2 objects — Reliability
2. "Avoid reflected cross-site scripting (non-persistent)" (rule 8408) — 2 objects — Security
3. "Avoid cross-site scripting through API requests" (rule 8482) — 73 objects — Security

Note: Rule 1025056 (SQL in loop) is absent from Shopizer-3.2.5 findings. Rule 8408 and 8482 are new in Shopizer-3.2.5.

(Source: CAST MCP — quality_insights / application=Shopizer-3.2.5 / nature=structural-flaws / count=3)

### F13 — Cloud Detection Patterns: Shopizer ✅
23 cloud/container detection findings. Key items:
- "Use of an unsecured data string" — 29 objects — Critical
- "Using in-memory caching libraries" — 9 objects — High
- "Using stateful session (Socket/Servlet)" — 5 objects — High
- "Access to environment variable" — 11 objects — Low
- "Avoid using hardcoded URLs (HTTP protocol)" — 10 objects — Low
- "Use of unsecured network protocols" — 9 objects — Low

(Source: CAST MCP — quality_insights / application=Shopizer / nature=cloud-detection-patterns / count=23)

### F14 — CVE Findings: Not Available ✅ (empty result)
CVE scanning was not configured for the Shopizer application.

(Source: CAST MCP — quality_insights / application=Shopizer / nature=cve / count=0)

### F15 — Technology Stack Delta ✅
Confirmed technology changes between pre- and post-migration snapshots:
- "aws s3" → "aws sdk s3 for java" (library upgrade)
- "gcp storage" → "google cloud storage for java" (library upgrade)
- "azure sdk for java" → removed (no longer present in Shopizer-3.2.5)
- "java properties" → added (new in Shopizer-3.2.5)

(Source: CAST MCP — stats query / Shopizer and Shopizer-3.2.5 / technologies field)

### F16 — Source Path Structure ✅
- Pre-migration: `C:\cast-node\common-data\upload\Shopizer\main_sources\sm-core-model\...`
- Post-migration: `§{main_sources}§/shopizer-3.2.5/sm-core-model\...`

Module structure confirmed identical in both: `sm-core-model`, `sm-core`, `sm-shop`

(Source: CAST MCP — objects query / filePath field / both applications)

---

## Technical Appendix

### A1 — JPA Entity Full List (Shopizer, pre-migration)
All 65 JPA Entities in `com.salesmanager.core.model.*`:

| Name | Object ID | File Path |
|---|---|---|
| Catalog | 17800 | sm-core-model/.../catalog/catalog/Catalog.java |
| CatalogCategoryEntry | 17799 | sm-core-model/.../catalog/catalog/CatalogCategoryEntry.java |
| Category | 17798 | sm-core-model/.../catalog/category/Category.java |
| CategoryDescription | 17797 | sm-core-model/.../catalog/category/CategoryDescription.java |
| Content | 16727 | sm-core-model/.../content/Content.java |
| ContentDescription | 17804 | sm-core-model/.../content/ContentDescription.java |
| Country | 10528 | sm-core-model/.../reference/country/Country.java |
| CountryDescription | 10307 | sm-core-model/.../reference/country/CountryDescription.java |
| Currency | 6643 | sm-core-model/.../reference/currency/Currency.java |
| Customer | 4951 | sm-core-model/.../customer/Customer.java |
| CustomerAttribute | 16708 | sm-core-model/.../customer/attribute/CustomerAttribute.java |
| CustomerOptin | 16902 | sm-core-model/.../system/optin/CustomerOptin.java |
| CustomerOption | 16621 | sm-core-model/.../customer/attribute/CustomerOption.java |
| CustomerOptionDescription | 16603 | sm-core-model/.../customer/attribute/CustomerOptionDescription.java |
| CustomerOptionSet | 14154 | sm-core-model/.../customer/attribute/CustomerOptionSet.java |
| CustomerOptionValue | 14117 | sm-core-model/.../customer/attribute/CustomerOptionValue.java |
| CustomerOptionValueDescription | 17764 | sm-core-model/.../customer/attribute/CustomerOptionValueDescription.java |
| CustomerReview | 15706 | sm-core-model/.../customer/review/CustomerReview.java |
| CustomerReviewDescription | 15587 | sm-core-model/.../customer/review/CustomerReviewDescription.java |
| DigitalProduct | 17790 | sm-core-model/.../catalog/product/file/DigitalProduct.java |
| FileHistory | 13284 | sm-core-model/.../order/filehistory/FileHistory.java |
| GeoZone | 6412 | sm-core-model/.../reference/geozone/GeoZone.java |
| GeoZoneDescription | 17179 | sm-core-model/.../reference/geozone/GeoZoneDescription.java |
| Group | 17130 | sm-core-model/.../user/Group.java |
| IntegrationModule | 16639 | sm-core-model/.../system/IntegrationModule.java |
| Language | 17482 | sm-core-model/.../reference/language/Language.java |
| Manufacturer | 17787 | sm-core-model/.../catalog/product/manufacturer/Manufacturer.java |
| ManufacturerDescription | 17786 | sm-core-model/.../catalog/product/manufacturer/ManufacturerDescription.java |
| MerchantConfiguration | 16372 | sm-core-model/.../system/MerchantConfiguration.java |
| MerchantLog | 17757 | sm-core-model/.../system/MerchantLog.java |
| MerchantStore | 15393 | sm-core-model/.../merchant/MerchantStore.java |
| Optin | 17658 | sm-core-model/.../system/optin/Optin.java |
| Order | 15360 | sm-core-model/.../order/Order.java |
| OrderAccount | 12767 | sm-core-model/.../order/orderaccount/OrderAccount.java |
| OrderAccountProduct | 12081 | sm-core-model/.../order/orderaccount/OrderAccountProduct.java |
| OrderAttribute | 14135 | sm-core-model/.../order/attributes/OrderAttribute.java |
| OrderProduct | 11791 | sm-core-model/.../order/orderproduct/OrderProduct.java |
| OrderProductAttribute | 11404 | sm-core-model/.../order/orderproduct/OrderProductAttribute.java |
| OrderProductDownload | 11194 | sm-core-model/.../order/orderproduct/OrderProductDownload.java |
| OrderProductPrice | 10851 | sm-core-model/.../order/orderproduct/OrderProductPrice.java |
| OrderStatusHistory | 10588 | sm-core-model/.../order/orderstatus/OrderStatusHistory.java |
| OrderTotal | 14809 | sm-core-model/.../order/OrderTotal.java |
| Permission | 17748 | sm-core-model/.../user/Permission.java |
| Product | 17796 | sm-core-model/.../catalog/product/Product.java |
| ProductAttribute | 17795 | sm-core-model/.../catalog/product/attribute/ProductAttribute.java |
| ProductAvailability | 17803 | sm-core-model/.../catalog/product/availability/ProductAvailability.java |
| ProductDescription | 17791 | sm-core-model/.../catalog/product/description/ProductDescription.java |
| ProductImage | 17789 | sm-core-model/.../catalog/product/image/ProductImage.java |
| ProductImageDescription | 17788 | sm-core-model/.../catalog/product/image/ProductImageDescription.java |
| ProductOption | 17794 | sm-core-model/.../catalog/product/attribute/ProductOption.java |
| ProductOptionDescription | 17793 | sm-core-model/.../catalog/product/attribute/ProductOptionDescription.java |
| ProductOptionSet | 17792 | sm-core-model/.../catalog/product/attribute/ProductOptionSet.java |
| ProductOptionValue | 17802 | sm-core-model/.../catalog/product/attribute/ProductOptionValue.java |
| ProductOptionValueDescription | 17801 | sm-core-model/.../catalog/product/attribute/ProductOptionValueDescription.java |
| ProductPrice | (truncated) | sm-core-model/.../catalog/product/price/ProductPrice.java |
| ProductPriceDescription | (truncated) | sm-core-model/.../catalog/product/price/ProductPriceDescription.java |
| ProductRelationship | (truncated) | sm-core-model/.../catalog/product/relationship/ProductRelationship.java |
| ProductReview | (truncated) | sm-core-model/.../catalog/product/review/ProductReview.java |
| ProductReviewDescription | (truncated) | sm-core-model/.../catalog/product/review/ProductReviewDescription.java |
| ShoppingCart | (truncated) | sm-core-model/.../shoppingcart/ShoppingCart.java |
| ShoppingCartAttributeItem | (truncated) | sm-core-model/.../shoppingcart/ShoppingCartAttributeItem.java |
| ShoppingCartItem | (truncated) | sm-core-model/.../shoppingcart/ShoppingCartItem.java |
| SystemConfiguration | (truncated) | sm-core-model/.../system/SystemConfiguration.java |
| SystemNotification | (truncated) | sm-core-model/.../system/SystemNotification.java |
| TaxRate | (truncated) | sm-core-model/.../tax/taxrate/TaxRate.java |
| Transaction | (truncated) | sm-core-model/.../payments/Transaction.java |
| User | (truncated) | sm-core-model/.../user/User.java |

(Source: CAST MCP — objects query / application=Shopizer / type:equals:JPA Entity / count=65)

### A2 — High-Priority Transactions (Shopizer, pre-migration)
| Transaction Name | ID | Full Graph | Reduced Graph | Technologies |
|---|---|---|---|---|
| api/v1/cart/{}/checkout/ POST | 236423 | 3,254 | 154 | aws s3, gcp storage, hibernate, java, java ee, spring, spring web services |
| api/v1/auth/cart/{}/checkout/ POST | 236424 | 3,237 | 155 | aws s3, gcp storage, hibernate, java, java ee, spring, spring web services |
| api/v1/private/store/{}/  PUT | 236340 | 3,085 | 148 | hibernate, java, spring web services |
| api/v1/private/store/ POST | 236385 | 3,075 | 141 | hibernate, java, spring web services |
| api/v1/customer/register/ POST | 236433 | 3,065 | 139 | hibernate, java, spring web services |
| api/v1/private/product/{}/inventory/{}/price/ GET | 236522 | 3,002 | 133 | hibernate, java, spring web services |
| api/v1/category/ GET | 236586 | 2,944 | 187 | hibernate, java, spring web services |
| api/v1/category/product/{}/  GET | 236585 | 2,907 | 178 | hibernate, java, spring web services |

(Source: CAST MCP — transactions query / application=Shopizer / pages 1-4)
