# CONSTITUTION
## GitHub Actions CI Workflow — Lint, SAST & Test Stages

---

## Project Identity

**Name:** GitHub Actions CI Pipeline Implementation
**Purpose:** Introduce a GitHub Actions continuous integration workflow to the repository, enforcing automated lint, static application security testing (SAST), and test execution on every relevant code change.
**High-Level Goal:** Establish a repeatable, automated quality gate that catches style violations, security issues, and functional regressions before code is merged — replacing any current manual or absent CI process.

---

## Guiding Principles

1. **Prefer automated enforcement over documentation-only standards** because the tech analysis identifies no existing CI mechanism, meaning quality gates are currently unenforceable at scale.
2. **Prefer fail-fast stage ordering (lint → SAST → test) over parallel-only execution** because cheap checks (lint) should block expensive checks (test runs) early, minimising CI compute cost.
3. **Prefer explicit, pinned Action versions over floating tags** because unpinned third-party Actions introduce silent supply-chain risk with no audit trail.
4. **Prefer workflow definitions that are language/runtime-agnostic at the constitution level** because the tech analysis does not confirm the language, runtime, or build tool — concrete tooling choices are deferred to spec.md once confirmed.
5. **Prefer secrets and tokens managed via GitHub Encrypted Secrets over hardcoded values** because SAST tooling commonly requires API tokens that must never appear in source.

---

## Constraints

- **Timeline / Effort:** Upgrade option is classified as *moderate*; specific person-days are not provided — TODO: confirm effort ceiling with project lead before plan.md is authored.
- **Scope Freeze:** This engagement covers only the CI workflow files (`.github/workflows/`). Application source changes, dependency upgrades, and infrastructure modifications are out of scope.
- **Technology Mandates:**
  - CI platform: **GitHub Actions** (non-negotiable per task definition).
  - Workflow syntax must conform to the current GitHub Actions YAML schema.
  - SAST stage must include at least one tool capable of producing SARIF output for upload to GitHub Code Scanning (required for audit traceability).
- **Unknowns / TODOs:**
  - TODO: Confirm primary language, runtime version, and build tool so lint and test runner steps can be specified.
  - TODO: Confirm whether a specific SAST tool is mandated (e.g., CodeQL, Semgrep, Snyk).
  - TODO: Confirm target branches that should trigger the workflow (assumed: `main`, all pull requests).

---

## Quality Standards

| Standard | Measurable Bar |
|---|---|
| Workflow validity | All workflow YAML files must pass `actionlint` with zero errors before merge. |
| Stage coverage | Workflow must contain exactly three named jobs: `lint`, `sast`, and `test`; absence of any job is a blocking defect. |
| SAST reporting | SAST job must upload a SARIF results file to GitHub Code Scanning; workflow run without a successful upload step fails the gate. |
| Test reporting | Test job must produce a structured results artifact (e.g., JUnit XML) attached to the workflow run. |
| Code review | Workflow files require at least one peer review approval via GitHub Pull Request before merge to the default branch. |
| Documentation | A `docs/ci.md` file must be delivered alongside the workflow, documenting each stage, its purpose, and how to run checks locally. |
| Secret hygiene | No credentials, tokens, or keys may appear in workflow YAML; verified by SAST and manual review checklist. |

---

## Decision Log

| ID | Decision | Rationale | Status |
|---|---|---|---|
| ADR-001 | Use GitHub Actions as the sole CI platform | Explicitly mandated by the task; no alternative platforms are in scope. | Accepted |
| ADR-002 | Structure CI as three sequential jobs: lint → sast → test | Fail-fast ordering reduces wasted compute; aligns with Guiding Principle 2. | Accepted |
| ADR-003 | Require SARIF upload to GitHub Code Scanning | Provides persistent, auditable security findings without external tooling dependency. | Accepted |
| ADR-004 | Defer language-specific tooling selection to spec.md | Language/runtime is unconfirmed in tech analysis; premature selection risks rework. | Accepted |
| ADR-005 | Pin all third-party Actions to a full commit SHA | Mitigates supply-chain risk from mutable version tags (Guiding Principle 3). | Accepted |