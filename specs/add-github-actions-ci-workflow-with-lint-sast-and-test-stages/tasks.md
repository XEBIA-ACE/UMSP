# Tasks: Add GitHub Actions CI Workflow with Lint, SAST, and Test Stages

> **Note:** Language, runtime, and build tool are unspecified in the tech analysis. Several tasks below include decision points that must be resolved by the team before or during Phase 1. Tasks are written to be as specific as possible given available context; file paths and tool choices marked with `*` require confirmation.

---

## Prerequisites

- [ ] [XS] Confirm repository has a `main` (or `master`) default branch and that the team has write access to create `.github/workflows/` directory
- [ ] [XS] Confirm GitHub Actions is enabled for the repository in **Settings → Actions → General**
- [ ] [XS] Identify and document the project's language, runtime version, and build tool (e.g., Node/npm, Python/pip, Java/Maven) — required before Phase 2 tasks can be executed
- [ ] [XS] Identify the intended SAST tool (e.g., CodeQL, Semgrep, Bandit, SpotBugs) and confirm it supports the project's language
- [ ] [XS] Identify the intended lint tool (e.g., ESLint, Flake8, Pylint, Checkstyle) and confirm a config file exists in the repository root
- [ ] [XS] Confirm any required GitHub Actions secrets (e.g., `GITHUB_TOKEN` for CodeQL) are available or can be provisioned

---

## Phase 1 — Preparation

- [ ] [XS] Create feature branch `ci/add-github-actions-workflow` from the default branch
- [ ] [XS] Audit existing CI configuration files (e.g., `.travis.yml`, `Jenkinsfile`, `circle.yml`) in the repository root and document any lint, test, or SAST steps already defined — to be replicated or superseded
- [ ] [XS] Verify that lint and test commands run successfully in a clean local environment and document the exact commands (e.g., `npm run lint`, `pytest`, `mvn test`) in a scratch note or PR description
- [ ] [XS] Create the `.github/workflows/` directory in the repository root if it does not already exist
- [ ] [XS] Confirm the default branch protection rules in **Settings → Branches** to determine which status checks must pass before merge — these will become required checks after rollout

---

## Phase 2 — Core Upgrade

- [ ] [S] Create `.github/workflows/ci.yml` with top-level workflow metadata: name, `on` triggers (`push` to `main`, `pull_request` to `main`), and a `concurrency` key to cancel redundant runs on the same branch
- [ ] [S] Add a `lint` job to `.github/workflows/ci.yml` that checks out the repository, sets up the correct language runtime, installs dependencies, and runs the project's lint command — using the tool and command confirmed in Phase 1
- [ ] [S] Add a `test` job to `.github/workflows/ci.yml` that checks out the repository, sets up the correct language runtime, installs dependencies, and runs the project's test command — with `needs: [lint]` to enforce ordering
- [ ] [M] Add a `sast` job to `.github/workflows/ci.yml` using the SAST tool confirmed in Phase 1 (e.g., configure `github/codeql-action/init`, `autobuild`, and `analyze` steps for CodeQL; or `returntocorp/semgrep-action` for Semgrep) — with `needs: [lint]` and appropriate `permissions: security-events: write` if using CodeQL
- [ ] [XS] Add a `permissions` block at the workflow or job level in `.github/workflows/ci.yml` following the principle of least privilege (e.g., `contents: read`, `security-events: write` only where required)
- [ ] [XS] Pin all third-party GitHub Actions to specific commit SHAs (not floating tags) in `.github/workflows/ci.yml` to prevent supply-chain risk (e.g., `actions/checkout@<SHA>`, `actions/setup-node@<SHA>`)

---

## Phase 3 — Testing & Validation

- [ ] [S] Trigger the workflow manually via `workflow_dispatch` (add trigger to `.github/workflows/ci.yml`) or by pushing the feature branch, and verify all three jobs (`lint`, `sast`, `test`) appear in the **Actions** tab and complete without errors
- [ ] [XS] Introduce a deliberate lint violation in a scratch file, open a draft PR, confirm the `lint` job fails and blocks the `test` job, then revert the violation
- [ ] [XS] Introduce a deliberate test failure in a scratch file, open a draft PR, confirm the `test` job fails, then revert
- [ ] [XS] Verify SAST results appear in **Security → Code scanning alerts** (if using CodeQL or Semgrep with GitHub integration) or in the job log for other tools
- [ ] [XS] Confirm workflow run times are reasonable (lint + test + SAST completing within an acceptable window for the team) and document baseline durations in the PR description

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [XS] Add `lint`, `test`, and `sast` as required status checks on the `main` branch in **Settings → Branches → Branch protection rules** so PRs cannot merge if any job fails
- [ ] [XS] Verify that `GITHUB_TOKEN` permissions in **Settings → Actions → General → Workflow permissions** are set to "Read repository contents and packages" (least privilege) and that the `sast` job's explicit `permissions` block overrides as needed

---

## Phase 5 — Documentation & Rollout

- [ ] [XS] Add a `## CI` section to `README.md` (or the project's primary documentation file) describing the three workflow stages, how to run lint and tests locally, and how to view SAST results
- [ ] [XS] Add an entry to `CHANGELOG.md` (or equivalent) under an `[Unreleased]` heading documenting the addition of the GitHub Actions CI workflow with lint, SAST, and test stages
- [ ] [XS] Open the feature PR from `ci/add-github-actions-workflow` to `main`, confirm all three required status checks pass on the PR itself, and request review from at least one team member before merging
- [ ] [XS] After merge, monitor the first two or three CI runs on `main` in the **Actions** tab to confirm no flakiness or environment-specific failures

---

> **Unresolved dependencies:** Tasks in Phase 2 cannot be fully implemented until the language/runtime, build tool, lint command, and SAST tool are confirmed (Phase 1 prerequisites). An AI coding agent picking up Phase 2 tasks should treat those decisions as blocking inputs and request clarification before proceeding.