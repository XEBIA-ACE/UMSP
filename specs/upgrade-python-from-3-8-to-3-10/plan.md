# PLAN: Upgrade Python from 3.8 to 3.10 (JTT-3255)

## Overview
Parallel-run migration: the Python 3.10 toolchain is introduced alongside the
existing setup, validated by CI and the smoke suite, then made the sole runtime.

## Phases

| Phase | Description                                   | Deliverable                                     |
|-------|-----------------------------------------------|-------------------------------------------------|
| 1     | Set up Python 3.10 environment                | `Dockerfile` (`python:3.10-slim`), `pyproject.toml` (`requires-python >= 3.10`) |
| 2     | Update codebase for compatibility             | `migration/CompatibilityHelper.py` scanner + runtime guard in `umsp/__init__.py` |
| 3     | Run tests under Python 3.10                   | `tests/SmokeTest.py`; CI runs `pytest -W error::DeprecationWarning` |
| 4     | Complete migration                            | CI `PYTHON_VERSION: "3.10"` for lint/test/build/SAST |

## Infrastructure Changes
- **Docker**: multi-stage build on `python:3.10-slim`; `compileall` step fails the image build on syntax errors.
- **CI/CD**: single `PYTHON_VERSION` env var; `compileall` lint gate; deprecation warnings promoted to errors in tests; Docker image build in the Build job.

## Rollback Strategy
Revert the `modernization/JTT-3255` merge commit; no data or schema changes are involved.

## Testing Strategy
- Runtime/version guards (interpreter, pyproject, Dockerfile, CI).
- Application initialisation (`python -m umsp`) and tree-wide `compileall`.
- Python 3.10 feature checks (pattern matching, `X | Y` unions, parenthesised context managers, `zip(strict=True)`).
- Deprecation checks (removed `collections` ABC aliases, `asyncio` without `loop=`, import under `-W error::DeprecationWarning`).
- Scanner self-tests for each deprecated construct it detects.
