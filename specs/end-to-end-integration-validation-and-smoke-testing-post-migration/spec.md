# Specification: End-to-End Integration Validation and Smoke Testing Post-Migration
## Application: Shopizer

---

## ⚠️ BCM Scope Gap (GR-08)
No BCM (Business Capability Model) subsystem was provided. All queries were executed application-wide. This is a standing compliance gap. Every deliverable in this Spec Kit is flagged accordingly. SME validation is required to confirm scope boundaries before implementation begins.

---

## 1. Overview

This specification defines the end-to-end integration validation and smoke testing strategy for the Shopizer e-commerce application following a migration. CAST Imaging contains two analyzed snapshots of the application:

- **Shopizer** — pre-migration snapshot (delivery: 2026-07-10)
- **Shopizer-3.2.5** — post-migration snapshot (delivery: 2026-07-30)

Both snapshots share the same codebase size (91,162 lines of code) and identical transaction surface (324 Spring MVC endpoints), but differ in technology stack composition, element counts, and quality findings. The smoke testing suite must validate that all 324 API endpoints function correctly in the migrated version.

---

## 2. Current State (Pre-Migration: "Shopizer")

### 2.1 Application Metrics
- **Lines of Code**: 91,162
- **Total Elements**: 16,468
- **Total Interactions**: 72,524
- **Technologies**: aws s3, azure sdk for java, gcp storage, hibernate, java, java ee, java server pages, jee, jpa, spring, spring web services
- **Source root**: `C:\cast-node\common-data\upload\Shopizer\main_sources\`

### 2.2 Framework Object Counts
| Object Type | Count |
|---|---|
| JPA Entity | 65 |
| Spring Bean | ~250 (pages 1–3 of 100 items/page) |
| Spring MVC Transactions (all HTTP methods) | 324 |
| JPA Entity Operations | 18 |
| JPQL Queries | present (exact count: not queried separately) |

### 2.3 API Surface (324 Transactions)
The 324 transactions span three API version namespaces:
- `/api/v0/` — legacy REST endpoints (SystemRESTController, StoreContactRESTController)
- `/api/v1/` — primary REST API (cart, order, customer, product, store, shipping, tax, user, content, catalog)
- `/api/v2/` — extended REST API (ProductApiV2, ProductVariantApi, ProductVariantGroupApi, ProductVariationApi)
- Static file serving endpoints (`/static/files/`, `/static/products/`, `/admin/files/`)

### 2.4 Quality Findings (Pre-Migration)
| Rule | Count | Factor |
|---|---|---|
| Avoid running SQL queries inside a loop (1025056) | 3 objects | Efficiency |
| Avoid empty catch blocks for methods with high fan-in (1060020) | 2 objects | Reliability |

### 2.5 Cloud Readiness Findings (Pre-Migration)
| Finding | Count | Criticality |
|---|---|---|
| Use of an unsecured data string | 29 objects | Critical |
| Cross-site scripting via API requests | Not present in pre-migration | — |
| Using in-memory caching libraries | 9 objects | High |
| Using stateful session (Socket/Servlet) | 5 objects | High |
| Access to environment variable | 11 objects | Low |
| Hardcoded URLs (HTTP protocol) | 10 objects | Low |
| Use of unsecured network protocols | 9 objects | Low |

---

## 3. Post-Migration State ("Shopizer-3.2.5")

### 3.1 Application Metrics
- **Lines of Code**: 91,162 (unchanged)
- **Total Elements**: 16,572 (+104 vs pre-migration)
- **Total Interactions**: 72,325 (−199 vs pre-migration)
- **Technologies**: aws sdk s3 for java, google cloud storage for java, hibernate, java, java ee, java properties, java server pages, jee, jpa, spring, spring web services
- **Source root**: `§{main_sources}§/shopizer-3.2.5/`

### 3.2 Framework Object Counts (Post-Migration)
| Object Type | Count |
|---|---|
| JPA Entity | 65 (unchanged) |
| Spring Bean | ~250 (same structure) |
| Spring MVC Transactions | 324 (unchanged) |

### 3.3 Technology Stack Changes (CAST-Confirmed)
| Pre-Migration Technology | Post-Migration Technology | Status |
|---|---|---|
| aws s3 | aws sdk s3 for java | Changed |
| gcp storage | google cloud storage for java | Changed |
| azure sdk for java | (not present) | Removed |
| (not present) | java properties | Added |
| hibernate, java, jpa, spring, spring web services | hibernate, java, jpa, spring, spring web services | Unchanged |

### 3.4 Quality Findings (Post-Migration)
| Rule | Count | Factor | Delta vs Pre-Migration |
|---|---|---|---|
| Avoid empty catch blocks for methods with high fan-in (1060020) | 2 objects | Reliability | Same |
| Avoid reflected cross-site scripting (non-persistent) (8408) | 2 objects | Security | New |
| Avoid cross-site scripting through API requests (8482) | 73 objects | Security | New |

> ⚠️ The 73 XSS-via-API-requests findings in Shopizer-3.2.5 are new compared to the pre-migration snapshot. SME validation required to determine whether these represent newly introduced vulnerabilities or newly detected pre-existing issues.

---

## 4. Migration Delta Summary

| Dimension | Pre-Migration | Post-Migration | Delta |
|---|---|---|---|
| LOC | 91,162 | 91,162 | 0 |
| Elements | 16,468 | 16,572 | +104 |
| Interactions | 72,524 | 72,325 | −199 |
| Transactions | 324 | 324 | 0 |
| JPA Entities | 65 | 65 | 0 |
| Structural Flaws | 2 | 3 | +1 |
| Security Findings | 0 | 75 | +75 |
| Azure SDK dependency | Present | Absent | Removed |

---

## 5. Smoke Testing Scope

### 5.1 Entry Point Categories (GR-11 Separation)

**Online (REST/Spring MVC) — 324 transactions**
All 324 transactions are Spring MVC operations. No batch (scheduled jobs) or message-listener (JMS/Kafka) entry points were identified in CAST.

> Batch entry points: Not available in CAST MCP — query not run (no batch/scheduler types found in element_types list).
> Message-listener entry points: Not available in CAST MCP — no JMS/Kafka/MQ types in element_types list.

### 5.2 Critical Smoke Test Paths (by transaction size)
The following transactions have the largest full call graphs and represent the highest-risk integration paths:

| Endpoint | HTTP Method | Full Graph Size | Priority |
|---|---|---|---|
| `api/v1/private/store/` (POST) | POST | 3,075 | P1 |
| `api/v1/private/store/{}/` (PUT) | PUT | 3,085 | P1 |
| `api/v1/auth/cart/{}/checkout/` (POST) | POST | 3,254 | P1 |
| `api/v1/cart/{}/checkout/` (POST) | POST | 3,281 | P1 |
| `api/v1/customer/register/` (POST) | POST | 3,065 | P1 |
| `api/v1/private/product/{}/inventory/{}/price/` (GET) | GET | 3,002 | P1 |
| `api/v1/category/` (GET) | GET | 2,944 | P1 |
| `api/v1/category/product/{}/` (GET) | GET | 2,907 | P1 |

### 5.3 JPA Entity Coverage
All 65 JPA entities must be exercised through the smoke test suite. Key entities include:
- `Customer`, `Order`, `OrderProduct`, `Product`, `MerchantStore`, `ShoppingCart`
- `Category`, `Catalog`, `CatalogCategoryEntry`
- `ProductAvailability`, `ProductPrice`, `ProductImage`
- `Transaction`, `OrderStatusHistory`, `OrderTotal`

### 5.4 Technology Integration Points to Validate
Based on CAST technology stack changes:
1. **AWS S3 (sdk migration)**: Validate file upload/download endpoints (`api/v1/private/file/`, `api/v1/private/files/`, `api/v1/content/images/`, `static/files/`)
2. **GCP Storage (sdk migration)**: Validate image serving endpoints (`static/products/`, `static/files/`)
3. **Azure SDK removal**: Validate that shipping-related endpoints no longer depend on Azure SDK (pre-migration shipping transactions used `azure sdk for java`)
4. **Hibernate/JPA**: Validate all 65 JPA entity CRUD operations

---

## 6. Acceptance Criteria

### 6.1 Functional Acceptance
- All 324 Spring MVC transactions return expected HTTP status codes (2xx for valid requests, 4xx for invalid inputs)
- All 65 JPA entities can be created, read, updated, and deleted through their respective API endpoints
- Authentication flows (customer login, user login, token refresh) function correctly
- Shopping cart lifecycle (create, add item, checkout) completes end-to-end
- Order management (create, status update, payment) completes end-to-end

### 6.2 Technology Integration Acceptance
- AWS S3 file operations succeed using the migrated `aws sdk s3 for java` library
- GCP Storage image operations succeed using the migrated `google cloud storage for java` library
- No runtime errors related to removed Azure SDK dependency
- Hibernate/JPA entity persistence works for all 65 entities

### 6.3 Quality Acceptance
- The 2 empty catch block findings (rule 1060020) are reviewed and either remediated or accepted with documented rationale
- The 73 XSS-via-API-requests findings (rule 8482) are triaged — SME validation required to determine if these are new vulnerabilities introduced by migration
- The 3 SQL-in-loop findings from pre-migration are confirmed absent or documented in post-migration

### 6.4 Regression Acceptance
- Element count delta (+104) is explained and documented
- Interaction count delta (−199) is explained and documented
- No new structural flaws beyond those already present in pre-migration snapshot

---

## 7. Build Tool and Configuration

- **Build tool**: Not available in CAST MCP — pom.xml query returned no results. Build tool type and manifest file count cannot be confirmed from CAST data.
- **Language**: Java (Source: CAST MCP — element_types include Java Method, Java Class, etc.)
- **Runtime**: Spring Boot with Spring Web Services (Source: CAST MCP — technologies list)
- **Language version**: Not available in CAST MCP — not determinable from CAST structural data.
- **Target version**: Not available in CAST MCP — not determinable from CAST structural data.

> (Source: Requirement Document) — Language: unknown, Language latest: unknown, Runtime: unknown, Build tool: unknown, Upgrade urgency: medium.

---

## 8. Out-of-Scope Items

- GR-12/13 (batch/message decomposition): N/A — this is a smoke testing spec, not a decomposition exercise. No batch or message-listener entry points were identified in CAST.
- Column-level SQL schema detail: Out of scope for this use case — not queried.
- Semantic/GraphRAG analysis: Out of scope for this use case — not queried.
