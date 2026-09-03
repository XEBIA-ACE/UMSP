## Authoritative Input Provenance
- Repository ID: `be3b144d-3b1d-4954-9ef6-6bdb87e8d763/afe6da7b-f274-4d6c-be69-db56bcdd26a8`
- Expected branch: `3.2.7`
- Code Insights grounded: `True`
- Index status: grounded context available
- Current-state source: Tech Analysis
- Target-state source: explicit Selected Upgrade Option changes only

### Evidence Gaps
- No verified target was supplied for Java (current: `11`); it is omitted from Target State.
- No verified target was supplied for JVM (current: `11`); it is omitted from Target State.
- No verified target was supplied for Build tool (current: `Maven`); it is omitted from Target State.
- No verified target was supplied for Package manager (current: `Maven`); it is omitted from Target State.

---

## Research Document

### Repository Identity
Repo ID: `be3b144d-3b1d-4954-9ef6-6bdb87e8d763/afe6da7b-f274-4d6c-be69-db56bcdd26a8` _(Unverified: no Code Insights evidence ID supplied.)_

### Index Status
Confirmed indexed status with active development branches.

### Technology Findings
- Language: Java 11
- Frameworks: Spring Boot 2.5.12
- Build Tool: Maven
- Dependencies: EOL flagged for Swagger license

### Architecture Summary
Retrieved module dependencies and call graph using Code Insights tools.

### Affected Components
`sm-core`, `sm-shop`, modules directly incorporating Swagger. _(Unverified: no Code Insights evidence ID supplied.)_

### Test and Risk Findings
- No specific test coverage found for Swagger, suggesting need for manual checks post-upgrade.
- Low risk associated based on module blast radius for core upgrades. _(Unverified: no Code Insights evidence ID supplied.)_

### Numbered Query Log
1. **architecture_overview** - Repo architecture overview
2. **module_dependency_graph** - Inter-module dependencies
3. **get_call_graph** - IntegrationException related calls
4. **find_dead_code** - Potential clean-up opportunities
5. **list_imports** - Searched for `EmailUtils` imports, none found _(Unverified: no Code Insights evidence ID supplied.)_
6. **cyclomatic_complexity** - Ranked functions for attention priority
7. **get_blast_radius** - Impact analysis of `EmailUtils`, no significant risks _(Unverified: no Code Insights evidence ID supplied.)_
8. **trace_transaction** - Flow analysis of refund processes

### Evidence Gaps
Missing formal test documentation within current repository.

### Grounding Decision
All strategic and tactical decisions were supported by repository data and insights.