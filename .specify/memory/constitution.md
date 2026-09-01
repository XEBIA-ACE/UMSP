# Constitution: Quality Standards for Shopizer Post-Migration Smoke Testing

---

## 1. Grounding Principles

### GR-08 Compliance Gap
No BCM subsystem was provided for this engagement. All quality standards apply application-wide. Before any implementation begins, the team must obtain BCM scope from the product owner and re-scope queries accordingly.

### Zero Hallucination
All test assertions must be grounded in CAST-confirmed structural facts:
- Test endpoints must match the 324 CAST-confirmed Spring MVC transactions
- JPA entity assertions must reference the 65 CAST-confirmed JPA entities
- Technology integration tests must reflect the CAST-confirmed technology stack changes

---

## 2. Test Coverage Standards

### 2.1 Transaction Coverage
- **Minimum**: 100% of P1 transactions (full call graph > 3,000 objects) must have explicit smoke tests
- **Target**: 100% of all 324 CAST-confirmed Spring MVC transactions must be exercised
- **Measurement**: Each test must reference its CAST transaction ID in test metadata

### 2.2 JPA Entity Coverage
- All 65 CAST-confirmed JPA entities must be exercised through at least one CRUD operation
- Entity coverage must be tracked against the CAST entity list (see research.md Appendix A1)
- No entity may be assumed covered without a corresponding test assertion

### 2.3 Technology Integration Coverage
- Each CAST-confirmed technology change must have at least one dedicated integration test:
  - `aws sdk s3 for java` (migrated from `aws s3`)
  - `google cloud storage for java` (migrated from `gcp storage`)
  - Azure SDK removal (confirmed absent from Shopizer-3.2.5 technology list)

---

## 3. Code Conventions

### 3.1 Test Naming
- Test method names must include the CAST transaction ID where applicable
- Format: `test_[HTTP_METHOD]_[endpoint_path]_[CAST_txId]`
- Example: `test_POST_api_v1_cart_checkout_232211()`

### 3.2 Test Metadata
Each test must carry metadata annotations:
```java
@CastTransaction(id = "232211", fullGraphSize = 3281, priority = "P1")
@JpaEntities({"Order", "OrderProduct", "OrderTotal"})
@Technologies({"aws sdk s3 for java", "google cloud storage for java", "hibernate"})
```

### 3.3 Assertion Standards
- HTTP status code assertions are mandatory for every test
- Response body structure assertions are required for P1 transactions
- Database state assertions (JPA entity persistence) are required for all write operations
- No test may pass solely on HTTP 200 without validating response content

---

## 4. Security Standards

### 4.1 XSS Finding Remediation (Shopizer-3.2.5)
The 73 objects flagged by CAST rule 8482 ("Avoid cross-site scripting through API requests") and 2 objects flagged by rule 8408 must be addressed before production deployment:
- All user-controlled input reflected in HTTP responses must be HTML-encoded using `StringEscapeUtils.escapeHtml4()` or equivalent
- Output encoding must be applied in the controller layer, not the service layer
- Remediation must be verified by re-running CAST analysis and confirming rule 8482/8408 findings are resolved

### 4.2 Empty Catch Block Standard
The 2 objects flagged by CAST rule 1060020 ("Avoid empty catch blocks for methods with high fan-in") must be remediated:
- Empty catch blocks must be replaced with appropriate exception handling
- At minimum, exceptions must be logged with sufficient context for debugging
- Silent swallowing of exceptions in high-fan-in methods is prohibited

### 4.3 Unsecured Data Strings
The 29 objects flagged by CAST cloud-readiness rule 1200056 ("Use of an unsecured data string") must be reviewed:
- Hardcoded credentials or sensitive strings must be externalized to environment variables or secrets management
- This is a pre-existing finding from the pre-migration snapshot and must not be worsened by migration

---

## 5. Backward Compatibility Standards

### 5.1 API Surface Preservation
- The 324-transaction API surface must be preserved exactly post-migration
- No endpoint may be removed or renamed without explicit versioning
- Response schemas must be backward-compatible with pre-migration clients

### 5.2 JPA Entity Schema Compatibility
- All 65 JPA entities must maintain their existing database schema
- No column renames or type changes are permitted without migration scripts
- Hibernate DDL validation mode must pass without errors

### 5.3 Spring Bean Compatibility
- All ~250 Spring Beans must initialize without errors
- Bean names must not change (Spring injection by name must continue to work)
- XML-defined beans (`shopizer-core-cms.xml`, `shopizer-core-modules.xml`, `shopizer-core-config.xml`) must remain valid

---

## 6. Performance Standards

### 6.1 Response Time Baselines
- P1 transactions (full graph > 3,000) must complete within 5 seconds under test load
- P2 transactions (full graph 1,000–3,000) must complete within 3 seconds
- All other transactions must complete within 2 seconds

### 6.2 Database Query Standards
- The 3 SQL-in-loop violations (CAST rule 1025056) from pre-migration must not be reintroduced
- New SQL-in-loop patterns are prohibited in migrated code

---

## 7. Documentation Standards

### 7.1 Test Result Traceability
- Every test result must be traceable to a CAST transaction ID
- Test reports must include: CAST transaction ID, endpoint, HTTP method, full graph size, pass/fail, response time
- Failed tests must include the CAST object IDs of the affected components

### 7.2 Migration Delta Documentation
- The +104 element count delta must be documented with explanation before production deployment
- The −199 interaction count delta must be documented with explanation before production deployment
- The Azure SDK removal must be documented with confirmation that no functionality was lost

### 7.3 Security Finding Documentation
- All 75 security findings (73 XSS-via-API + 2 reflected XSS) must be triaged and documented
- Each finding must be classified as: (a) newly introduced by migration, (b) pre-existing, or (c) false positive
- Classification must be reviewed by a security SME before production deployment
