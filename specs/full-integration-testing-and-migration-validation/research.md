# Research Findings: Shopizer-3.2.5

## BCM Scope Notice
⚠️ **Standing Compliance Gap (GR-08)**: No BCM subsystem was provided. All queries executed application-wide.

## CAST Snapshot Information
- Application name: `Shopizer-3.2.5`
- Delivery name: `Onboarding-202607301729`
- Delivery date: `2026-07-30T17:29:00`
- CAST snapshot ID: Not exposed by tool — stated explicitly per GR-03.

---

## Query Log

| # | Tool/Query | Scope Filter | Raw Result Count | Disposition |
|---|---|---|---|---|
| Q01 | `applications` | none | 9 applications | run-returned |
| Q02 | `stats` | application=Shopizer-3.2.5 | 1 record | run-returned |
| Q03 | `objects` | type:contains:JPA Entity | 50+ items (page 1, mixed JPA Entity + JPA Entity Operation) | run-returned |
| Q04 | `objects` | type:equals:JPA Entity | 63 items (page 1 only) | run-returned |
| Q05 | `objects` | type:equals:JPA Entity, page=2 | 0 items | run-returned (empty) |
| Q06 | `objects` | type:equals:Spring Bean | 100 items (page 1) | run-returned |
| Q07 | `objects` | type:equals:Spring Bean, page=2 | 100 items (page 2) | run-returned |
| Q08 | `objects` | type:equals:Spring Bean, page=3 | 100 items (page 3) | run-returned |
| Q09 | `objects` | type:contains:Spring MVC | 100 items (page 1) | run-returned |
| Q10 | `objects` | type:contains:Spring MVC, page=2 | 100 items (page 2) | run-returned |
| Q11 | `objects` | type:contains:Spring MVC, page=3 | 100 items (page 3) | run-returned |
| Q12 | `objects` | type:contains:Spring MVC, page=4 | 24 items (page 4, last); metadata total_items=324 | run-returned |
| Q13 | `objects` | type:equals:Java Properties File | 42 items; metadata total_items=42 | run-returned |
| Q14 | `objects` | type:equals:J2EE Scoped Bean | 2 items; metadata total_items=2 | run-returned |
| Q15 | `packages` | application=Shopizer-3.2.5 | 0 | run-returned (empty — "No packages in this application") |
| Q16 | `transactions` | application=Shopizer-3.2.5 | 100 items (page 1) | run-returned |
| Q17 | `quality_insights` | nature=structural-flaws | 3 rules; metadata total_items=3 | run-returned |
| Q18 | `quality_insights` | nature=cve | 0 | run-returned (empty — "scanning not configured") |

**Unqueried types (logged as out-of-scope per GR-09/GR-11):**
- Batch/scheduled job entry points: Out of scope for this use case — not queried.
- Message-listener entry points (JMS/MQ/Kafka): Out of scope for this use case — not queried.
- `cloud-detection-patterns` quality insights: Out of scope for this use case — not queried.
- `green-detection-patterns` quality insights: Out of scope for this use case — not queried.
- `iso-5055` quality insights: Out of scope for this use case — not queried.

---

## Confirmed Facts (✅ direct CAST result)

### Application Stats
- LOC: 91,162 ✅ (Source: CAST MCP — stats / Shopizer-3.2.5 / nb_LOC=91162)
- Elements: 16,572 ✅ (Source: CAST MCP — stats / Shopizer-3.2.5 / nb_elements=16572)
- Interactions: 72,325 ✅ (Source: CAST MCP — stats / Shopizer-3.2.5 / nb_interactions=72325)
- CRUD interactions: select, insert, update, delete ✅ (Source: CAST MCP — stats / Shopizer-3.2.5)

### Technologies
Technologies confirmed: aws sdk s3 for java, google cloud storage for java, hibernate, java, java ee, java properties, java server pages, jee, jpa, spring, spring web services ✅ (Source: CAST MCP — stats / Shopizer-3.2.5 / technologies)

### Element Types Confirmed Present
Generic Java Class, Generic Java Interface, J2EE Scoped Bean, JPA Entity, Java AWS S3 Bucket, Java AWS Unknown S3 Bucket, Java Class, Java Enum, Java GCP Cloud Storage Bucket, Java GCP Unknown Cloud Storage Bucket, Java Get Resource Service, Java Interface, Java Post Resource Service, Java Properties File, Missing Table, Spring Bean, Spring MVC Any Operation, Spring MVC Delete Operation, Spring MVC Get Operation, Spring MVC Post Operation, Spring MVC Put Operation, System Schema, Java Method, Generic Java Method, JPQL Query, Java Field, Java Constructor, Java Instantiated Constructor, JPA Unknown SQL Query, Java Enum Item, JPA Entity Operation, Java Annotation Type, Java Initializer, Java Annotation Type Method, System Table ✅ (Source: CAST MCP — stats / Shopizer-3.2.5 / element_types)

---

## Technical Appendix

### A1. JPA Entities (Q04 — type:equals:JPA Entity — 63 objects)

(Source: CAST MCP — objects query / type:equals:JPA Entity / count=63)

| Object Name | Object ID | File Path |
|---|---|---|
| Catalog | 17945 | sm-core-model/.../catalog/catalog/Catalog.java |
| CatalogCategoryEntry | 17944 | sm-core-model/.../catalog/catalog/CatalogCategoryEntry.java |
| Category | 17943 | sm-core-model/.../catalog/category/Category.java |
| CategoryDescription | 17942 | sm-core-model/.../catalog/category/CategoryDescription.java |
| Content | 15919 | sm-core-model/.../content/Content.java |
| ContentDescription | 15382 | sm-core-model/.../content/ContentDescription.java |
| Country | 16017 | sm-core-model/.../reference/country/Country.java |
| CountryDescription | 16000 | sm-core-model/.../reference/country/CountryDescription.java |
| Currency | 17724 | sm-core-model/.../reference/currency/Currency.java |
| Customer | 7189 | sm-core-model/.../customer/Customer.java |
| CustomerAttribute | 17830 | sm-core-model/.../customer/attribute/CustomerAttribute.java |
| CustomerOptin | 17901 | sm-core-model/.../system/optin/CustomerOptin.java |
| CustomerOption | 17677 | sm-core-model/.../customer/attribute/CustomerOption.java |
| CustomerOptionDescription | 17662 | sm-core-model/.../customer/attribute/CustomerOptionDescription.java |
| CustomerOptionSet | 17786 | sm-core-model/.../customer/attribute/CustomerOptionSet.java |
| CustomerOptionValue | 17771 | sm-core-model/.../customer/attribute/CustomerOptionValue.java |
| CustomerOptionValueDescription | 17755 | sm-core-model/.../customer/attribute/CustomerOptionValueDescription.java |
| CustomerReview | 17519 | sm-core-model/.../customer/review/CustomerReview.java |
| CustomerReviewDescription | 16902 | sm-core-model/.../customer/review/CustomerReviewDescription.java |
| DigitalProduct | 17932 | sm-core-model/.../catalog/product/file/DigitalProduct.java |
| FileHistory | 17761 | sm-core-model/.../order/filehistory/FileHistory.java |
| GeoZone | 17698 | sm-core-model/.../reference/geozone/GeoZone.java |
| GeoZoneDescription | 17647 | sm-core-model/.../reference/geozone/GeoZoneDescription.java |
| Group | 17917 | sm-core-model/.../user/Group.java |
| IntegrationModule | 14882 | sm-core-model/.../system/IntegrationModule.java |
| Language | 17544 | sm-core-model/.../reference/language/Language.java |
| Manufacturer | 17946 | sm-core-model/.../catalog/product/manufacturer/Manufacturer.java |
| ManufacturerDescription | 17931 | sm-core-model/.../catalog/product/manufacturer/ManufacturerDescription.java |
| MerchantConfiguration | 14867 | sm-core-model/.../system/MerchantConfiguration.java |
| MerchantLog | 14673 | sm-core-model/.../system/MerchantLog.java |
| MerchantStore | 6285 | sm-core-model/.../merchant/MerchantStore.java |
| Optin | 17886 | sm-core-model/.../system/optin/Optin.java |
| Order | 6168 | sm-core-model/.../order/Order.java |
| OrderAccount | 17730 | sm-core-model/.../order/orderaccount/OrderAccount.java |
| OrderAccountProduct | 17672 | sm-core-model/.../order/orderaccount/OrderAccountProduct.java |
| OrderAttribute | 17848 | sm-core-model/.../order/attributes/OrderAttribute.java |
| OrderProduct | 17266 | sm-core-model/.../order/orderproduct/OrderProduct.java |
| OrderProductAttribute | 17203 | sm-core-model/.../order/orderproduct/OrderProductAttribute.java |
| OrderProductDownload | 16579 | sm-core-model/.../order/orderproduct/OrderProductDownload.java |
| OrderProductPrice | 16251 | sm-core-model/.../order/orderproduct/OrderProductPrice.java |
| OrderStatusHistory | 16233 | sm-core-model/.../order/orderstatus/OrderStatusHistory.java |
| OrderTotal | 6141 | sm-core-model/.../order/OrderTotal.java |
| Permission | 17916 | sm-core-model/.../user/Permission.java |
| Product | 17941 | sm-core-model/.../catalog/product/Product.java |
| ProductAttribute | 17940 | sm-core-model/.../catalog/product/attribute/ProductAttribute.java |
| ProductAvailability | 17934 | sm-core-model/.../catalog/product/availability/ProductAvailability.java |
| ProductDescription | 17933 | sm-core-model/.../catalog/product/description/ProductDescription.java |
| ProductImage | 17948 | sm-core-model/.../catalog/product/image/ProductImage.java |
| ProductImageDescription | 17947 | sm-core-model/.../catalog/product/image/ProductImageDescription.java |
| ProductOption | 17939 | sm-core-model/.../catalog/product/attribute/ProductOption.java |
| ProductOptionDescription | 17938 | sm-core-model/.../catalog/product/attribute/ProductOptionDescription.java |
| ProductOptionSet | 17937 | sm-core-model/.../catalog/product/attribute/ProductOptionSet.java |
| ProductOptionValue | 17936 | sm-core-model/.../catalog/product/attribute/ProductOptionValue.java |
| ProductOptionValueDescription | 17935 | sm-core-model/.../catalog/product/attribute/ProductOptionValueDescription.java |
| ProductPrice | 17930 | sm-core-model/.../catalog/product/price/ProductPrice.java |
| ProductPriceDescription | 17929 | sm-core-model/.../catalog/product/price/ProductPriceDescription.java |
| ProductRelationship | 17928 | sm-core-model/.../catalog/product/relationship/ProductRelationship.java |
| ProductReview | 17927 | sm-core-model/.../catalog/product/review/ProductReview.java |
| ProductReviewDescription | 17926 | sm-core-model/.../catalog/product/review/ProductReviewDescription.java |
| SystemConfiguration | (no ID returned — in truncated Q04 results) | sm-core-model/.../system/SystemConfiguration.java |
| SystemNotification | (no ID returned — in truncated Q04 results) | sm-core-model/.../system/SystemNotification.java |
| Transaction | (no ID returned — in truncated Q04 results) | sm-core-model/.../payments/Transaction.java |
| TaxRate | (no ID returned — in truncated Q04 results) | sm-core-model/.../tax/taxrate/TaxRate.java |
| User | (no ID returned — in truncated Q04 results) | sm-core-model/.../user/User.java |

### A2. Key Spring Beans (Q06–Q08 — selected entries)

(Source: CAST MCP — objects query / type:equals:Spring Bean / count≥200 across 3 pages)

| Bean Name | Object ID | File Path |
|---|---|---|
| OrderTotalService | 21201 | sm-core/.../order/ordertotal/OrderTotalServiceImpl.java |
| apiAdminAuthenticationEntryPoint | 21159 | sm-shop/.../config/MultipleEntryPointsSecurityConfig.java |
| apiCustomerAuthenticationEntryPoint | 21158 | sm-shop/.../config/MultipleEntryPointsSecurityConfig.java |
| authenticationProvider | 21160 | sm-shop/.../config/MultipleEntryPointsSecurityConfig.java |
| authenticationTokenFilter | 21169 | sm-shop/.../config/MultipleEntryPointsSecurityConfig.java |
| passwordEncoder | 21167 | sm-shop/.../config/MultipleEntryPointsSecurityConfig.java |
| awsAssetsManager | 21259 | sm-core/.../resources/spring/shopizer-core-cms.xml |
| awsContentAssetsManager | 21147 | sm-core/.../resources/spring/shopizer-core-cms.xml |
| awsDownloadsManager | 21129 | sm-core/.../resources/spring/shopizer-core-cms.xml |
| awsProductAssetsManager | 21164 | sm-core/.../resources/spring/shopizer-core-cms.xml |
| sesEmailSender | 21237 | sm-core/.../modules/email/SESEmailSenderImpl.java |
| orderService | 21204 | sm-core/.../services/order/OrderServiceImpl.java |
| customerService | 21212 | sm-core/.../services/customer/CustomerServiceImpl.java |
| paymentService | 21200 | sm-core/.../services/payments/PaymentServiceImpl.java |
| shippingService | 21189 | sm-core/.../services/shipping/ShippingServiceImpl.java |
| catalogService | 21233 | sm-core/.../services/catalog/catalog/CatalogServiceImpl.java |
| categoryService | 21243 | sm-core/.../services/catalog/category/CategoryServiceImpl.java |
| merchantService | 21205 | sm-core/.../services/merchant/MerchantStoreServiceImpl.java |
| droolsBeanFactory | 21250 | sm-core/.../configuration/DroolsBeanFactory.java |
| dbCredentials | 21252 | sm-core/.../configuration/db/DbConfig.java |
| orderFacade | 21315 | sm-shop/.../controller/order/facade/OrderFacadeImpl.java |
| customerFacade | 21321 | sm-shop/.../controller/customer/facade/CustomerFacadeImpl.java |
| catalogFacade | 21306 | sm-shop/.../store/facade/catalog/CatalogFacadeImpl.java |
| categoryFacade | 21305 | sm-shop/.../store/facade/category/CategoryFacadeImpl.java |
| shippingFacade | 21311 | sm-shop/.../controller/shipping/facade/ShippingFacadeImpl.java |
| securityFacade | 21312 | sm-shop/.../controller/security/facade/SecurityFacadeImpl.java |
| authenticateUserApi | 21326 | sm-shop/.../store/api/v1/user/AuthenticateUserApi.java |
| applicationEventMulticaster | 21251 | sm-core/.../configuration/events/AsynchronousEventsConfiguration.java |
| publishProductAspect | 21249 | sm-core/.../configuration/events/products/PublishProductAspect.java |

### A3. Spring MVC Operations — Highest-Complexity Transactions (Q16)

(Source: CAST MCP — transactions / Shopizer-3.2.5 / page 1)

| Transaction Name | Transaction ID | Full Graph Size | Reduced Graph Size | Stack |
|---|---|---|---|---|
| api/v1/cart/{}/checkout/ (POST) | 232211 | 3,281 | 154 | aws sdk s3, gcp, hibernate, java, java ee, spring web services |
| api/v1/auth/cart/{}/checkout/ (POST) | 232212 | 3,264 | 155 | aws sdk s3, gcp, hibernate, java, java ee, spring web services |
| api/v1/customer/register/ (POST) | 232221 | 3,093 | 139 | hibernate, java, spring web services |
| api/v1/category/ (GET) | 232387 | 2,972 | 187 | hibernate, java, spring web services |
| api/v1/category/{} (GET) | 232390 | 2,936 | 185 | hibernate, java, spring web services |
| api/v1/category/product/{} (GET) | 232386 | 2,935 | 178 | hibernate, java, spring web services |
| api/v1/category/{}/manufacturer/ (GET) | 232321 | 2,933 | 180 | hibernate, java, spring web services |
| api/v1/auth/cart/{}/shipping/ (GET) | 232349 | 1,220 | 62 | hibernate, java, java ee, jee, spring web services |
| api/v1/cart/{}/checkout/ (POST, auth) | 232212 | 3,264 | 155 | aws sdk s3, gcp, hibernate, java, java ee, spring web services |

### A4. Quality Findings (Q17 — structural-flaws)

(Source: CAST MCP — quality_insights / nature=structural-flaws / total_items=3)

| Rule ID | Rule Name | Affected Objects | Factors | CWE Categories |
|---|---|---|---|---|
| 1060020 | Avoid empty catch blocks for methods with high fan-in | 2 | Reliability | AIP-CWE-1069 |
| 8408 | Avoid reflected cross-site scripting (non persistent) | 2 | Security | CWE-79, CWE-89, CWE-78, CWE-77, CWE-119, CWE-120, CWE-676, CWE-943 |
| 8482 | Avoid cross-site scripting through API requests | 73 | Security | CWE-79, CWE-89, CWE-78, CWE-77, CWE-119, CWE-120, CWE-676, CWE-943 |

### A5. Java Properties Files (Q13 — 42 files)

(Source: CAST MCP — objects query / type:equals:Java Properties File / total_items=42)

| File Name | Object ID | Full Path |
|---|---|---|
| application-test.properties | 25112 | sm-shop/src/test/resources/application-test.properties |
| application.properties | 8412 | sm-shop/src/main/resources/application.properties |
| application.properties | 9513 | sm-core/src/test/resources/application.properties |
| authentication.properties | 12677 | sm-core/src/main/resources/authentication.properties |
| database.properties | 6643 | sm-shop/.../profiles/docker/database.properties |
| database.properties | 6661 | sm-shop/.../profiles/dependency/database.properties |
| database.properties | 7067 | sm-shop/.../profiles/cloud/database.properties |
| database.properties | 7318 | sm-shop/src/main/resources/database.properties |
| database.properties | 9485 | sm-core/src/test/resources/database.properties |
| database.properties | 25016 | sm-shop/.../profiles/mysql/database.properties |
| database.properties | 25042 | sm-shop/.../profiles/local/database.properties |
| database.properties | 25069 | sm-shop/.../profiles/gcp/database.properties |
| database.properties | 25111 | sm-shop/src/test/resources/database.properties |
| email.properties | 12588 | sm-core/src/main/resources/email.properties |
| hbm2dll.properties | 9322 | sm-core/src/test/resources/hbm2dll.properties |
| log4j.properties | 9250 | sm-core/src/test/resources/log4j.properties |
| log4j.properties | 25110 | sm-shop/src/test/resources/log4j.properties |
| maven-wrapper.properties | 8497 | sm-shop/.mvn/wrapper/maven-wrapper.properties |
| maven-wrapper.properties | 8528 | sm-shop-model/.mvn/wrapper/maven-wrapper.properties |
| maven-wrapper.properties | 12906 | sm-core/.mvn/wrapper/maven-wrapper.properties |
| maven-wrapper.properties | 13264 | sm-core-modules/.mvn/wrapper/maven-wrapper.properties |
| maven-wrapper.properties | 13347 | sm-core-model/.mvn/wrapper/maven-wrapper.properties |
| messages.properties | 8358 | sm-shop/src/main/resources/bundles/messages.properties |
| messages_fr.properties | 8173 | sm-shop/src/main/resources/bundles/messages_fr.properties |
| payment.properties | 25089 | sm-shop/src/main/resources/bundles/payment.properties |
| payment_fr.properties | 7977 | sm-shop/src/main/resources/bundles/payment_fr.properties |
| shipping.properties | 7937 | sm-shop/src/main/resources/bundles/shipping.properties |
| shipping_fr.properties | 7812 | sm-shop/src/main/resources/bundles/shipping_fr.properties |
| shopizer-core.properties | 9527 | sm-core/src/main/resources/shopizer-core.properties |
| shopizer-core.properties | 10041 | sm-core/.../profiles/mysql/shopizer-core.properties |
| shopizer-core.properties | 9235 | sm-core/src/test/resources/shopizer-core.properties |
| shopizer-core.properties | 10193 | sm-core/.../profiles/local/shopizer-core.properties |
| shopizer-core.properties | 10244 | sm-core/.../profiles/gcp/shopizer-core.properties |
| shopizer-core.properties | 11425 | sm-core/.../profiles/dependency/shopizer-core.properties |
| shopizer-core.properties | 12314 | sm-core/.../profiles/cloud/shopizer-core.properties |
| shopizer-core.properties | 12570 | sm-core/.../profiles/aws/shopizer-core.properties |
| shopizer-properties.properties | 8832 | sm-core/src/test/resources/shopizer-properties.properties |
| shopizer-properties.properties | 24990 | sm-shop/src/main/resources/shopizer-properties.properties |
| shopizer.properties | 7578 | sm-shop/src/main/resources/bundles/shopizer.properties |
| shopizer_fr.properties | 7426 | sm-shop/src/main/resources/bundles/shopizer_fr.properties |
| vault.properties | 8598 | sm-core/src/test/resources/vault.properties |
| vault.properties | 25113 | sm-shop/src/main/resources/vault.properties |

### A6. J2EE Scoped Beans (Q14)

(Source: CAST MCP — objects query / type:equals:J2EE Scoped Bean / total_items=2)

| Bean Name | Object ID | Scope | Source File |
|---|---|---|---|
| LANGUAGE | 1924 | sessionScope | sm-shop/.../utils/LanguageUtils.java |
| SPRING_SECURITY_CONTEXT | 1925 | sessionScope | sm-shop/.../admin/security/AbstractAuthenticatinSuccessHandler.java |

---

## Inferred Facts (⚠️ structurally inferred — SME validation required)

- ⚠️ The presence of `java ee` and `jee` in the technology stack suggests Java EE APIs (potentially `javax.*` namespaces) are in use. If a Spring Boot 3.x migration is planned, `javax.*` → `jakarta.*` migration would be required. The exact count of affected files was not queried in this session.
- ⚠️ The 5 `maven-wrapper.properties` files (one per module) confirm Maven as the build tool, but the specific Maven version and Spring Boot version are not confirmed by CAST.
- ⚠️ The presence of `droolsBeanFactory` (ID: 21250) suggests Drools rules engine integration, which may require separate migration validation.
- ⚠️ The presence of `dbCredentials` bean (ID: 21252) in `DbConfig.java` suggests database credential management that may need validation in target environments.
- ⚠️ The `publishProductAspect` bean (ID: 21249) and `applicationEventMulticaster` bean (ID: 21251) suggest AOP and async event processing, which may require validation during migration.

## Not Available / Not Queried

- CVE scanning results: Not available in CAST MCP — query ran, returned "scanning not configured." (Q18)
- Packages/external dependencies: Not available in CAST MCP — query ran, returned "No packages in this application." (Q15)
- Column-level SQL schema detail: Out of scope for this use case — not queried.
- Batch/scheduled job entry points: Out of scope for this use case — not queried.
- Message-listener entry points: Out of scope for this use case — not queried.
- `cloud-detection-patterns` quality insights: Out of scope for this use case — not queried.
- `green-detection-patterns` quality insights: Out of scope for this use case — not queried.
- `iso-5055` quality insights: Out of scope for this use case — not queried.
- Specific Spring Boot version: Not available in CAST MCP — no packages returned. (Q15)
- Java version: Not available in CAST MCP — no packages returned. (Q15)
- Spring Bean total count (exact): Query ran across 3 pages of 100 items each; page 4 not queried. Minimum confirmed: 200+ Spring Beans. Exact total not confirmed.
