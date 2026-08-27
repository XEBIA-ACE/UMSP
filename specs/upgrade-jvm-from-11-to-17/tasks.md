## Mandatory Upgrade Coverage
- [ ] **UPG-001: Upgrade JVM 11 → 17**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-002: Upgrade Spring Boot 2.5.12 → 3.0.0**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-003: Upgrade Swagger 2.9.2 → 2.10.5**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.
- [ ] **UPG-004: Improve configuration management**
  - Source: Selected Upgrade Option
  - Acceptance: Implemented change is verified by relevant build and test checks.
  - Estimate: Allocate within the selected option's total effort after repository impact review.

---

# Tasks

- [ ] **T1**: Verify current Java version and update compatibility
  - **Objective**: Ascertain running Java version
  - **Dependencies**: None
  - **Actions**: Manual inspection
  - **Acceptance Criteria**: Documented verification

- [ ] **T2**: Track and verify existing configuration files
  - **Objective**: Confirm presence of pom.xml
  - **Dependencies**: T1
  - **Actions**: Search through repo, manual verification if necessary
  - **Acceptance Criteria**: Configuration files confirmed and documented

- [ ] **T3**: Prepare for JVM Upgrade
  - **Objective**: Ensure Spring Boot compatibility with Java 17
  - **Dependencies**: T2
  - **Actions**: Manual dependency inspection and documentation
  - **Acceptance Criteria**: All dependencies verified

- [ ] **T4**: Plan and Execute Upgrade Steps
  - **Objective**: Complete upgrade task steps outlined
  - **Dependencies**: T3
  - **Actions**: Stepwise execution of upgrade process
  - **Acceptance Criteria**: Successful execution and testing documentation.

- [ ] **T5**: Review and adjust CI/CD pipeline
  - **Objective**: Confirm Jenkins changes as per upgrade
  - **Dependencies**: T4
  - **Actions**: Inspect Jenkins pipeline, adjust as needed
  - **Acceptance Criteria**: CI/CD functional post-upgrade implementation.