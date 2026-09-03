## Authoritative Pipeline Facts
These facts are generated from Tech Analysis and the selected Upgrade Option and take precedence over narrative text.

### Current State
| Category | Component | Current value | Source |
| --- | --- | --- | --- |
| language | Java | 11 | Tech Analysis |
| runtime | JVM | 11 | Tech Analysis |
| build_tool | Build tool | Maven | Tech Analysis |
| package_manager | Package manager | Maven | Tech Analysis |
| framework | Spring Boot | 2.5.12 | Tech Analysis |
| framework | Swagger | 2.9.2 | Tech Analysis |
| dependency | Elasticsearch | 7.5.2 | Tech Analysis |
| dependency | Jackson | 2.13.4.1 | Tech Analysis |

### Target State
| Component | Current | Explicit target | Source |
| --- | --- | --- | --- |
| Upgrade Swagger | 2.9.2 | 3.0.0 | Selected Upgrade Option |

## Authoritative Modernization Decision
- Selected option: Minimal Version Bumps and Security Patches (`conservative`)
- Effort: 5 person-days
- Risk score: 3/10
- Blockers: None supplied
- Impacted areas: source code, tests

### Open Questions
- Verify the target requirement for Java; current value `11` is intentionally omitted from Target State.
- Verify the target requirement for JVM; current value `11` is intentionally omitted from Target State.
- Verify the target requirement for Build tool; current value `Maven` is intentionally omitted from Target State.
- Verify the target requirement for Package manager; current value `Maven` is intentionally omitted from Target State.

---

## Specification Document

### Summary
Upgrade Swagger from version 2.9.2 to 3.0.0 to address the end-of-life status and enhance compatibility with future dependencies.

### Motivation
Swagger 2.9.2 is no longer supported, and upgrading will ensure ongoing maintenance and security patches.

### Repository Evidence
Based on the [Code Insights architecture overview](#log), the project is structured into several modules primarily built with Java (version 11), using a Maven build system.

### Current State
- **Swagger Version**: 2.9.2
- **Java Version**: 11
- **Framework**: Spring Boot 2.5.12
- **Key Dependencies**: Elasticsearch 7.5.2, Hibernate, Jackson

### Target State
- **Swagger Version**: 3.0.0
- **Framework**: No change planned concurrently

### Compatibility Matrix
Current to target version compatibility assured through minor version bump, indicated by low blast radius. _(Unverified: no Code Insights evidence ID supplied.)_

### Scope
Upgrade involves modifying Swagger configurations and associated API documentation for support in v3.0.0.

### Affected Components/Interfaces
- API interfaces documented across modules `sm-core` and `sm-shop` _(Unverified: no Code Insights evidence ID supplied.)_

### Compatibility and Breaking Changes
Minimal changes required, mainly adaptations in annotations in API methods.

### Testable Acceptance Criteria
- Successful build with Maven
- No new critical issues in runs
- Application starting without errors during Swagger initialization

### Risks
- Potential downtime during deployment
- Any overlooked breaking change

### Out-of-Scope
Upgrades to other frameworks during this process.

### Open Questions
None identified at this stage.