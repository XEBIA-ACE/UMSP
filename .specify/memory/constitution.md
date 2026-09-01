# Constitution: Quality Standards and Design Principles — Shopizer-3.2.5

## BCM Scope Notice
⚠️ **Standing Compliance Gap (GR-08)**: No BCM subsystem was provided. These standards apply application-wide.

---

## 1. Code Conventions

### 1.1 Java Code Style
- Follow existing package structure: `com.salesmanager.core.*` for core modules, `com.salesmanager.shop.*` for web/API layer
- Maintain the established module separation: model layer (`sm-core-model`), service layer (`sm-core`), API layer (`sm-shop`)
- All new code must be compatible with the confirmed technology stack: Java, JPA, Hibernate, Spring, Spring Web Services ✅

### 1.2 JPA Entity Standards
- All 63 confirmed JPA entities reside in `sm-core-model/src/main/java/com/salesmanager/core/model/` ✅
- New JPA entities must follow the same package structure
- Entity classes must not contain business logic — maintain separation between entity model and service layer
- All entities must have corresponding repository integration tests (per Tasks 3.1–3.5)

### 1.3 Spring Bean Naming
- Spring Bean names must follow the existing camelCase convention (confirmed from CAST: `orderService`, `customerService`, `paymentService`, etc.) ✅
- XML-defined beans (in `shopizer-core-cms.xml`, `shopizer-core-modules.xml`, etc.) must maintain their existing bean IDs unless explicitly migrating to Java configuration

### 1.4 API Versioning
- Maintain the existing three-version API structure: v0 (legacy), v1 (primary), v2 (extended) ✅
- New endpoints must be added to v2 or later; do not add new endpoints to v0 or v1
- All new Spring MVC operations must follow the existing URL pattern conventions

---

## 2. Security Standards

### 2.1 XSS Prevention (Mandatory)
- All user-controlled input reflected in HTTP responses must be HTML-encoded using `StringEscapeUtils.escapeHtml4()` or equivalent
- This standard is required to remediate the 73 confirmed XSS violations (rule 8482) and 2 reflected XSS violations (rule 8408) ✅
- No new code may introduce XSS vulnerabilities; CAST rule 8482 and 8408 must show 0 violations after remediation

### 2.2 Exception Handling
- Empty catch blocks are prohibited, especially in methods with high fan-in
- This standard is required to remediate the 2 confirmed empty catch block violations (rule 1060020) ✅
- All catch blocks must at minimum log the exception with appropriate severity

### 2.3 Authentication
- JWT authentication must be used for all protected endpoints
- The multi-entry-point security configuration (`MultipleEntryPointsSecurityConfig`) must not be simplified or removed ✅
- Password encoding must use the confirmed `passwordEncoder` bean (ID: 21167) ✅

---

## 3. Test Coverage Standards

### 3.1 Integration Test Requirements
- All 63 JPA entities must have CRUD integration tests ✅ (required by spec)
- All 324 Spring MVC endpoints must have at least one integration test ✅ (required by spec)
- Integration tests must use the test properties files: `application-test.properties` (ID: 25112), `sm-core/src/test/resources/application.properties` (ID: 9513) ✅

### 3.2 Test Isolation
- Integration tests must not depend on external services (AWS S3, GCP, SES) unless explicitly tagged as cloud integration tests
- Cloud integration tests (Tasks 5.1–5.3) must be in a separate test profile and not run by default in CI

### 3.3 Test Naming Convention
- Integration test classes must be named `*IntegrationTest` (e.g., `OrderRepositoryIntegrationTest`)
- Unit test classes must be named `*Test`
- Test methods must follow the pattern: `should[ExpectedBehavior]When[Condition]`

---

## 4. Configuration Management

### 4.1 Properties File Standards
- All 42 confirmed properties files must be maintained ✅
- Profile-specific properties (docker, dependency, cloud, mysql, local, gcp, aws) must not be merged
- Sensitive values (database credentials, API keys) must use the confirmed `vault.properties` mechanism (IDs: 8598, 25113) ✅
- The `authentication.properties` file (ID: 12677) must not be modified without security review

### 4.2 Spring XML Configuration
- Existing Spring XML configuration files must not be deleted without migrating all bean definitions to Java configuration
- If migrating XML beans to Java configuration, maintain identical bean names and behavior
- The 6 confirmed XML configuration files must remain functional ✅

---

## 5. Backward Compatibility

### 5.1 API Backward Compatibility
- All existing 324 Spring MVC endpoints must remain functional after any migration ✅
- Breaking changes to existing API contracts require versioning (new v2/v3 endpoint, not modification of existing)
- The v0 legacy endpoints (`services/private/...`, `services/public/...`) must remain functional until explicitly deprecated

### 5.2 Database Backward Compatibility
- No DDL changes may be introduced without explicit schema migration scripts
- Hibernate DDL auto-generation must be set to `validate` (not `update` or `create`) in production profiles
- All 63 JPA entity mappings must remain compatible with the existing database schema ✅

### 5.3 Namespace Migration Compatibility (If Applicable)
- If `javax.*` → `jakarta.*` migration is executed, it must be atomic across all affected files
- Partial migration (some files using `javax.*`, others using `jakarta.*`) is not permitted
- All 63 JPA entities must be migrated in the same release ✅

---

## 6. Cloud Integration Standards

### 6.1 AWS S3
- All 4 confirmed AWS S3 beans (awsAssetsManager, awsContentAssetsManager, awsDownloadsManager, awsProductAssetsManager) must remain functional ✅
- AWS credentials must not be hardcoded; use the confirmed `vault.properties` or environment variables

### 6.2 Google Cloud Storage
- GCP storage integration must remain functional for the `gcp` profile ✅
- GCP credentials must not be hardcoded

### 6.3 AWS SES
- The `sesEmailSender` bean (ID: 21237) must remain functional ✅
- Email configuration must use `email.properties` (ID: 12588) ✅

---

## 7. Build Standards

### 7.1 Maven Build
- All 5 Maven modules must pass `mvn clean verify` before any release ✅
- The 5 `maven-wrapper.properties` files (IDs: 8497, 8528, 12906, 13264, 13347) must be kept in sync ✅
- No module may introduce circular dependencies

### 7.2 Quality Gates
- CAST structural flaw rules 8482, 8408, and 1060020 must show 0 violations before release
- New code must not introduce violations of any CAST structural flaw rule

---

## 8. GR-12/GR-13 Applicability

GR-12 (batch boundary) and GR-13 (fine-grained boundary) are **not applicable** to this use case. This is an integration testing and migration validation specification, not a decomposition exercise. No batch jobs or message listeners were identified in CAST queries; this is logged as not queried (out of scope), not confirmed absent.
