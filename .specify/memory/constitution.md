# Shopizer — Integration Smoke Test & Regression Validation: Quality Standards

## 1. Code Conventions

### 1.1 Test Class Naming
- Smoke test classes: `*SmokeTest.java`
- Regression test classes: `*RegressionTest.java`
- Structural flaw tests: `*DetectionTest.java`
- All test classes in package `com.salesmanager.shop.test.*` mirroring the source package structure

### 1.2 Test Method Naming
- Format: `should_[expectedBehavior]_when_[condition]()`
- Example: `should_return200_when_validCartIsCheckedOut()`

### 1.3 Assertion Style
- Use AssertJ fluent assertions for readability
- Every test must have at least one explicit assertion — no empty test bodies
- HTTP status assertions must be explicit (e.g., `assertThat(response.statusCode()).isEqualTo(200)`)

### 1.4 Test Data Management
- Test data must be isolated per test run using Testcontainers or in-memory H2
- No test may depend on pre-existing production data
- All test data must be cleaned up after each test class

---

## 2. Test Coverage Standards

### 2.1 Minimum Coverage Requirements
- All 150+ Spring MVC operations (CAST-confirmed) must have at least one test case
- All 70 JPA entities (CAST-confirmed) must be exercised through at least one API call
- All 100+ Spring Beans (CAST-confirmed) must be loaded in the Spring context smoke test
- The 5 CAST structural flaw objects must each have a dedicated regression test

### 2.2 Smoke Test Standards
- Smoke tests must complete within 60 seconds total
- Each individual smoke test must complete within 10 seconds
- Smoke tests must not depend on external services (use mocks or stubs for AWS S3, Azure SDK, GCP Storage)

### 2.3 Regression Test Standards
- Regression tests may use real database connections (Testcontainers)
- Each regression test must be independent and idempotent
- Regression tests must not share mutable state between test methods

---

## 3. Security Standards

### 3.1 Test Credentials
- No production credentials may appear in test code or test configuration files
- Test JWT tokens must be generated programmatically using test-only signing keys
- The 29 "unsecured data string" findings (CAST cloud-detection-patterns ID: platform-migration:1200056) must be documented but must not be reproduced in test code

### 3.2 Authentication Testing
- Admin authentication tests must use a dedicated test admin account
- Customer authentication tests must use a dedicated test customer account
- All test accounts must be created and destroyed within the test lifecycle

---

## 4. Backward Compatibility

### 4.1 API Contract Preservation
- All 150+ Spring MVC operation signatures (HTTP method + path) must remain unchanged
- Response body schemas for all P1 smoke test endpoints must remain backward compatible
- No test may modify the Spring Bean wiring confirmed by CAST

### 4.2 JPA Entity Preservation
- All 70 JPA entity class names and package paths (as confirmed by CAST) must remain unchanged
- No test may alter JPA entity annotations or table mappings

### 4.3 Structural Flaw Baseline
- The structural flaw count (2 rules, 5 objects) is the regression baseline
- Any test run that causes the CAST structural flaw count to increase must be treated as a regression failure

---

## 5. Documentation Standards

### 5.1 Test Documentation
- Each test class must have a Javadoc comment referencing the CAST transaction ID(s) it covers
- Example: `/** Covers CAST transaction ID 236423 (api/v1/cart/{}/checkout/, fullSize: 3254) */`
- The BCM compliance gap (GR-08) must be noted in the test suite README

### 5.2 Known Issues
- The 29 "unsecured data string" findings must be listed in `SecurityFindingsReport.md`
- The 10 hardcoded HTTP URL findings must be listed in `HardcodedUrlReport.md`
- Both reports must be committed to the repository alongside the test code

---

## 6. CI/CD Integration Standards

### 6.1 Pipeline Requirements
- Smoke tests must run on every pull request
- Full regression suite must run on every merge to main branch
- CAST structural flaw count must be checked post-merge (Task 8.3)

### 6.2 Failure Thresholds
- Any smoke test failure blocks merge
- Any regression test failure blocks deployment
- Any increase in CAST structural flaw count blocks deployment

---

## 7. GR-08 Compliance Note
This constitution applies to the full application scope. When BCM scope is defined (Task 8.2), these standards must be re-evaluated and potentially narrowed to the BCM-scoped subsystem. The BCM gap is a standing compliance issue that must be resolved before this test suite is used as a production deployment gate.
