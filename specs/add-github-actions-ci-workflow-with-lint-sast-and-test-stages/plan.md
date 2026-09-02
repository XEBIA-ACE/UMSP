# Plan: Add GitHub Actions CI Workflow with Lint, SAST, and Test Stages

## Overview

**Migration Strategy: Big-Bang (Greenfield Addition)**

This task introduces a net-new GitHub Actions CI workflow into a repository that currently has no CI pipeline. Because no existing pipeline is being replaced or modified, a big-bang approach is appropriate — the entire workflow is delivered in a single, self-contained pull request with no migration of prior state required.

The upgrade urgency is rated **medium**. There is no production runtime risk associated with adding a CI configuration file; the worst-case outcome of a misconfigured workflow is a failing PR check, which is independently reversible by updating or removing the workflow file. Effort is low-to-moderate (see Phases).

> **Note:** The tech analysis reports the language, runtime, and build tool as **unknown**. Concrete tool selections for lint, SAST, and test runners are marked as TODO pending codebase identification. The structural plan and workflow skeleton are fully specified below.

---

## Phases

| Phase | Description | Dependencies | Estimated Effort |
|-------|-------------|--------------|-----------------|
| 1 | Identify language, runtime, and build tool; select lint/SAST/test tooling | Access to repository source tree | 0.5 person-days |
| 2 | Author `.github/workflows/ci.yml` with lint, SAST, and test jobs | Phase 1 complete | 1 person-day |
| 3 | Validate workflow on a feature branch; fix runner/tool configuration issues | Phase 2 complete; GitHub Actions runner availability | 0.5 person-days |
| 4 | Set workflow as a required status check on `main`/`master` branch protection rules | Phase 3 green | 0.25 person-days |

**Total estimated effort: ~2.25 person-days** (derived from moderate-effort option).

---

## Component Changes

### `.github/workflows/ci.yml` *(new file)*

This is the sole deliverable. It defines a workflow triggered on `push` and `pull_request` events targeting the default branch.

**Structural layout:**

```
jobs:
  lint:      # static style/format checks
  sast:      # security static analysis
  test:      # unit + integration test execution
```

**Key configuration keys:**

| Key | Value / Notes |
|-----|---------------|
| `on.push.branches` | `[main, master]` (adjust to repo default) |
| `on.pull_request.branches` | `[main, master]` |
| `jobs.<job>.runs-on` | `ubuntu-latest` (TODO: confirm if self-hosted runners are required) |
| `jobs.test.needs` | `[lint]` — test job depends on lint passing |
| `jobs.sast.needs` | `[lint]` — SAST job depends on lint passing |

**Per-job responsibilities:**

- **`lint` job:** Checks out code, sets up language runtime, installs dependencies, runs linter. TODO: specify linter tool once language is confirmed (e.g., `eslint`, `flake8`, `golangci-lint`, `rubocop`).
- **`sast` job:** Runs static application security testing. Default recommendation: **CodeQL** via `github/codeql-action` (language-agnostic, native to GitHub Actions). TODO: confirm language is supported by CodeQL or substitute tool (e.g., `semgrep`, `bandit`, `gosec`).
- **`test` job:** Installs dependencies, executes test suite, uploads coverage report as artifact. TODO: specify test runner once language is confirmed.

**No existing files are modified** by this task.

---

## Dependency Upgrade Plan

N/A — not applicable to this task.

> The CI workflow consumes GitHub-hosted Actions (e.g., `actions/checkout`, `github/codeql-action`) which are versioned within the workflow YAML itself, not in a package manifest. No application dependencies are added or upgraded.

**GitHub Actions versions to pin (recommended):**

| Action | Recommended Pin | Notes |
|--------|----------------|-------|
| `actions/checkout` | TODO: pin to latest SHA at time of authoring | Prevents supply-chain drift |
| `actions/setup-<runtime>` | TODO: determined by language | e.g., `actions/setup-node`, `actions/setup-python` |
| `github/codeql-action/init` | TODO: pin to latest SHA | SAST |
| `github/codeql-action/analyze` | TODO: pin to latest SHA | SAST |

---

## Infrastructure Changes

### GitHub Actions Runner
- **Runner:** `ubuntu-latest` (GitHub-hosted). TODO: confirm whether the organization requires self-hosted runners (e.g., for private network access or compliance reasons).

### Branch Protection Rules
- After Phase 3, enable **required status checks** in repository Settings → Branches → Branch protection rules for `main`/`master`:
  - Require `lint` to pass
  - Require `sast` to pass
  - Require `test` to pass
- TODO: confirm whether branch protection is managed via IaC (e.g., Terraform `github_branch_protection` resource) or manually in the GitHub UI.

### Repository Secrets / Permissions
- CodeQL requires `security-events: write` permission. Add to workflow:
  ```yaml
  permissions:
    security-events: write
    contents: read
  ```
- TODO: determine if any lint or test steps require repository secrets (e.g., private package registry tokens). If so, document secret names and add to GitHub repository/organization secrets.

### CI/CD Pipeline
- This task **creates** the CI pipeline from scratch. There is no existing pipeline to modify.
- TODO: if a CD pipeline exists or is planned, document how it should depend on this CI workflow's success.

---

## Rollback Strategy

Each phase is independently reversible:

| Phase | Rollback Action |
|-------|----------------|
| **Phase 1** | No artifacts produced; no rollback needed. |
| **Phase 2** | Delete or revert `.github/workflows/ci.yml`. The workflow ceases to exist; no repository behavior changes. |
| **Phase 3** | If the workflow causes unexpected runner costs or blocks PRs, disable it by setting `on: {}` (empty trigger) or deleting the file via a follow-up commit. |
| **Phase 4** | Remove the required status checks from branch protection rules in GitHub Settings. PRs can merge without CI passing. This restores the pre-task state completely. |

> Because this task adds only a new file and a branch protection rule, rollback at any phase has zero impact on application source code or deployable artifacts.

---

## Testing Strategy

The CI workflow itself must be validated before being enforced as a required check.

| Layer | Approach | Tool | Gate |
|-------|----------|------|------|
| **Workflow syntax validation** | Lint the YAML workflow file for schema correctness | `actionlint` (static linter for GitHub Actions workflows) | Must pass before PR merge |
| **Dry-run / integration** | Push to a non-protected feature branch and observe all three jobs execute successfully in the Actions tab | GitHub Actions live run | All jobs green before enabling branch protection |
| **Lint job validation** | Introduce a deliberate lint violation on the feature branch; confirm the `lint` job fails and blocks | Manual test | Lint job must fail on bad code |
| **SAST job validation** | Confirm CodeQL (or chosen tool) produces a scan result (even if zero findings) | GitHub Security tab | Scan result present |
| **Test job validation** | Confirm test runner executes and exits 0 on a clean codebase | Manual observation | Test job green |
| **Coverage reporting** | TODO: define coverage threshold once test runner is known (e.g., 80% line coverage) | TODO | TODO |

**CI Gate (Phase 4 prerequisite):** All three jobs (`lint`, `sast`, `test`) must have at least one successful run on the feature branch before branch protection is enabled.

---

## Timeline

| Milestone | Phase | Estimated Completion | Owner |
|-----------|-------|---------------------|-------|
| Language/runtime/tooling confirmed | 1 | Day 1 | TODO |
| `.github/workflows/ci.yml` authored | 2 | Day 2 | TODO |
| Workflow validated green on feature branch | 3 | Day 3 | TODO |
| Branch protection rules enforced on `main` | 4 | Day 3 (end) | TODO |

**Total calendar time: ~3 days** (assumes single owner, sequential execution, moderate-effort option).