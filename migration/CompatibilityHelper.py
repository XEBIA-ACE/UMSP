# migration_helper.py
# Compatibility shim for upgrading test coverage reporting in the user-management service.
# Addresses: Flask 1.x → 3.1, SQLAlchemy 1.3 → 2.0, Python 3.8 → 3.12, and pytest-cov addition.
#
# Usage:
#   python migration_helper.py
#
# This script:
#   1. Migrates Jest coverage config in package.json to add explicit reporters and thresholds.
#   2. Provides Flask 1.x → 3.x compatibility shims for any Python Flask code found.
#   3. Provides SQLAlchemy 1.3 → 2.0 compatibility shims for any Python SQLAlchemy code found.
#   4. Adds pytest-cov configuration to setup.cfg / pyproject.toml if Python test infra is found.
#   5. Transforms old config formats to new formats.
#
# NOTE: The primary test stack in this repo is Node.js/Jest (user-management) and
# Java/JUnit (payment-service). The Python/pytest-cov goal is addressed here for any
# Python components that exist or will be added. See TODO comments for manual steps.

import json
import os
import re
import sys
import textwrap
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Constants — all names sourced exclusively from spec.md / design.md context
# ---------------------------------------------------------------------------

# Jest coverage reporters to add (spec: "not consumable by CI tooling")
JEST_COVERAGE_REPORTERS = ["text", "lcov", "json-summary", "clover"]

# Jest coverage thresholds (spec: "threshold enforcement" gap)
JEST_COVERAGE_THRESHOLDS: Dict[str, int] = {
    "branches": 70,
    "functions": 70,
    "lines": 70,
    "statements": 70,
}

# Source files already scoped by spec
JEST_COLLECT_COVERAGE_FROM = [
    "src/**/*.js",
    "!src/__tests__/**",
]

# pytest-cov configuration values (spec: "Add pytest-cov for Test Coverage Reporting")
PYTEST_COV_SOURCE = "src"
PYTEST_COV_REPORT_FORMATS = ["term-missing", "lcov", "xml", "html"]
PYTEST_MIN_COVERAGE = 70

# Flask version markers (spec: Flask 1.x → 3.1)
FLASK_OLD_IMPORT_PATTERNS = [
    # Flask 1.x patterns that changed in Flask 3.x
    (r"from flask\.ext\.", "flask_"),          # flask.ext.* removed in Flask 1.0, gone in 3.x
    (r"flask\.json\.provider", None),          # new in Flask 2.2 — manual review needed
]

# SQLAlchemy 1.3 → 2.0 deprecated API patterns (spec: SQLAlchemy 1.3 → 2.0)
SQLALCHEMY_DEPRECATED_PATTERNS = [
    # Query API replaced by select() in SQLAlchemy 2.0
    (r"\.query\.filter_by\(", "session.execute(select(...).filter_by("),
    (r"\.query\.filter\(",    "session.execute(select(...).filter("),
    (r"\.query\.all\(\)",     "session.execute(select(...)).scalars().all()"),
    (r"\.query\.first\(\)",   "session.execute(select(...)).scalars().first()"),
    (r"\.query\.get\(",       "session.get(Model, "),
    # Boolean column arguments changed in 2.0
    (r"Column\(Boolean,\s*create_constraint=True\)", "Column(Boolean)"),
]

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    """Read and parse a JSON file, returning None on failure."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"  [WARN] Could not read {path}: {exc}")
        return None


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write a dict as pretty-printed JSON."""
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    print(f"  [OK]   Written: {path}")


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"  [OK]   Written: {path}")


def _find_repo_root() -> Path:
    """Walk up from CWD to find the repo root (contains package.json or pyproject.toml)."""
    current = Path.cwd()
    for candidate in [current, *current.parents]:
        if (candidate / "package.json").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return current


# ---------------------------------------------------------------------------
# 1. Jest / package.json coverage config migration
#    Spec: "coverage reporters, coverage thresholds, or output formats beyond a bare
#           coverageDirectory setting"
# ---------------------------------------------------------------------------

def migrate_jest_coverage_config(package_json_path: Path) -> bool:
    """
    Migrate the Jest configuration inside package.json to add:
      - coverageReporters (text, lcov, json-summary, clover)
      - coverageThreshold (branches/functions/lines/statements at 70%)
      - Ensure collectCoverageFrom is correctly set

    Returns True if changes were made.
    """
    print(f"\n[Jest] Migrating Jest coverage config in: {package_json_path}")

    data = _read_json(package_json_path)
    if data is None:
        return False

    jest_config: Dict[str, Any] = data.get("jest", {})
    changed = False

    # ── coverageReporters ──────────────────────────────────────────────────
    existing_reporters = jest_config.get("coverageReporters", [])
    if set(existing_reporters) != set(JEST_COVERAGE_REPORTERS):
        print(f"  [CHANGE] coverageReporters: {existing_reporters!r} → {JEST_COVERAGE_REPORTERS!r}")
        jest_config["coverageReporters"] = JEST_COVERAGE_REPORTERS
        changed = True
    else:
        print("  [SKIP]  coverageReporters already configured correctly.")

    # ── coverageThreshold ──────────────────────────────────────────────────
    existing_threshold = jest_config.get("coverageThreshold", {})
    desired_threshold = {"global": JEST_COVERAGE_THRESHOLDS}
    if existing_threshold != desired_threshold:
        print(f"  [CHANGE] coverageThreshold: adding global thresholds {JEST_COVERAGE_THRESHOLDS!r}")
        jest_config["coverageThreshold"] = desired_threshold
        changed = True
    else:
        print("  [SKIP]  coverageThreshold already configured correctly.")

    # ── collectCoverageFrom ────────────────────────────────────────────────
    existing_collect = jest_config.get("collectCoverageFrom", [])
    if existing_collect != JEST_COLLECT_COVERAGE_FROM:
        print(f"  [CHANGE] collectCoverageFrom: {existing_collect!r} → {JEST_COLLECT_COVERAGE_FROM!r}")
        jest_config["collectCoverageFrom"] = JEST_COLLECT_COVERAGE_FROM
        changed = True
    else:
        print("  [SKIP]  collectCoverageFrom already configured correctly.")

    # ── coverageDirectory ─────────────────────────────────────────────────
    if "coverageDirectory" not in jest_config:
        print("  [CHANGE] coverageDirectory: adding 'coverage'")
        jest_config["coverageDirectory"] = "coverage"
        changed = True

    # ── testEnvironment ───────────────────────────────────────────────────
    if jest_config.get("testEnvironment") != "node":
        print("  [CHANGE] testEnvironment: setting to 'node'")
        jest_config["testEnvironment"] = "node"
        changed = True

    if changed:
        data["jest"] = jest_config
        _write_json(package_json_path, data)
    else:
        print("  [SKIP]  No Jest config changes required.")

    # TODO: If you add a separate jest.config.js, ensure it does not conflict with
    #       the jest key in package.json. Jest merges configs from only one source.
    #       Breaking change ref: Jest 29 dropped support for jest.config.ts without
    #       ts-jest; use jest.config.js or the package.json jest key exclusively.

    return changed


# ---------------------------------------------------------------------------
# 2. pytest-cov configuration (Python test infra)
#    Spec: "Add pytest-cov for Test Coverage Reporting"
#    NOTE: The primary stack is Node.js/Jest. This section handles any Python
#          components that exist or will be added to the repo.
# ---------------------------------------------------------------------------

def generate_pytest_ini_options() -> str:
    """
    Return the [tool.pytest.ini_options] TOML block for pytest-cov.
    Spec: pytest-cov, source=src, reporters=term-missing/lcov/xml/html, min=70
    """
    report_args = " ".join(f"--cov-report={fmt}" for fmt in PYTEST_COV_REPORT_FORMATS)
    return textwrap.dedent(f"""\
        [tool.pytest.ini_options]
        addopts = "--cov={PYTEST_COV_SOURCE} {report_args} --cov-fail-under={PYTEST_MIN_COVERAGE}"
        testpaths = ["tests"]

        [tool.coverage.run]
        source = ["{PYTEST_COV_SOURCE}"]
        omit = [
            "*/tests/*",
            "*/__pycache__/*",
            "*/migrations/*",
        ]

        [tool.coverage.report]
        show_missing = true
        skip_covered = false
        fail_under = {PYTEST_MIN_COVERAGE}

        [tool.coverage.html]
        directory = "htmlcov"

        [tool.coverage.xml]
        output = "coverage.xml"

        [tool.coverage.lcov]
        output = "coverage.lcov"
    """)


def generate_setup_cfg_coverage() -> str:
    """
    Return a setup.cfg [coverage:run] / [coverage:report] block as a fallback
    for projects not yet using pyproject.toml.
    """
    omit_lines = "\n    ".join([
        "*/tests/*",
        "*/__pycache__/*",
        "*/migrations/*",
    ])
    report_formats = "\n    ".join(PYTEST_COV_REPORT_FORMATS)
    return textwrap.dedent(f"""\
        [tool:pytest]
        addopts = --cov={PYTEST_COV_SOURCE} --cov-report=term-missing --cov-report=lcov --cov-report=xml --cov-report=html --cov-fail-under={PYTEST_MIN_COVERAGE}
        testpaths = tests

        [coverage:run]
        source = {PYTEST_COV_SOURCE}
        omit =
            {omit_lines}

        [coverage:report]
        show_missing = True
        fail_under = {PYTEST_MIN_COVERAGE}

        [coverage:html]
        directory = htmlcov

        [coverage:xml]
        output = coverage.xml
    """)


def migrate_pyproject_toml(pyproject_path: Path) -> bool:
    """
    Add or update pytest-cov configuration in pyproject.toml.
    Returns True if changes were made.
    """
    print(f"\n[Python] Migrating pyproject.toml for pytest-cov: {pyproject_path}")

    existing = _read_text(pyproject_path)

    if existing is None:
        # Create a minimal pyproject.toml with pytest-cov config
        print("  [CREATE] pyproject.toml not found — creating with pytest-cov config.")
        content = textwrap.dedent("""\
            [build-system]
            requires = ["setuptools>=68", "wheel"]
            build-backend = "setuptools.backends.legacy:build"

        """) + generate_pytest_ini_options()
        _write_text(pyproject_path, content)
        return True

    if "[tool.pytest.ini_options]" in existing:
        print("  [SKIP]  [tool.pytest.ini_options] already present in pyproject.toml.")
        print("          Review manually to ensure pytest-cov addopts are included.")
        # TODO: Manually verify that --cov, --cov-report, and --cov-fail-under flags
        #       are present in the addopts value. Automated merge of TOML arrays is
        #       not performed here to avoid corrupting existing config.
        return False

    # Append pytest-cov config block
    new_content = existing.rstrip("\n") + "\n\n" + generate_pytest_ini_options()
    _write_text(pyproject_path, new_content)
    return True


def migrate_setup_cfg(setup_cfg_path: Path) -> bool:
    """
    Add pytest-cov configuration to setup.cfg if pyproject.toml is absent.
    Returns True if changes were made.
    """
    print(f"\n[Python] Migrating setup.cfg for pytest-cov: {setup_cfg_path}")

    existing = _read_text(setup_cfg_path)

    if existing is None:
        print("  [CREATE] setup.cfg not found — creating with pytest-cov config.")
        _write_text(setup_cfg_path, generate_setup_cfg_coverage())
        return True

    if "[coverage:run]" in existing or "[tool:pytest]" in existing:
        print("  [SKIP]  Coverage config already present in setup.cfg.")
        # TODO: Manually verify --cov-fail-under and --cov-report flags in [tool:pytest] addopts.
        return False

    new_content = existing.rstrip("\n") + "\n\n" + generate_setup_cfg_coverage()
    _write_text(setup_cfg_path, new_content)
    return True


def ensure_pytest_cov_in_requirements(repo_root: Path) -> None:
    """
    Check common requirements files and warn if pytest-cov is absent.
    Spec: pytest-cov is a dev dependency.
    """
    print("\n[Python] Checking for pytest-cov in requirements files...")

    candidates = [
        repo_root / "requirements-dev.txt",
        repo_root / "requirements_dev.txt",
        repo_root / "requirements-test.txt",
        repo_root / "requirements.txt",
        repo_root / "pyproject.toml",
    ]

    found_in: list[Path] = []
    for candidate in candidates:
        content = _read_text(candidate)
        if content and "pytest-cov" in content:
            found_in.append(candidate)

    if found_in:
        print(f"  [OK]   pytest-cov found in: {[str(p) for p in found_in]}")
    else:
        print("  [WARN] pytest-cov not found in any requirements file.")
        print("         Add it manually:")
        print("           pip install pytest-cov")
        print("           # or add to requirements-dev.txt:")
        print("           pytest-cov>=4.1.0")
        # TODO: Add pytest-cov>=4.1.0 to your requirements-dev.txt or pyproject.toml
        #       [project.optional-dependencies] dev section. This is required for the
        #       --cov flags injected into pytest addopts to resolve at runtime.


# ---------------------------------------------------------------------------
# 3. Flask 1.x → 3.1 compatibility shim
#    Spec: Flask 1.x → 3.1 (urgency: critical)
# ---------------------------------------------------------------------------

# TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: flask.ext.* namespace was removed. Any import of the form
#   `from flask.ext.something import X` must be replaced with `from flask_something import X`.
#
# TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: The `PROPAGATE_EXCEPTIONS` config key behaviour changed.
#   In Flask 3.x, exceptions are always propagated in testing mode. Remove any
#   explicit `app.config['PROPAGATE_EXCEPTIONS'] = True` in test setup.
#
# TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: `flask.json` module restructured. `flask.json.provider.DefaultJSONProvider`
#   is the new extension point. Replace any subclass of `flask.json.JSONEncoder` with
#   a subclass of `flask.json.provider.DefaultJSONProvider` and assign to `app.json_provider_class`.
#
# TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: Application factory pattern is now strongly recommended.
#   The `create_app()` factory must be used instead of a module-level `app = Flask(__name__)`.
#   The user-management service already uses `createApp()` in Node.js; mirror this pattern
#   in any Python Flask components.
#
# TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: `before_first_request` decorator removed in Flask 3.x.
#   Replace with explicit initialisation inside the application factory or use
#   `with app.app_context(): init_db()` patterns.
#
# TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: `flask.signals` (blinker) is now a required dependency, not optional.
#   Ensure `blinker` is listed in your requirements.

def flask_compat_shim():
    """
    Compatibility shim providing Flask 1.x API aliases backed by Flask 3.x equivalents.
    Import this module in place of direct Flask imports during the migration period.

    Usage in migrating code:
        from migration_helper import flask_compat_shim as flask_shim
        # Then use flask_shim.Flask, flask_shim.jsonify, etc.
    """
    try:
        import flask
        from flask import Flask, jsonify, request, g, current_app
        from flask import Blueprint, render_template, redirect, url_for, abort
    except ImportError:
        # TODO: Install Flask 3.1: pip install "Flask>=3.1,<4.0"
        warnings.warn(
            "Flask is not installed. Install Flask>=3.1: pip install 'Flask>=3.1,<4.0'",
            ImportWarning,
            stacklevel=2,
        )
        return None

    flask_version = tuple(int(x) for x in flask.__version__.split(".")[:2])

    if flask_version < (3, 0):
        # TODO (Flask 1.x → 3.1): You are running Flask < 3.0. The following
        #   breaking changes require manual code updates before upgrading:
        #   - Remove all uses of flask.ext.*
        #   - Replace flask.json.JSONEncoder subclasses with DefaultJSONProvider
        #   - Replace @app.before_first_request with factory-pattern init
        #   - Add blinker to requirements
        warnings.warn(
            f"Flask {flask.__version__} detected. Target is Flask 3.1. "
            "Run this migration helper after upgrading Flask to validate shims.",
            DeprecationWarning,
            stacklevel=2,
        )

    # Re-export stable API surface (unchanged between 1.x and 3.x)
    return {
        "Flask": Flask,
        "jsonify": jsonify,
        "request": request,
        "g": g,
        "current_app": current_app,
        "Blueprint": Blueprint,
        "render_template": render_template,
        "redirect": redirect,
        "url_for": url_for,
        "abort": abort,
    }


def migrate_flask_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a Flask 1.x application config dict to Flask 3.x compatible format.

    Breaking changes addressed:
    - PRESERVE_CONTEXT_ON_EXCEPTION renamed/removed (Flask 3.x always preserves in debug)
    - JSON_SORT_KEYS moved to app.json.sort_keys
    - JSON_AS_ASCII moved to app.json.ensure_ascii (inverted)
    - JSONIFY_PRETTYPRINT_REGULAR moved to app.json.compact (inverted)
    - JSONIFY_MIMETYPE moved to app.json.mimetype
    """
    new_config = dict(old_config)

    # ── JSON config keys (Flask 1.x → 3.x) ───────────────────────────────
    # TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
    #   JSON_SORT_KEYS, JSON_AS_ASCII, JSONIFY_PRETTYPRINT_REGULAR, and
    #   JSONIFY_MIMETYPE are no longer top-level config keys in Flask 3.x.
    #   They must be set on the app.json provider instance after app creation:
    #     app.json.sort_keys = False
    #     app.json.ensure_ascii = False   # was JSON_AS_ASCII = False
    #     app.json.compact = True         # was JSONIFY_PRETTYPRINT_REGULAR = False
    #     app.json.mimetype = "application/json"
    #   This function removes them from the config dict and emits warnings.

    json_key_migrations = {
        "JSON_SORT_KEYS": ("app.json.sort_keys", lambda v: v),
        "JSON_AS_ASCII": ("app.json.ensure_ascii", lambda v: v),
        "JSONIFY_PRETTYPRINT_REGULAR": ("app.json.compact", lambda v: not v),
        "JSONIFY_MIMETYPE": ("app.json.mimetype", lambda v: v),
    }

    for old_key, (new_attr, transform) in json_key_migrations.items():
        if old_key in new_config:
            old_val = new_config.pop(old_key)
            new_val = transform(old_val)
            warnings.warn(
                f"Flask config key '{old_key}' is removed in Flask 3.x. "
                f"Set '{new_attr} = {new_val!r}' on the app instance after creation. "
                f"(Breaking change: Flask 1.x → 3.1)",
                DeprecationWarning,
                stacklevel=2,
            )

    # ── PRESERVE_CONTEXT_ON_EXCEPTION ─────────────────────────────────────
    if "PRESERVE_CONTEXT_ON_EXCEPTION" in new_config:
        new_config.pop("PRESERVE_CONTEXT_ON_EXCEPTION")
        # TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
        #   PRESERVE_CONTEXT_ON_EXCEPTION is removed. Flask 3.x always preserves
        #   the context on exception when TESTING=True. Remove this key from config.
        warnings.warn(
            "PRESERVE_CONTEXT_ON_EXCEPTION is removed in Flask 3.x. "
            "Remove it from your config. (Breaking change: Flask 1.x → 3.1)",
            DeprecationWarning,
            stacklevel=2,
        )

    # ── SEND_FILE_MAX_AGE_DEFAULT ──────────────────────────────────────────
    if "SEND_FILE_MAX_AGE_DEFAULT" in new_config:
        val = new_config["SEND_FILE_MAX_AGE_DEFAULT"]
        if isinstance(val, int):
            # Flask 3.x expects a timedelta or None, not an integer seconds value
            # TODO (Flask 1.x → 3.1 — MANUAL INTERVENTION REQUIRED):
            #   SEND_FILE_MAX_AGE_DEFAULT must be a datetime.timedelta or None in Flask 3.x,
            #   not an integer. Replace: SEND_FILE_MAX_AGE_DEFAULT = 43200
            #   with: from datetime import timedelta; SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=43200)
            warnings.warn(
                "SEND_FILE_MAX_AGE_DEFAULT must be a datetime.timedelta in Flask 3.x, not int. "
                "(Breaking change: Flask 1.x → 3.1)",
                DeprecationWarning,
                stacklevel=2,
            )

    return new_config


# ---------------------------------------------------------------------------
# 4. SQLAlchemy 1.3 → 2.0 compatibility shim
#    Spec: SQLAlchemy 1.3 → 2.0 (urgency: critical)
# ---------------------------------------------------------------------------

# TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: The legacy Query API (session.query(Model)) is removed in 2.0.
#   All queries must use the new select() construct:
#     Old: session.query(User).filter_by(email=email).first()
#     New: session.execute(select(User).filter_by(email=email)).scalars().first()
#
# TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: Implicit autocommit is removed. All write operations must be
#   wrapped in an explicit transaction:
#     with session.begin():
#         session.add(obj)
#   or use session.commit() / session.rollback() explicitly.
#
# TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: relationship() lazy loading behaviour changed. Add
#   lazy="select" explicitly where 1.3 implicit lazy loading was relied upon,
#   or migrate to explicit joinedload() / selectinload() in queries.
#
# TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: Column type Boolean with create_constraint=True is deprecated.
#   Remove create_constraint argument from Boolean columns.
#
# TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
#   Breaking change: Engine.execute() and Connection.execute(string) removed.
#   Use session.execute(text("...")) with explicit text() wrapper for raw SQL.

def sqlalchemy_session_shim(session_factory):
    """
    Wraps a SQLAlchemy 2.0 session factory to provide a compatibility layer
    for code still using 1.3-style session.query() patterns.

    This shim emits DeprecationWarnings for legacy usage and delegates to
    the 2.0 API. It is intended as a transitional aid — not a permanent solution.

    Args:
        session_factory: A SQLAlchemy 2.0 sessionmaker or scoped_session factory.

    Returns:
        A wrapped session class with legacy shim methods.
    """
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import Session
    except ImportError:
        # TODO: Install SQLAlchemy 2.0: pip install "SQLAlchemy>=2.0,<3.0"
        warnings.warn(
            "SQLAlchemy is not installed. Install SQLAlchemy>=2.0: "
            "pip install 'SQLAlchemy>=2.0,<3.0'",
            ImportWarning,
            stacklevel=2,
        )
        return session_factory

    class LegacyQueryShim:
        """
        Shim that intercepts legacy session.query(Model) calls and routes them
        to the SQLAlchemy 2.0 select() API.

        TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
          Replace all session.query(Model) usages with select(Model) constructs.
          This shim covers only the most common patterns. Complex query chains
          (e.g. .join(), .options(), .with_entities()) require manual migration.
        """

        def __init__(self, session: "Session", model):
            self._session = session
            self._model = model
            self._stmt = select(model)
            warnings.warn(
                f"session.query({model.__name__}) is removed in SQLAlchemy 2.0. "
                f"Use session.execute(select({model.__name__})).scalars() instead. "
                "(Breaking change: SQLAlchemy 1.3 → 2.0)",
                DeprecationWarning,
                stacklevel=3,
            )

        def filter_by(self, **kwargs):
            self._stmt = self._stmt.filter_by(**kwargs)
            return self

        def filter(self, *criteria):
            self._stmt = self._stmt.filter(*criteria)
            return self

        def all(self):
            return self._session.execute(self._stmt).scalars().all()

        def first(self):
            return self._session.execute(self._stmt).scalars().first()

        def one(self):
            return self._session.execute(self._stmt).scalars().one()

        def one_or_none(self):
            return self._session.execute(self._stmt).scalars().one_or_none()

        def get(self, pk):
            # TODO (SQLAlchemy 1.3 → 2.0): session.query(Model).get(pk) →
            #   session.get(Model, pk)
            warnings.warn(
                f"session.query({self._model.__name__}).get(pk) is removed in SQLAlchemy 2.0. "
                f"Use session.get({self._model.__name__}, pk) instead. "
                "(Breaking change: SQLAlchemy 1.3 → 2.0)",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._session.get(self._model, pk)

        def count(self):
            from sqlalchemy import func
            count_stmt = select(func.count()).select_from(self._model)
            return self._session.execute(count_stmt).scalar()

        def delete(self):
            # TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
            #   Bulk delete via query().delete() is removed. Use:
            #     session.execute(delete(Model).filter(...))
            #   with explicit synchronize_session parameter.
            warnings.warn(
                "query().delete() is removed in SQLAlchemy 2.0. "
                "Use session.execute(delete(Model).filter(...)) instead. "
                "(Breaking change: SQLAlchemy 1.3 → 2.0)",
                DeprecationWarning,
                stacklevel=2,
            )
            from sqlalchemy import delete as sa_delete
            del_stmt = sa_delete(self._model).filter(self._stmt.whereclause)
            return self._session.execute(del_stmt)

    class CompatSession(Session):
        """
        SQLAlchemy 2.0 Session subclass that adds a legacy query() shim.
        Use this as the class= argument to sessionmaker() during migration.

        Example:
            engine = create_engine(DATABASE_URL)
            SessionLocal = sessionmaker(bind=engine, class_=CompatSession)
        """

        def query(self, model):
            return LegacyQueryShim(self, model)

    return CompatSession


def migrate_sqlalchemy_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a SQLAlchemy 1.3-style engine/session config dict to 2.0 format.

    Addresses:
    - convert_unicode removed (always True in 2.0)
    - implicit_returning default changed (now always True)
    - pool_timeout / pool_recycle units unchanged but validate presence
    - echo_pool renamed handling
    """
    new_config = dict(old_config)

    # ── convert_unicode removed in 2.0 ────────────────────────────────────
    if "convert_unicode" in new_config:
        new_config.pop("convert_unicode")
        # TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
        #   convert_unicode is removed from create_engine() in SQLAlchemy 2.0.
        #   Unicode conversion is always enabled. Remove this argument.
        warnings.warn(
            "create_engine(convert_unicode=...) is removed in SQLAlchemy 2.0. "
            "Remove this argument. (Breaking change: SQLAlchemy 1.3 → 2.0)",
            DeprecationWarning,
            stacklevel=2,
        )

    # ── implicit_returning ─────────────────────────────────────────────────
    if "implicit_returning" in new_config and new_config["implicit_returning"] is False:
        # TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
        #   implicit_returning=False is no longer supported in SQLAlchemy 2.0.
        #   RETURNING is always used where the database supports it.
        warnings.warn(
            "implicit_returning=False is not supported in SQLAlchemy 2.0. "
            "Remove this argument. (Breaking change: SQLAlchemy 1.3 → 2.0)",
            DeprecationWarning,
            stacklevel=2,
        )
        new_config.pop("implicit_returning")

    # ── use_batch_mode (psycopg2 dialect) ─────────────────────────────────
    if "use_batch_mode" in new_config:
        new_config.pop("use_batch_mode")
        # TODO (SQLAlchemy 1.3 → 2.0 — MANUAL INTERVENTION REQUIRED):
        #   use_batch_mode is removed. Use executemany_mode='values' in the
        #   psycopg2 dialect URL parameters instead.
        warnings.warn(
            "use_batch_mode is removed in SQLAlchemy 2.0. "
            "Use executemany_mode='values' in dialect URL params. "
            "(Breaking change: SQLAlchemy 1.3 → 2.0)",
            DeprecationWarning,
            stacklevel=2,
        )

    return new_config


# ---------------------------------------------------------------------------
# 5. Python version compatibility check
#    Spec: Python 3.8 (EOL) → 3.12 or 3.13
# ---------------------------------------------------------------------------

def check_python_version() -> None:
    """
    Warn if the current Python version is below the target (3.12).
    Spec: Upgrade Python from 3.8 (EOL) to 3.12 or 3.13.
    """
    current = sys.version_info
    print(f"\n[Python] Runtime version: {sys.version}")

    if current < (3, 12):
        # TODO (Python 3.8 → 3.12 — MANUAL INTERVENTION REQUIRED):
        #   Python 3.8 reached EOL on 2024-10-07. Upgrade to Python 3.12 or 3.13.
        #   Steps:
        #     1. Update pyenv: pyenv install 3.12.x && pyenv local 3.12.x
        #     2. Recreate virtualenv: python3.12 -m venv .venv
        #     3. Reinstall dependencies: pip install -r requirements.txt
        #     4. Update Dockerfile: FROM python:3.12-slim
        #     5. Update CI matrix: python-version: ["3.12", "3.13"]
        #   Breaking changes from 3.8 → 3.12:
        #     - distutils removed (use setuptools)
        #     - asyncio.coroutine decorator removed (use async def)
        #     - collections.abc aliases in collections removed (use collections.abc.*)
        #     - typing.io and typing.re removed (use io and re directly)
        warnings.warn(
            f"Python {current.major}.{current.minor} detected. "
            "Target is Python 3.12+. Python 3.8 is EOL. "
            "Upgrade to Python 3.12 or 3.13. (Breaking change: Python 3.8 → 3.12)",
            DeprecationWarning,
            stacklevel=2,
        )
        print(f"  [WARN] Python {current.major}.{current.minor} is below target 3.12.")
    else:
        print(f"  [OK]   Python {current.major}.{current.minor} meets target (>=3.12).")


# ---------------------------------------------------------------------------
# 6. Scan Python source files for deprecated patterns
#    Covers Flask and SQLAlchemy breaking changes from spec
# ---------------------------------------------------------------------------

def scan_python_files_for_deprecated_patterns(root: Path) -> None:
    """
    Walk the repo and flag Python files containing known deprecated API patterns
    from Flask 1.x and SQLAlchemy 1.3 that require manual migration.
    """
    print(f"\n[Scan] Scanning Python files under: {root}")

    all_patterns = [
        # Flask 1.x → 3.x
        (r"flask\.ext\.", "Flask: flask.ext.* namespace removed in Flask 3.x"),
        (r"before_first_request", "Flask: @before_first_request removed in Flask 3.x"),
        (r"flask\.json\.JSONEncoder", "Flask: JSONEncoder replaced by DefaultJSONProvider in Flask 3.x"),
        (r"PRESERVE_CONTEXT_ON_EXCEPTION", "Flask: PRESERVE_CONTEXT_ON_EXCEPTION removed in Flask 3.x"),
        (r"JSON_SORT_KEYS", "Flask: JSON_SORT_KEYS config key removed in Flask 3.x"),
        (r"JSON_AS_ASCII", "Flask: JSON_AS_ASCII config key removed in Flask 3.x"),
        (r"JSONIFY_PRETTYPRINT_REGULAR", "Flask: JSONIFY_PRETTYPRINT_REGULAR config key removed in Flask 3.x"),
        # SQLAlchemy 1.3 → 2.0
        (r"session\.query\(", "SQLAlchemy: session.query() removed in 2.0 — use select()"),
        (r"\.query\.filter_by\(", "SQLAlchemy: .query.filter_by() removed in 2.0"),
        (r"\.query\.filter\(", "SQLAlchemy: .query.filter() removed in 2.0"),
        (r"\.query\.get\(", "SQLAlchemy: .query.get() removed in 2.0 — use session.get()"),
        (r"convert_unicode", "SQLAlchemy: convert_unicode removed from create_engine() in 2.0"),
        (r"implicit_returning\s*=\s*False", "SQLAlchemy: implicit_returning=False not supported in 2.0"),
        (r"use_batch_mode", "SQLAlchemy: use_batch_mode removed in 2.0"),
        (r"Engine\.execute\(", "SQLAlchemy: Engine.execute() removed in 2.0 — use session.execute()"),
        (r"autocommit\s*=\s*True", "SQLAlchemy: implicit autocommit removed in 2.0"),
        # Python 3.8 → 3.12
        (r"from collections import (Mapping|Sequence|MutableMapping|Callable)",
         "Python: collections.abc aliases removed in 3.10+ — use collections.abc.*"),
        (r"asyncio\.coroutine", "Python: asyncio.coroutine removed in 3.11"),
        (r"import distutils", "Python: distutils removed in 3.12 — use setuptools"),
    ]

    compiled = [(re.compile(pat), msg) for pat, msg in all_patterns]
    hits: list[tuple[Path, int, str, str]] = []

    for py_file in root.rglob("*.py"):
        # Skip this migration helper itself
        if py_file.name == "migration_helper.py":
            continue
        try:
            lines = py_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            for pattern, message in compiled:
                if pattern.search(line):
                    hits.append((py_file, lineno, line.strip(), message))

    if hits:
        print(f"  [WARN] Found {len(hits)} deprecated pattern(s) requiring manual migration:\n")
        for path, lineno, line, message in hits:
            rel = path.relative_to(root) if path.is_relative_to(root) else path
            print(f"    {rel}:{lineno}")
            print(f"      Pattern : {message}")
            print(f"      Line    : {line[:120]}")
            print()
    else:
        print("  [OK]   No deprecated patterns found in Python source files.")


# ---------------------------------------------------------------------------
# 7. Hardcoded credentials check
#    Spec: "Remove hardcoded credentials and introduce environment-based secrets management"
# ---------------------------------------------------------------------------

# TODO (Hardcoded credentials — MANUAL INTERVENTION REQUIRED):
#   The spec requires removing hardcoded credentials and using environment variables.
#   This scanner flags common patterns. All flagged occurrences require manual review
#   and replacement with os.environ.get('SECRET_NAME') or a secrets manager call.

_CREDENTIAL_PATTERNS = [
    (r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}['\"]", "Possible hardcoded password"),
    (r"(?i)(secret|api_key|apikey|token)\s*=\s*['\"][^'\"]{8,}['\"]", "Possible hardcoded secret/key"),
    (r"(?i)(stripe_api_key|sk_live_|sk_test_)", "Possible hardcoded Stripe key"),
    (r"(?i)(paypal_client_secret)\s*=\s*['\"][^'\"]{4,}['\"]", "Possible hardcoded PayPal secret"),
    (r"(?i)jwt_secret\s*=\s*['\"][^'\"]{4,}['\"]", "Possible hardcoded JWT secret"),
    (r"(?i)smtp_pass\s*=\s*['\"][^'\"]{4,}['\"]", "Possible hardcoded SMTP password"),
]


def scan_for_hardcoded_credentials(root: Path) -> None:
    """
    Scan Python and JavaScript files for hardcoded credentials.
    Spec: "Remove hardcoded credentials and introduce environment-based secrets management"
    """
    print(f"\n[Security] Scanning for hardcoded credentials under: {root}")

    compiled = [(re.compile(pat), msg) for pat, msg in _CREDENTIAL_PATTERNS]
    hits: list[tuple[Path, int, str, str]] = []

    for ext in ("*.py", "*.js", "*.ts", "*.env", "*.cfg", "*.ini", "*.yaml", "*.yml"):
        for src_file in root.rglob(ext):
            if any(skip in src_file.parts for skip in ("node_modules", ".git", "__pycache__", "coverage")):
                continue
            if src_file.name in (".env.example",):
                continue
            try:
                lines = src_file.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, start=1):
                for pattern, message in compiled:
                    if pattern.search(line):
                        hits.append((src_file, lineno, line.strip(), message))

    if hits:
        print(f"  [WARN] Found {len(hits)} potential hardcoded credential(s):\n")
        for path, lineno, line, message in hits:
            rel = path.relative_to(root) if path.is_relative_to(root) else path
            print(f"    {rel}:{lineno} — {message}")
            print(f"      {line[:120]}")
            # TODO (Hardcoded credentials — MANUAL INTERVENTION REQUIRED):
            #   Replace hardcoded value with: os.environ.get('VARIABLE_NAME')
            #   or load from a .env file using python-dotenv:
            #     from dotenv import load_dotenv; load_dotenv()
            print()
    else:
        print("  [OK]   No hardcoded credentials detected.")


# ---------------------------------------------------------------------------
# 8. Main orchestration
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 70)
    print("Migration Helper — Flask 3.1 / SQLAlchemy 2.0 / pytest-cov / Python 3.12")
    print("=" * 70)

    repo_root = _find_repo_root()
    print(f"\nRepo root detected: {repo_root}")

    exit_code = 0

    # ── Python version check ───────────────────────────────────────────────
    check_python_version()

    # ── Jest / package.json migration ──────────────────────────────────────
    package_json_candidates = [
        repo_root / "user-management" / "package.json",
        repo_root / "package.json",
    ]
    for pkg_path in package_json_candidates:
        if pkg_path.exists():
            migrate_jest_coverage_config(pkg_path)

    # ── Python test infra (pytest-cov) ─────────────────────────────────────
    pyproject_path = repo_root / "pyproject.toml"
    setup_cfg_path = repo_root / "setup.cfg"

    if pyproject_path.exists():
        migrate_pyproject_toml(pyproject_path)
    elif setup_cfg_path.exists():
        migrate_setup_cfg(setup_cfg_path)
    else:
        # Neither exists — check if there are Python files that warrant creating one
        py_files = list(repo_root.rglob("*.py"))
        # Exclude this helper itself
        py_files = [p for p in py_files if p.name != "migration_helper.py"]
        if py_files:
            print(f"\n[Python] Found {len(py_files)} Python file(s) but no pyproject.toml or setup.cfg.")
            print("         Creating pyproject.toml with pytest-cov configuration.")
            migrate_pyproject_toml(pyproject_path)
        else:
            print("\n[Python] No Python source files found. Skipping pytest-cov config generation.")
            print("         If you add Python components, re-run this helper to generate config.")

    ensure_pytest_cov_in_requirements(repo_root)

    # ── Scan for deprecated patterns ───────────────────────────────────────
    scan_python_files_for_deprecated_patterns(repo_root)

    # ── Scan for hardcoded credentials ─────────────────────────────────────
    scan_for_hardcoded_credentials(repo_root)

    # ── Summary of manual TODOs ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("MANUAL INTERVENTION REQUIRED — Summary of TODOs")
    print("=" * 70)
    todos = [
        # Flask 1.x → 3.1
        ("Flask 1.x → 3.1",
         "Replace flask.ext.* imports with flask_* package imports"),
        ("Flask 1.x → 3.1",
         "Replace @app.before_first_request with factory-pattern initialisation"),
        ("Flask 1.x → 3.1",
         "Replace flask.json.JSONEncoder subclasses with DefaultJSONProvider"),
        ("Flask 1.x → 3.1",
         "Remove PRESERVE_CONTEXT_ON_EXCEPTION from app config"),
        ("Flask 1.x → 3.1",
         "Move JSON_SORT_KEYS/JSON_AS_ASCII/JSONIFY_* to app.json.* attributes"),
        ("Flask 1.x → 3.1",
         "Add blinker to requirements (now a required Flask dependency)"),
        ("Flask 1.x → 3.1",
         "Adopt application factory pattern: create_app() returning Flask instance"),
        # SQLAlchemy 1.3 → 2.0
        ("SQLAlchemy 1.3 → 2.0",
         "Replace all session.query(Model) with session.execute(select(Model)).scalars()"),
        ("SQLAlchemy 1.3 → 2.0",
         "Replace session.query(Model).get(pk) with session.get(Model, pk)"),
        ("SQLAlchemy 1.3 → 2.0",
         "Wrap all write operations in explicit transactions (no implicit autocommit)"),
        ("SQLAlchemy 1.3 → 2.0",
         "Remove convert_unicode and implicit_returning=False from create_engine()"),
        ("SQLAlchemy 1.3 → 2.0",
         "Replace Engine.execute() with session.execute(text(...))"),
        ("SQLAlchemy 1.3 → 2.0",
         "Audit relationship() lazy loading — add explicit lazy= arguments"),
        # Python 3.8 → 3.12
        ("Python 3.8 → 3.12",
         "Upgrade Python runtime to 3.12 or 3.13 (3.8 is EOL)"),
        ("Python 3.8 → 3.12",
         "Replace distutils imports with setuptools"),
        ("Python 3.8 → 3.12",
         "Replace collections.Mapping/Sequence/etc with collections.abc.*"),
        ("Python 3.8 → 3.12",
         "Remove asyncio.coroutine usage — use async def"),
        # pytest-cov
        ("pytest-cov",
         "Add pytest-cov>=4.1.0 to requirements-dev.txt or pyproject.toml dev deps"),
        ("pytest-cov",
         "Verify --cov-fail-under threshold is appropriate for your codebase"),
        # Credentials
        ("Security",
         "Remove all hardcoded credentials; use environment variables or secrets manager"),
        ("Security",
         "Add .env to .gitignore; use .env.example for documentation only"),
        # CI/CD
        ("CI/CD",
         "Add Dockerfile for Python services (FROM python:3.12-slim)"),
        ("CI/CD",
         "Add GitHub Actions workflow with dependency vulnerability scanning (pip-audit)"),
        ("CI/CD",
         "Upload coverage.xml / coverage.lcov as CI artefacts for coverage reporting"),
    ]

    for category, description in todos:
        print(f"  [{category}] {description}")

    print("\nMigration helper complete.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())