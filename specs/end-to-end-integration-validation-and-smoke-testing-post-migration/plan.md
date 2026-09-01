# Implementation Plan: Post-Migration Smoke Testing for Shopizer

---

## ⚠️ BCM Scope Gap (GR-08)
No BCM subsystem was provided. This plan covers the entire Shopizer application. SME validation required before execution.

---

## 1. Migration Context

Two CAST snapshots confirm the migration has been completed:
- **Pre-migration**: Shopizer (delivery 2026-07-10) — 16,468 elements, technologies include `aws s3`, `azure sdk for java`, `gcp storage` ✅
- **Post-migration**: Shopizer-3.2.5 (delivery 2026-07-30) — 16,572 elements, technologies include `aws sdk s3 for java`, `google cloud storage for java` (Azure removed) ✅

The migration involved SDK library upgrades for cloud storage integrations. The API surface (324 transactions) and data model (65 JPA entities) are structurally identical between versions. ✅

---

## 2. Phased Smoke Testing Strategy

### Phase 1: Environment Validation (Pre-Test)
**Goal**: Confirm the migrated application starts and is reachable.

1. Deploy Shopizer-3.2.5 to a test environment
2. Verify Spring Boot application context loads without errors
3. Confirm all ~250 Spring Beans initialize successfully (no `NoSuchBeanDefinitionException`)
4. Confirm database connectivity (Hibernate/JPA schema validation against all 65 entities)
5. Confirm cloud storage connectivity:
   - AWS S3 using `aws sdk s3 for java` (migrated from `aws s3`) ✅
   - GCP Storage using `google cloud storage for java` (migrated from `gcp storage`) ✅
6. Confirm Azure SDK is absent from classpath (no `azure sdk for java` dependency) ✅

### Phase 2: Authentication Smoke Tests
**Goal**: Validate all authentication entry points function.

Endpoints to test (from CAST transaction data ✅):
- `POST /api/v1/customer/login/` (transaction 232220, full graph=63)
- `POST /api/v1/private/login/` (full graph=68)
- `GET /api/v1/auth/refresh/` (transaction 232275, full graph=73)
- `GET /api/v1/auth/customer/refresh/` (transaction 232366, full graph=63)
- `POST /api/v1/customer/register/` (transaction 232221, full graph=3,093)

### Phase 3: Core Business Flow Smoke Tests
**Goal**: Validate the highest-risk transactions (largest call graphs).

Priority order based on full call graph size (CAST-confirmed ✅):

| Priority | Endpoint | Method | Post-Migration TxID | Full Graph |
|---|---|---|---|---|
| P1 | `api/v1/cart/{}/checkout/` | POST | 232211 | 3,281 |
| P1 | `api/v1/auth/cart/{}/checkout/` | POST | 232212 | 3,264 |
| P1 | `api/v1/private/store/{}/` | PUT | (page 3) | ~3,085 |
| P1 | `api/v1/private/store/` | POST | (page 3) | ~3,075 |
| P1 | `api/v1/customer/register/` | POST | 232221 | 3,093 |
| P2 | `api/v1/category/` | GET | 232387 | 2,972 |
| P2 | `api/v1/category/{}/` | GET | 232390 | 2,936 |
| P2 | `api/v1/category/product/{}/` | GET | 232386 | 2,935 |
| P2 | `api/v1/category/{}/manufacturer/` | GET | 232321 | 2,933 |

### Phase 4: JPA Entity Coverage Tests
**Goal**: Exercise all 65 JPA entities through their API endpoints.

All 65 JPA entities must be exercised. Key entity-to-endpoint mappings (CAST-confirmed ✅):

| JPA Entity (CAST ID) | Test Endpoint |
|---|---|
| Customer (7189) | POST /api/v1/customer/register/, GET /api/v1/auth/customer/profile/ |
| Order (6168) | GET /api/v1/auth/orders/, GET /api/v1/private/orders/ |
| Product (17941) | GET /api/v1/product/{id}/, POST /api/v1/auth/products/ |
| MerchantStore (6285) | GET /api/v1/private/store/{id}/, POST /api/v1/private/store/ |
| OrderTotal (6141) | POST /api/v1/cart/{}/checkout/ |
| Category (17943) | GET /api/v1/category/, GET /api/v1/category/{id}/ |
| Catalog (17945) | (via catalog API endpoints) |
| OrderStatusHistory (16233) | GET /api/v1/private/orders/{id}/history/ |
| Currency (17724) | GET /api/v1/currency/ (232306) |
| Country (16017) | GET /api/v1/country/ (232308) |
| Language (17544) | GET /api/v1/country/ (returns language data) |
| Manufacturer (17946) | POST /api/v1/private/manufacturer/ |

### Phase 5: Cloud Storage Integration Tests
**Goal**: Validate migrated cloud SDK integrations.

Based on CAST technology stack changes (✅ confirmed):

| Test | Endpoint | Pre-Migration SDK | Post-Migration SDK |
|---|---|---|---|
| S3 file upload | POST /api/v1/private/file/ | aws s3 | aws sdk s3 for java |
| S3 file list | GET /api/v1/private/content/list/ | aws s3 | aws sdk s3 for java |
| S3 image serve | GET /api/v1/content/images/ | aws s3 | aws sdk s3 for java |
| GCP image serve | GET /static/products/{}/{}/{} | gcp storage | google cloud storage for java |
| GCP file serve | GET /static/files/{}/{} | gcp storage | google cloud storage for java |
| Azure removal | GET /api/v1/auth/cart/{}/shipping/ | azure sdk for java | (none — verify no Azure calls) |

> ⚠️ The pre-migration shipping transaction `api/v1/auth/cart/{}/shipping/` (236552) used `azure sdk for java`. The post-migration equivalent (232349) uses `hibernate, java, java ee, jee, spring web services` — Azure SDK is absent. SME validation required to confirm this is intentional and that shipping functionality is not degraded.

### Phase 6: API Version Coverage
**Goal**: Validate all three API version namespaces (CAST-confirmed ✅).

- `/api/v0/` — 3 endpoints (SystemRESTController, StoreContactRESTController)
- `/api/v1/` — majority of 324 endpoints
- `/api/v2/` — product variant/group endpoints (ProductApiV2, ProductVariantApi, ProductVariantGroupApi, ProductVariationApi)

### Phase 7: Security Finding Triage
**Goal**: Address new XSS findings in Shopizer-3.2.5.

⚠️ Shopizer-3.2.5 has 73 new XSS-via-API-requests findings (rule 8482) and 2 reflected XSS findings (rule 8408) not present in pre-migration. These must be triaged before production deployment.

---

## 3. Rollback Strategy

⚠️ Rollback strategy is a proposal — SME validation required.

1. **Trigger**: Any P1 smoke test failure (checkout, store creation, customer registration)
2. **Rollback action**: Revert to pre-migration Shopizer deployment
3. **Data safety**: Ensure no production data was written during smoke testing
4. **Rollback validation**: Re-run Phase 2 (authentication) against rolled-back deployment to confirm baseline

---

## 4. Dependency Upgrade Table

| Component | Pre-Migration | Post-Migration | CAST Evidence |
|---|---|---|---|
| AWS S3 SDK | aws s3 | aws sdk s3 for java | ✅ CAST stats technology field |
| GCP Storage SDK | gcp storage | google cloud storage for java | ✅ CAST stats technology field |
| Azure SDK | azure sdk for java | (removed) | ✅ CAST stats technology field |
| Java Properties | (not present) | java properties | ✅ CAST stats technology field |
| Hibernate | hibernate | hibernate | ✅ Unchanged |
| Spring | spring, spring web services | spring, spring web services | ✅ Unchanged |
| JPA | jpa | jpa | ✅ Unchanged |
| Build tool | Not available in CAST MCP — pom.xml query returned no results | — | ❌ |
| Java version | Not available in CAST MCP — not determinable from structural data | — | ❌ |

---

## 5. Risk Register

| Risk | Severity | Evidence | Mitigation |
|---|---|---|---|
| 73 new XSS findings in post-migration | High | ✅ CAST quality_insights rule 8482, 73 objects | Triage before production; determine if pre-existing or newly introduced |
| Azure SDK removal breaks shipping | Medium | ✅ CAST: azure sdk for java absent from Shopizer-3.2.5 technologies | Validate shipping endpoints in Phase 5 |
| +104 element count unexplained | Low | ✅ CAST stats: 16,468 → 16,572 | SME review of new elements |
| −199 interaction count unexplained | Low | ✅ CAST stats: 72,524 → 72,325 | SME review of removed interactions |
| SQL-in-loop finding absent from post-migration | Low | ✅ CAST: rule 1025056 absent from Shopizer-3.2.5 | Confirm remediation or verify detection scope |
