# Spec: Add GitHub Actions CI Workflow with Lint, SAST, and Test Stages

## Summary

This spec covers the addition of a GitHub Actions continuous integration (CI) workflow to the repository. The workflow will introduce automated pipeline stages for linting (code style and formatting enforcement), static application security testing (SAST), and automated test execution. The expected outcome is that every pull request and push to the main branch triggers these checks automatically, providing fast feedback on code quality, security posture, and functional correctness before changes are merged.

---

## Motivation

- **No existing CI pipeline:** The repository currently has no automated CI enforcement. Code quality, security, and correctness checks are entirely manual, creating risk of regressions and vulnerabilities reaching the main branch undetected.
- **Security posture:** Without SAST, known vulnerability patterns in committed code go undetected until a manual review or post-incident audit. Automated SAST on every change reduces this exposure window.
- **Upgrade urgency:** Rated **medium** — the absence of CI is an active tech-debt item. While not an emergency, the lack of automated checks slows safe iteration and increases review burden on maintainers.
- **Compliance and best practices:** Many organizational and open-source contribution standards require a passing CI status check as a merge gate. Adding this workflow enables branch protection rules to be enforced.
- **Developer experience:** Automated feedback on lint and test failures reduces the round-trip time between code authoring and defect discovery.

> **Note:** Specific CVEs, EOL dates, or framework-level urgency ratings are not applicable here, as this task introduces new tooling rather than upgrading existing dependencies.

---

## Current State

- **CI system:** None. No `.github/workflows/` directory or equivalent CI configuration exists in the repository.
- **Lint enforcement:** N/A — no automated linting is configured.
- **SAST tooling:** N/A — no static analysis tooling is configured.
- **Test execution:** N/A — tests (if they exist) are run manually by developers.
- **Branch protection:** TODO — it is unknown whether branch protection rules are currently configured on the main branch.
- **Language / Runtime / Build tool:** Listed as unknown in the tech analysis. The specific lint tool, SAST tool, and test runner to be used are therefore TODO pending language identification (see Open Questions).

---

## Proposed Changes

The following CI pipeline stages will be added as a GitHub Actions workflow:

| Component | Before | After | Breaking? |
|---|---|---|---|
| CI pipeline | None | GitHub Actions workflow triggered on `push` and `pull_request` events | N |
| Lint stage | None (manual) | Automated lint check as a required CI stage | N |
| SAST stage | None (manual) | Automated static security analysis as a required CI stage | N |
| Test stage | None (manual) | Automated test execution as a required CI stage | N |
| Branch merge gate | None | CI status checks available to enforce as merge requirements | N |

**What is added:**
- A GitHub Actions workflow definition targeting `push` to the default branch and all `pull_request` events.
- A **lint stage** that runs the appropriate linter for the repository's language and fails the build on violations.
- A **SAST stage** that runs a static security analysis tool appropriate for the repository's language and fails the build on findings above a defined severity threshold (TODO: threshold to be confirmed).
- A **test stage** that executes the repository's existing test suite and fails the build on any test failure or if no tests are found (TODO: confirm behaviour when test suite is empty).

**What is removed:**
- Nothing is removed. This is a net-new addition.

**What is changed:**
- Nothing in application source code is changed by this spec.

---

## Compatibility & Breaking Changes

| Change | Impact | Migration Path |
|---|---|---|
| CI checks now run on every PR | PRs with pre-existing lint violations will fail CI | Contributors must resolve lint violations before merge; a one-time bulk fix pass may be needed on existing open PRs |
| CI checks now run on every PR | PRs with pre-existing SAST findings will fail CI | TODO — policy for handling pre-existing findings (suppress, fix, or set a baseline) must be decided before enforcement is enabled |
| CI checks now run on every PR | PRs where tests fail will be blocked | No migration needed if tests currently pass; if tests are broken, they must be fixed before the merge gate is enforced |
| Branch protection (if enabled) | External contributors and maintainers must wait for CI to pass | No code change required; workflow change only |

---

## Acceptance Criteria

1. **Given** a pull request is opened against the default branch, **when** the PR is created or updated, **then** the GitHub Actions workflow is automatically triggered and all three stages (lint, SAST, test) execute without requiring manual intervention.

2. **Given** the lint stage runs, **when** the source code contains a lint violation, **then** the lint stage exits with a non-zero status and the overall workflow run is marked as failed.

3. **Given** the lint stage runs, **when** the source code contains no lint violations, **then** the lint stage exits with a zero status and does not block the workflow.

4. **Given** the SAST stage runs, **when** the source code contains a finding at or above the defined severity threshold, **then** the SAST stage exits with a non-zero status and the overall workflow run is marked as failed.

5. **Given** the SAST stage runs, **when** no findings at or above the severity threshold are present, **then** the SAST stage exits with a zero status and does not block the workflow.

6. **Given** the test stage runs, **when** one or more tests fail, **then** the test stage exits with a non-zero status and the overall workflow run is marked as failed.

7. **Given** the test stage runs, **when** all tests pass, **then** the test stage exits with a zero status and does not block the workflow.

8. **Given** a push is made directly to the default branch, **when** the push completes, **then** the GitHub Actions workflow is triggered and all three stages execute.

9. **Given** the workflow is triggered, **when** all three stages (lint, SAST, test) pass, **then** the overall workflow run is marked as successful and the status check is reported as passing on the associated commit.

10. **Given** the workflow definition is present in the repository, **when** the repository is viewed in the GitHub Actions UI, **then** the workflow is listed and its run history is visible to repository maintainers.

---

## Open Questions

| # | Question | Owner | Due Date |
|---|---|---|---|
| 1 | What is the repository's primary language and runtime? This determines which lint tool, SAST tool, and test runner are used. | TODO | TODO |
| 2 | What build tool is used (e.g., Make, npm, Gradle, Poetry)? This determines how stages are invoked. | TODO | TODO |
| 3 | Which specific SAST tool should be used (e.g., CodeQL, Semgrep, Bandit, ESLint security plugin)? | TODO | TODO |
| 4 | What severity threshold should cause the SAST stage to fail (e.g., medium, high, critical only)? | TODO | TODO |
| 5 | What is the expected behaviour of the test stage if no test files exist in the repository? (Fail, warn, or skip?) | TODO | TODO |
| 6 | Are branch protection rules to be enabled on the default branch as part of this work, or is that a separate task? | TODO | TODO |
| 7 | How should pre-existing SAST findings be handled at rollout — fix-first, suppress with a baseline file, or enforce only on new code? | TODO | TODO |
| 8 | Should the workflow run on all branches or only on the default branch and pull requests targeting it? | TODO | TODO |
| 9 | Are there secrets or environment variables required by the test suite that must be configured in GitHub Actions secrets? | TODO | TODO |
| 10 | Is there a required CI runtime environment (e.g., self-hosted runners vs. GitHub-hosted runners)? | TODO | TODO |