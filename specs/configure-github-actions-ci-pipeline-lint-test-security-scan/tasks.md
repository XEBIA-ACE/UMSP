# TASKS: Configure GitHub Actions CI Pipeline (Lint, Test, Security Scan)

> **Scope:** Set up a GitHub Actions CI pipeline covering lint, test, and security scan stages.
> **Upgrade Option:** Moderate
> **Note:** Language, runtime, and build tool are unspecified in the tech analysis. Tasks below are written to the extent determinable; the implementing agent must substitute concrete tool names, file paths, and version pins once the repository is inspected.

---

## Prerequisites

- [ ] [XS] Confirm repository visibility (public/private) and verify GitHub Actions is enabled under **Settings → Actions → General** in the target repository
- [ ] [XS] Identify the primary language, runtime version, and build tool by inspecting the repository root (e.g., `package.json`, `pom.xml`, `requirements.txt`, `go.mod`, `Gemfile`) and record findings before any pipeline work begins
- [ ] [XS] Confirm that a `GITHUB_TOKEN` with sufficient permissions (read for checkout, write for PR status checks) is available as a default Actions secret — no manual secret creation required unless third-party scanners are used
- [ ] [XS] Identify any existing CI configuration files (e.g., `.travis.yml`, `Jenkinsfile`, `circle.yml`) in the repository root that may conflict with the new workflow and flag them for deprecation

---

## Phase 1 — Preparation

- [ ] [XS] Create a long-lived feature branch `ci/github-actions-pipeline` from the default branch to contain all pipeline configuration changes
- [ ] [S] Audit existing test scripts and lint commands in the project's build manifest (e.g., `scripts` block in `package.json`, `Makefile` targets, `tox.ini`) and document the exact commands the pipeline will invoke in a scratch note or PR description
- [ ] [XS] Create the directory `.github/workflows/` at the repository root if it does not already exist
- [ ] [XS] Identify the appropriate GitHub-hosted runner OS (e.g., `ubuntu-latest`) and confirm it supports the detected runtime version before writing any workflow YAML

---

## Phase 2 — Core Upgrade

- [ ] [M] Create `.github/workflows/ci.yml` with a top-level workflow definition: set `name: CI`, define `on` triggers for `push` (all branches) and `pull_request` (targeting the default branch), and declare a `permissions` block scoped to `contents: read`
- [ ] [M] Add a `lint` job to `.github/workflows/ci.yml`: configure the correct runner, add a checkout step using `actions/checkout@v4`, set up the runtime using the appropriate setup action (e.g., `actions/setup-node`, `actions/setup-python`, `actions/setup-java`) with an explicit version pin derived from the repository's runtime, and invoke the project's lint command identified in Phase 1
- [ ] [M] Add a `test` job to `.github/workflows/ci.yml`: reuse the same runner and setup steps as the `lint` job (or extract them into a reusable composite action if duplication is significant), invoke the project's test command, and configure the job to upload test result artifacts using `actions/upload-artifact@v4` if the test framework produces a report file
- [ ] [M] Add a `security-scan` job to `.github/workflows/ci.yml`: integrate a dependency vulnerability scanner appropriate to the detected language (e.g., `actions/dependency-review-action@v4` for pull requests, or `github/codeql-action` for SAST) with default configuration and `continue-on-error: false` to enforce the gate
- [ ] [S] Configure job dependencies in `.github/workflows/ci.yml` using `needs:` so that `test` runs after `lint` passes and `security-scan` runs in parallel with `test`, minimising total pipeline duration
- [ ] [XS] Add a `.github/workflows/ci.yml` `concurrency` block scoped to `${{ github.workflow }}-${{ github.ref }}` with `cancel-in-progress: true` to prevent redundant runs on rapid pushes

---

## Phase 3 — Testing & Validation

- [ ] [S] Trigger the workflow manually via `workflow_dispatch` (add the trigger to `.github/workflows/ci.yml`) on the feature branch and verify all three jobs (`lint`, `test`, `security-scan`) complete with green status in the **Actions** tab
- [ ] [XS] Introduce a deliberate lint error in a throwaway branch, open a draft PR, and confirm the `lint` job fails and blocks merge — then revert
- [ ] [XS] Confirm test results artifact is accessible in the **Actions** run summary if a report file was configured in Phase 2
- [ ] [XS] Verify the `security-scan` job produces a populated results summary in the **Security** tab (or Actions log) and that a known-vulnerable dependency (if any) surfaces correctly

---

## Phase 4 — CI/CD & Infrastructure

- [ ] [S] Enable **branch protection** on the default branch under **Settings → Branches**: require status checks `lint`, `test`, and `security-scan` to pass before merging, and enable "Require branches to be up to date before merging"
- [ ] [XS] Set the workflow-level `permissions` in `.github/workflows/ci.yml` to the minimum required (e.g., `contents: read`, `security-events: write` only if CodeQL is used) to satisfy least-privilege requirements
- [ ] [XS] Deprecate or remove any legacy CI configuration files identified in Phase 1 (e.g., `.travis.yml`) in a follow-up commit on the same branch to avoid conflicting status checks

---

## Phase 5 — Documentation & Rollout

- [ ] [S] Add a `## CI Pipeline` section to `CONTRIBUTING.md` (or create the file if absent) documenting: how to run lint and tests locally, what each CI job checks, and how to interpret security scan results
- [ ] [XS] Add a GitHub Actions status badge for the `ci.yml` workflow to `README.md` using the standard badge URL pattern `https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg`
- [ ] [XS] Update `CHANGELOG.md` (or create it) with an entry recording the addition of the GitHub Actions CI pipeline, the three enforced gates, and the date of rollout
- [ ] [XS] Notify the team (via PR description or team channel) that branch protection is now active on the default branch and that all future PRs must pass `lint`, `test`, and `security-scan` before merge

---

> **Agent note:** Tasks in Phase 2 marked `[M]` assume a single-language, single-module repository. If the repository is a monorepo or multi-language project, each job may need to be split into per-package matrix strategies — reassess sizing accordingly once the repository structure is confirmed in Phase 1.