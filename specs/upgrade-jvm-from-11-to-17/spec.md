## JVM Upgrade from 11 to 17 for Shopizer

### Current State
The Shopizer application is currently running on JVM 11. It utilizes various Java technologies such as AWS S3, Azure SDK, Spring Framework, and Hibernate. The build tool and some configurations regarding namespace or import alignments are yet to be determined through CAST.

### Proposed Changes
- Upgrade the Java Virtual Machine from version 11 to 17.
- Refactor any deprecated methods and classes to comply with Java 17's standards.
- Update framework versions if required by Java 17 compatibility.
- Perform necessary namespace/import updates, particularly from `javax.*` to `jakarta.*` if moving to newer versions of specifications requiring this change.

### Breaking Changes
- The migration may affect JPA Entities, Spring Beans, and MVC components.

#### Affected Files
- **JPA Entities**:
  - `User.java (id: 236738)`
  - `ShoppingCartItem.java (id: 236759)`
  - `Content.java (id: 236770)`
  - (and several others)

### Acceptance Criteria
- Application must build successfully using Java 17.
- All endpoints must function without crashes or unexpected behavior.
- Performance metrics must remain consistent or improved compared to the previous JVM version.
