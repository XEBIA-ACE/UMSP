# PLAN: SQLAlchemy Upgrade

## Overview
The modernization strategy chosen for upgrading SQLAlchemy from 1.3 to 2.x is the feature-flag gated approach. This approach is selected given the medium upgrade urgency and the flexible manageability of changes SQLAlchemy may introduce, thereby reducing the risks associated with the transition. By controlling the activation of the new SQLAlchemy features or functionalities through feature flags, we limit potential disruptions in production environments while gaining the ability to incrementally test new code paths.

## Phases
| Phase               | Description                                        | Dependencies          | Estimated Effort |
|---------------------|----------------------------------------------------|-----------------------|------------------|
| Phase 1: Preparation| Identify todos and setup feature flags             | N/A                   | 2 person-days    |
| Phase 2: Implementation | Upgrade SQLAlchemy and wrap changes with feature flags | Completion of Phase 1 | 5 person-days    |
| Phase 3: Testing    | Comprehensive testing and validation of the changes | Completion of Phase 2 | 3 person-days    |
| Phase 4: Deployment | Gradual deployment using feature flags             | Completion of Phase 3 | 2 person-days    |
| Phase 5: Decommissioning | Remove feature flags and finalize upgrade      | Stabilization post Phase 4 | 1 person-day    |

## Component Changes
- **Structural Changes**: The main structural change involves updating data access code using SQLAlchemy to be compatible with 2.x APIs. This will mainly affect:
  - Database model files
  - Query and transaction initialization code

- **Affected Files**: 
  - `models.py`
  - `database.py`
  - Any utilities interfacing with SQLAlchemy methods

- **API Modifications**: Modifications may include changes in session querying patterns, transaction management, and ORM configuration styles compliant with SQLAlchemy 2.x.

## Dependency Upgrade Plan
| Dependency       | Current Version | Target Version | Breaking Changes                           | Migration Notes     |
|------------------|-----------------|----------------|--------------------------------------------|---------------------|
| SQLAlchemy       | 1.3             | 2.x            | New syntactical and functional API changes | Refactor based on SQLAlchemy's migration guide |

## Infrastructure Changes
- **Docker Base Image**: Update image to support dependencies required by SQLAlchemy 2.x if necessary. TODO
- **Kubernetes**: N/A — not applicable to this task
- **CI/CD Pipeline**: Ensure integration tests run against both SQLAlchemy 1.3 and 2.x until full transition. TODO
- **IaC Updates**: N/A — not applicable to this task

## Rollback Strategy
- **Phase 1**: N/A as no changes are made to systems.
- **Phase 2**: Revert code changes and disable feature flags.
- **Phase 3**: Continue using SQLAlchemy 1.3 code path if testing fails.
- **Phase 4**: Feature flags can be used to rollback the deployment of 2.x path quickly.
- **Phase 5**: Ensure feature-flag rollback remains an option until stable for several release cycles.

## Testing Strategy
- **Unit Tests**: Cover all database interaction logic with at least 80% coverage using libraries such as `unittest` or `pytest`.
- **Integration Tests**: Verify ORM and native query functionalities, covering both older and newer SQLAlchemy versions.
- **Regression Tests**: Execute tests against key functional flows to trace unexpected behavior due to the ORM changes.
- **Performance Tests**: Conduct comparative benchmark testing to ensure there is no degradation under common workload scenarios.
  
## Timeline
| Milestone                   | Phase                      | Estimated Completion | Owner |
|-----------------------------|----------------------------|----------------------|-------|
| Feature flags configured    | Phase 1: Preparation       | Day 3                | TODO  |
| Code updated under feature flags | Phase 2: Implementation | Day 8                | TODO  |
| Testing complete            | Phase 3: Testing           | Day 11               | TODO  |
| Initial deployment complete | Phase 4: Deployment        | Day 13               | TODO  |
| Feature flags removed       | Phase 5: Decommissioning   | Day 14               | TODO  |