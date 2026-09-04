# migration_shim.py
# Compatibility shim for: Replace unittest with pytest + fixture-based DB isolation
# Covers: Flask 1.x -> 3.1, SQLAlchemy 1.3 -> 2.0, Python 3.8 -> 3.12/3.13
#
# Usage:
#   python migration_shim.py            # run config migration + print guidance
#   python migration_shim.py --check    # dry-run, print what would change
#
# NOTE: This shim targets the Python layer of the monorepo. The user-management
# service is Node.js/Jest; pytest migration for that layer requires manual work
# (see TODO comments below).

from __future__ import annotations

import ast
import importlib
import os
import re
import sys
import textwrap
import warnings
from contextlib import contextmanager
from typing import Any, Dict, Generator, Iterator, Optional

# ---------------------------------------------------------------------------
# Python version guard
# ---------------------------------------------------------------------------
# TODO: The upgrade goal targets Python 3.12 or 3.13. This shim runs on 3.8+
# but the target runtime must be 3.12+. Update your Dockerfile / pyenv config
# accordingly. See spec.md: "Upgrade Python from 3.8 (EOL) to 3.12 or 3.13".
if sys.version_info < (3, 8):
    raise RuntimeError("This shim requires Python 3.8 or newer.")

# ---------------------------------------------------------------------------
# Dependency availability probes
# ---------------------------------------------------------------------------

def _try_import(name: str) -> Optional[Any]:
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


_flask = _try_import("flask")
_sqlalchemy = _try_import("sqlalchemy")
_pytest = _try_import("pytest")


# ===========================================================================
# SECTION 1 — Flask 1.x → 3.1 compatibility shims
# ===========================================================================
#
# Breaking changes addressed (from spec.md / design.md):
#   • flask.ext.* namespace removed → use direct package imports
#   • flask.json.provider API changed
#   • Application factory pattern now required
#   • flask.escape moved to markupsafe.escape
#   • flask.Markup moved to markupsafe.Markup
#   • before_first_request removed
#   • flask.signals (blinker) now a hard dependency
#   • Response.autocorrect_location_header removed
#   • send_file / send_from_directory: attachment_filename → download_name
# ===========================================================================

# --- 1a. Markup / escape re-exports -------------------------------------------
# Flask 1.x exposed these directly; Flask 3.x removed them.
# TODO: Replace all `from flask import Markup, escape` in your source files
# with `from markupsafe import Markup, escape` (breaking change: Flask 3.x).

try:
    from markupsafe import Markup, escape  # noqa: F401  (re-export)
except ImportError:
    # TODO: Add markupsafe to requirements.txt — it ships with Flask 3.x but
    # must be explicit if you import it directly.
    Markup = None  # type: ignore[assignment,misc]
    escape = None  # type: ignore[assignment]


# --- 1b. Application factory shim --------------------------------------------
# Flask 1.x apps often called app.run() at module level.
# Flask 3.x strongly recommends the application factory pattern.
# TODO: Refactor your app entry-point to use create_app() factory.
# See design.md: "Upgrade Flask from 1.x (EOL) to 3.x with application factory pattern".

def create_app(config: Optional[Dict[str, Any]] = None):
    """
    Minimal application factory shim.

    Replace this stub with your real factory once you have migrated to Flask 3.x.
    Import and call this function from your WSGI entry-point (wsgi.py) and from
    pytest fixtures (see Section 3 below).

    TODO: Move all blueprint registrations, extension initialisations, and
    configuration loading into this function body.
    """
    if _flask is None:
        raise ImportError(
            "Flask is not installed. Run: pip install 'Flask>=3.1,<4'"
        )

    flask = _flask
    app = flask.Flask(__name__)

    # --- Load config ----------------------------------------------------------
    if config is not None:
        app.config.update(config)

    # TODO: Register blueprints here, e.g.:
    #   from .routes.payments import payments_bp
    #   app.register_blueprint(payments_bp, url_prefix="/api/payments")

    # TODO: Initialise SQLAlchemy extension here (see Section 2).

    return app


# --- 1c. before_first_request removal ----------------------------------------
# Flask 3.x removed @app.before_first_request.
# TODO: Replace every @app.before_first_request decorator with an explicit
# call inside create_app(), or use @app.cli.command("init-db") for one-time
# setup. Breaking change documented in Flask 3.0 changelog.

def _warn_before_first_request_removed() -> None:
    warnings.warn(
        "@app.before_first_request was removed in Flask 2.3 and is absent in "
        "Flask 3.x. Move one-time startup logic into create_app() or a CLI "
        "command. See spec.md breaking change: 'before_first_request removed'.",
        DeprecationWarning,
        stacklevel=2,
    )


# --- 1d. send_file / send_from_directory: attachment_filename → download_name --
# TODO: Rename every kwarg `attachment_filename=` to `download_name=` in calls
# to flask.send_file() and flask.send_from_directory().
# Breaking change: Flask 2.0+, still absent in Flask 3.x.

def send_file_compat(path_or_file, *, attachment_filename=None, download_name=None, **kwargs):
    """
    Wrapper around flask.send_file that accepts the old `attachment_filename`
    keyword argument and forwards it as `download_name` for Flask 3.x.

    TODO: Replace direct flask.send_file calls with this wrapper, then remove
    the wrapper once all call-sites have been updated.
    """
    if _flask is None:
        raise ImportError("Flask is not installed.")
    if attachment_filename is not None and download_name is None:
        warnings.warn(
            "attachment_filename is removed in Flask 3.x; use download_name instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        download_name = attachment_filename
    return _flask.send_file(path_or_file, download_name=download_name, **kwargs)


# ===========================================================================
# SECTION 2 — SQLAlchemy 1.3 → 2.0 compatibility shims
# ===========================================================================
#
# Breaking changes addressed (from spec.md / design.md):
#   • Query API (session.query()) soft-deprecated → use select() / Session.execute()
#   • Engine.execute() removed → use Connection.execute()
#   • autocommit mode removed from Core
#   • declarative_base() moved: sqlalchemy.ext.declarative → sqlalchemy.orm
#   • relationship() lazy="joined" behaviour changes
#   • Column type changes (Boolean, JSON strict mode)
#   • LegacyQuery shim available via future=True flag during transition
# ===========================================================================

# --- 2a. declarative_base re-export ------------------------------------------
# SQLAlchemy 1.3: from sqlalchemy.ext.declarative import declarative_base
# SQLAlchemy 2.0: from sqlalchemy.orm import declarative_base  (or DeclarativeBase)
# TODO: Update all imports of declarative_base to use sqlalchemy.orm.

try:
    # 2.0 canonical location
    from sqlalchemy.orm import declarative_base as _declarative_base_20  # noqa: F401
    declarative_base = _declarative_base_20
except ImportError:
    try:
        # 1.3 / 1.4 fallback — will warn
        from sqlalchemy.ext.declarative import declarative_base  # type: ignore[no-redef]  # noqa: F401
        warnings.warn(
            "sqlalchemy.ext.declarative.declarative_base is removed in SQLAlchemy 2.0. "
            "Import from sqlalchemy.orm instead. "
            "See spec.md: 'SQLAlchemy 1.3 → 2.0 and migrate to new query API'.",
            DeprecationWarning,
            stacklevel=1,
        )
    except ImportError:
        declarative_base = None  # type: ignore[assignment]


# --- 2b. Session factory helper ----------------------------------------------
# Provides a 2.0-style Session factory. During transition you can pass
# future=True to a 1.4 engine to opt into 2.0 behaviour.
# TODO: Replace all direct sessionmaker() calls with get_session_factory() and
# remove the future=True flag once fully on 2.0.

def get_session_factory(engine):
    """
    Returns a SQLAlchemy 2.0-compatible sessionmaker bound to *engine*.

    In SQLAlchemy 1.4 the `future=True` flag enables 2.0-style behaviour.
    In SQLAlchemy 2.0 the flag is the default and can be omitted.

    TODO: Remove the try/except once SQLAlchemy 1.3/1.4 support is dropped.
    """
    if _sqlalchemy is None:
        raise ImportError(
            "SQLAlchemy is not installed. Run: pip install 'SQLAlchemy>=2.0,<3'"
        )
    from sqlalchemy.orm import sessionmaker

    try:
        # SQLAlchemy 2.0 — future flag is default, no-op if passed
        factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    except TypeError:
        # Older 1.4 path
        factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)  # type: ignore[call-arg]
    return factory


# --- 2c. Legacy Query shim ---------------------------------------------------
# session.query(Model) is soft-deprecated in 2.0.
# Provide a thin wrapper that emits a DeprecationWarning and delegates to the
# new select() API so call-sites can be migrated incrementally.
# TODO: Replace every session.query(X).filter(...).all() with
#   session.execute(select(X).where(...)).scalars().all()
# after updating each call-site, remove the use of LegacyQueryShim entirely.

class LegacyQueryShim:
    """
    Thin compatibility wrapper that accepts SQLAlchemy 1.x-style .query() calls
    and re-issues them via the 2.0 select() API.

    Usage (temporary, during migration only):
        shim = LegacyQueryShim(session)
        results = shim.query(User).filter(User.email == email).all()

    TODO: Remove this class once all query call-sites have been migrated to
    the SQLAlchemy 2.0 select() API. Breaking change: 'migrate to new query API'.
    """

    def __init__(self, session):
        self._session = session

    def query(self, *entities):
        warnings.warn(
            "session.query() is deprecated in SQLAlchemy 2.0. "
            "Use session.execute(select(...)) instead. "
            "See spec.md: 'SQLAlchemy 1.3 → 2.0 and migrate to new query API'.",
            DeprecationWarning,
            stacklevel=2,
        )
        if _sqlalchemy is None:
            raise ImportError("SQLAlchemy is not installed.")
        from sqlalchemy import select as sa_select

        class _ChainedQuery:
            def __init__(self_, entities_, session_):
                self_._entities = entities_
                self_._session = session_
                self_._stmt = sa_select(*entities_)

            def filter(self_, *criteria):
                self_._stmt = self_._stmt.where(*criteria)
                return self_

            def filter_by(self_, **kwargs):
                # SQLAlchemy 2.0 select() supports filter_by via .filter_by()
                self_._stmt = self_._stmt.filter_by(**kwargs)
                return self_

            def order_by(self_, *clauses):
                self_._stmt = self_._stmt.order_by(*clauses)
                return self_

            def limit(self_, n):
                self_._stmt = self_._stmt.limit(n)
                return self_

            def first(self_):
                result = self_._session.execute(self_._stmt).scalars().first()
                return result

            def all(self_):
                return self_._session.execute(self_._stmt).scalars().all()

            def one(self_):
                return self_._session.execute(self_._stmt).scalars().one()

            def one_or_none(self_):
                return self_._session.execute(self_._stmt).scalars().one_or_none()

            def count(self_):
                from sqlalchemy import func
                count_stmt = sa_select(func.count()).select_from(self_._stmt.subquery())
                return self_._session.execute(count_stmt).scalar()

        return _ChainedQuery(entities, self._session)


# --- 2d. Engine.execute() removal shim ---------------------------------------
# SQLAlchemy 2.0 removed engine.execute(). Use engine.connect() + conn.execute().
# TODO: Replace every engine.execute(stmt) with:
#   with engine.connect() as conn:
#       result = conn.execute(stmt)
#       conn.commit()  # if write operation

def engine_execute_compat(engine, statement, *args, **kwargs):
    """
    Compatibility wrapper for the removed engine.execute() API.

    TODO: Replace all call-sites with explicit engine.connect() context managers
    and remove this function. Breaking change: 'Engine.execute() removed in 2.0'.
    """
    warnings.warn(
        "engine.execute() was removed in SQLAlchemy 2.0. "
        "Use 'with engine.connect() as conn: conn.execute(...)' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    with engine.connect() as conn:
        result = conn.execute(statement, *args, **kwargs)
        conn.commit()
        return result


# ===========================================================================
# SECTION 3 — pytest fixtures for DB isolation
# ===========================================================================
#
# These fixtures are designed to be placed in conftest.py at the root of your
# test directory. They provide:
#   • A fresh Flask application instance per test session / function
#   • A SQLAlchemy engine backed by an in-memory SQLite DB (isolated per test)
#   • A scoped DB session that rolls back after each test
#
# TODO: Copy the fixture definitions below into your tests/conftest.py.
# TODO: If you use PostgreSQL in production, install pytest-postgresql and
# replace the SQLite engine with a PostgreSQL test engine.
# See spec.md: "Add fixture-based DB isolation".
# ===========================================================================

CONFTEST_TEMPLATE = textwrap.dedent(
    '''
    # tests/conftest.py
    # Auto-generated by migration_shim.py — review and adjust before committing.
    #
    # TODO: Replace SQLite in-memory engine with your production DB engine config
    # if you need dialect-specific behaviour in tests.
    # TODO: Import your real SQLAlchemy Base and models below.

    import pytest
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # TODO: Replace this import with your actual declarative Base
    # from myapp.models import Base
    # from myapp import create_app  # your application factory

    # ---------------------------------------------------------------------------
    # Application fixture
    # ---------------------------------------------------------------------------

    @pytest.fixture(scope="session")
    def app():
        """
        Create a Flask application configured for testing.

        Scope: session — one app instance for the entire test run.
        TODO: Import and call your real create_app() factory here.
        TODO: Set TESTING=True and DATABASE_URL to the in-memory SQLite URI.
        """
        # TODO: Uncomment and adapt:
        # from myapp import create_app
        # application = create_app({
        #     "TESTING": True,
        #     "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        #     "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        #     "SECRET_KEY": "test-secret-key",
        # })
        # yield application
        raise NotImplementedError(
            "Replace this stub with your real create_app() call. "
            "See migration_shim.py Section 3."
        )


    @pytest.fixture(scope="session")
    def client(app):
        """Flask test client, session-scoped."""
        return app.test_client()


    # ---------------------------------------------------------------------------
    # Database engine fixture (isolated per test session)
    # ---------------------------------------------------------------------------

    @pytest.fixture(scope="session")
    def db_engine(app):
        """
        Create an in-memory SQLite engine and initialise the schema once per
        test session.

        TODO: Replace SQLite with your real DB URL for integration tests that
        require dialect-specific SQL.
        TODO: Import your Base and call Base.metadata.create_all(engine).
        """
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        # TODO: Uncomment once Base is importable:
        # Base.metadata.create_all(engine)
        yield engine
        engine.dispose()


    # ---------------------------------------------------------------------------
    # DB session fixture — rolls back after every test (function scope)
    # ---------------------------------------------------------------------------

    @pytest.fixture(scope="function")
    def db_session(db_engine):
        """
        Provide a transactional SQLAlchemy session that is rolled back after
        each test, ensuring full DB isolation without truncating tables.

        Pattern: begin a SAVEPOINT, yield the session, rollback to SAVEPOINT.
        This is the standard pytest-sqlalchemy isolation pattern.

        TODO: If you use async SQLAlchemy (2.0 async API), replace with
        AsyncSession and async fixtures.
        """
        connection = db_engine.connect()
        transaction = connection.begin()

        Session = sessionmaker(bind=connection, autocommit=False, autoflush=False)
        session = Session()

        # Nested transaction (SAVEPOINT) so individual test commits are invisible
        # to other tests and the outer transaction can be rolled back cleanly.
        nested = connection.begin_nested()

        yield session

        session.close()
        # Roll back to the state before this test ran
        if nested.is_active:
            nested.rollback()
        transaction.rollback()
        connection.close()


    # ---------------------------------------------------------------------------
    # InMemoryUserRepository fixture (for unit tests that do not need SQLAlchemy)
    # ---------------------------------------------------------------------------

    @pytest.fixture(scope="function")
    def in_memory_user_repo():
        """
        Returns a fresh InMemoryUserRepository instance for each test.

        This replaces the Jest beforeEach pattern of constructing a new
        repository instance, ensuring no shared mutable state between tests.

        TODO: Import your Python equivalent of InMemoryUserRepository.
        The Node.js version lives in:
          user-management/src/adapters/outbound/persistence/InMemoryUserRepository.js
        If you are migrating to Python, implement the equivalent class first.
        See spec.md: "DB isolation gap — InMemoryUserRepository shared Map".
        """
        # TODO: Uncomment once Python InMemoryUserRepository exists:
        # from myapp.adapters.persistence import InMemoryUserRepository
        # return InMemoryUserRepository()
        raise NotImplementedError(
            "Implement Python InMemoryUserRepository and update this fixture."
        )
    '''
)


def write_conftest(target_dir: str = "tests", dry_run: bool = False) -> None:
    """Write the conftest.py template to *target_dir*/conftest.py."""
    os.makedirs(target_dir, exist_ok=True)
    dest = os.path.join(target_dir, "conftest.py")
    if dry_run:
        print(f"[DRY-RUN] Would write conftest.py to: {dest}")
        print(CONFTEST_TEMPLATE)
        return
    if os.path.exists(dest):
        print(f"[SKIP] {dest} already exists — not overwriting. Review manually.")
        return
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(CONFTEST_TEMPLATE.lstrip("\n"))
    print(f"[WRITTEN] {dest}")


# ===========================================================================
# SECTION 4 — Config format migration
# ===========================================================================
#
# Transforms old-style Flask/SQLAlchemy config dicts to the new format
# required by Flask 3.x and SQLAlchemy 2.0.
#
# Old format (Flask 1.x + SQLAlchemy 1.3):
#   SQLALCHEMY_TRACK_MODIFICATIONS = True   (default was True, now must be False)
#   SQLALCHEMY_DATABASE_URI = "..."
#   SECRET_KEY = "hardcoded-secret"         (must move to env var)
#   DEBUG = True                            (must not be set in production)
#
# New format (Flask 3.x + SQLAlchemy 2.0):
#   SQLALCHEMY_TRACK_MODIFICATIONS = False  (removed in 2.0, set False to silence)
#   SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
#   SECRET_KEY = os.environ["SECRET_KEY"]
#   TESTING = True/False
# ===========================================================================

def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform an old Flask 1.x / SQLAlchemy 1.3 config dict into a
    Flask 3.x / SQLAlchemy 2.0 compatible config dict.

    Args:
        old_config: dict of config key-value pairs from the old application.

    Returns:
        A new dict with deprecated keys replaced or removed.

    Raises:
        ValueError: if a hardcoded SECRET_KEY is detected (must use env var).
    """
    new_config: Dict[str, Any] = dict(old_config)
    migration_log: list[str] = []

    # --- SQLALCHEMY_TRACK_MODIFICATIONS ---------------------------------------
    # SQLAlchemy 2.0 removed the event system that this flag controlled.
    # Flask-SQLAlchemy 3.x raises an error if it is True.
    # TODO: Remove SQLALCHEMY_TRACK_MODIFICATIONS from your config entirely
    # once you are on Flask-SQLAlchemy 3.x — it is no longer recognised.
    if new_config.get("SQLALCHEMY_TRACK_MODIFICATIONS") is True:
        new_config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        migration_log.append(
            "SQLALCHEMY_TRACK_MODIFICATIONS: True → False "
            "(removed in SQLAlchemy 2.0 / Flask-SQLAlchemy 3.x)"
        )

    # --- Hardcoded SECRET_KEY -------------------------------------------------
    # TODO: Remove hardcoded credentials and introduce environment-based secrets
    # management. See spec.md: "Remove hardcoded credentials".
    secret = new_config.get("SECRET_KEY", "")
    if isinstance(secret, str) and secret and not secret.startswith("${") and not secret.startswith("os.environ"):
        # Heuristic: if it looks like a literal string (not an env-var reference)
        # warn loudly. We do NOT replace it automatically to avoid breaking tests.
        migration_log.append(
            "SECRET_KEY appears to be a hardcoded literal. "
            "Move it to an environment variable: os.environ['SECRET_KEY']. "
            "See spec.md: 'Remove hardcoded credentials'."
        )
        warnings.warn(
            "Hardcoded SECRET_KEY detected. Use os.environ['SECRET_KEY'] instead.",
            UserWarning,
            stacklevel=2,
        )

    # --- DATABASE_URL / SQLALCHEMY_DATABASE_URI -------------------------------
    # TODO: Replace any hardcoded DB URIs with os.environ["DATABASE_URL"].
    db_uri = new_config.get("SQLALCHEMY_DATABASE_URI", "")
    if isinstance(db_uri, str) and db_uri and not db_uri.startswith("${"):
        if any(cred in db_uri for cred in ["password", "secret", "admin", "root"]):
            migration_log.append(
                "SQLALCHEMY_DATABASE_URI may contain credentials. "
                "Use os.environ['DATABASE_URL'] and store credentials in .env. "
                "See spec.md: 'Remove hardcoded credentials'."
            )
            warnings.warn(
                "Potential credentials in SQLALCHEMY_DATABASE_URI. "
                "Move to DATABASE_URL environment variable.",
                UserWarning,
                stacklevel=2,
            )

    # --- PROPAGATE_EXCEPTIONS (Flask 1.x testing pattern) --------------------
    # Flask 3.x uses TESTING=True; PROPAGATE_EXCEPTIONS is still supported but
    # the recommended pattern changed.
    if "PROPAGATE_EXCEPTIONS" in new_config:
        migration_log.append(
            "PROPAGATE_EXCEPTIONS: still supported in Flask 3.x but prefer "
            "setting TESTING=True and letting pytest capture exceptions."
        )

    # --- JSON_SORT_KEYS (Flask 3.x default changed) --------------------------
    # Flask 3.x changed the default JSON provider. JSON_SORT_KEYS defaults to
    # True in 1.x but the new provider may behave differently.
    # TODO: Explicitly set JSON_SORT_KEYS if your tests assert on key ordering.
    if "JSON_SORT_KEYS" not in new_config:
        new_config["JSON_SORT_KEYS"] = True
        migration_log.append(
            "JSON_SORT_KEYS not set — defaulting to True for backwards "
            "compatibility with Flask 1.x behaviour. "
            "Review if your tests assert on JSON key order."
        )

    # --- SQLALCHEMY_ENGINE_OPTIONS (new in 2.0) --------------------------------
    # SQLAlchemy 2.0 recommends explicit pool configuration.
    # TODO: Add SQLALCHEMY_ENGINE_OPTIONS with pool settings appropriate for
    # your deployment (pool_pre_ping=True is strongly recommended).
    if "SQLALCHEMY_ENGINE_OPTIONS" not in new_config:
        new_config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
        migration_log.append(
            "SQLALCHEMY_ENGINE_OPTIONS not set — added pool_pre_ping=True. "
            "Review pool_size and max_overflow for production."
        )

    # --- Report ---------------------------------------------------------------
    if migration_log:
        print("\n[migrate_config] Applied the following transformations:")
        for entry in migration_log:
            print(f"  • {entry}")
    else:
        print("[migrate_config] No transformations required.")

    return new_config


# ===========================================================================
# SECTION 5 — unittest → pytest import shims
# ===========================================================================
#
# If any Python test files still use unittest.TestCase, these shims allow them
# to run under pytest without modification while you migrate them incrementally.
#
# TODO: Migrate each TestCase class to a plain pytest function/class.
# pytest can collect unittest.TestCase subclasses natively, but fixtures
# (Section 3) are NOT injected into TestCase methods — that requires migration.
# See spec.md: "Replace unittest with pytest".
# ===========================================================================

# Re-export unittest symbols so old `from migration_shim import TestCase` works.
import unittest  # noqa: E402 (stdlib, always available)

TestCase = unittest.TestCase  # re-export alias

# Provide pytest.mark equivalents for common unittest decorators
if _pytest is not None:
    skip = _pytest.mark.skip
    skipIf = staticmethod(lambda cond, reason: _pytest.mark.skipif(cond, reason=reason))
    expectedFailure = _pytest.mark.xfail
else:
    # Fallback stubs so imports don't crash if pytest isn't installed yet
    skip = unittest.skip  # type: ignore[assignment]
    skipIf = unittest.skipIf  # type: ignore[assignment]
    expectedFailure = unittest.expectedFailure  # type: ignore[assignment]


class AssertionMixin:
    """
    Mixin that provides unittest-style assertion helpers as thin wrappers
    around plain assert statements, making migration to pytest-style assertions
    incremental.

    TODO: Replace usages of these methods with direct assert statements and
    pytest.raises() / pytest.approx() as you migrate each test file.
    """

    def assertEqual(self, first, second, msg=None):
        assert first == second, msg or f"{first!r} != {second!r}"

    def assertNotEqual(self, first, second, msg=None):
        assert first != second, msg or f"{first!r} == {second!r}"

    def assertTrue(self, expr, msg=None):
        assert expr, msg or f"Expected truthy, got {expr!r}"

    def assertFalse(self, expr, msg=None):
        assert not expr, msg or f"Expected falsy, got {expr!r}"

    def assertIsNone(self, obj, msg=None):
        assert obj is None, msg or f"Expected None, got {obj!r}"

    def assertIsNotNone(self, obj, msg=None):
        assert obj is not None, msg or f"Expected non-None value"

    def assertIn(self, member, container, msg=None):
        assert member in container, msg or f"{member!r} not in {container!r}"

    def assertNotIn(self, member, container, msg=None):
        assert member not in container, msg or f"{member!r} in {container!r}"

    def assertRaises(self, exc, callable_=None, *args, **kwargs):
        # Delegate to pytest.raises when available for better output
        if _pytest is not None and callable_ is None:
            return _pytest.raises(exc)
        if callable_ is not None:
            try:
                callable_(*args, **kwargs)
            except exc:
                return
            raise AssertionError(f"{exc.__name__} not raised")
        return _pytest.raises(exc) if _pytest else unittest.TestCase().assertRaises(exc)

    def assertAlmostEqual(self, first, second, places=7, msg=None):
        if _pytest is not None:
            import pytest as _pt
            assert first == _pt.approx(second, abs=10 ** -places), msg
        else:
            assert round(abs(first - second), places) == 0, msg


# ===========================================================================
# SECTION 6 — requirements.txt migration helper
# ===========================================================================
#
# Prints the recommended requirements changes to stdout.
# TODO: Apply these changes to your requirements.txt / pyproject.toml.
# ===========================================================================

REQUIREMENTS_DIFF = """
# ============================================================
# requirements.txt — recommended changes for this upgrade
# ============================================================
#
# REMOVE (old / incompatible):
#   Flask==1.*
#   SQLAlchemy==1.3.*
#   Flask-SQLAlchemy==2.*
#
# ADD / PIN (new):
#   Flask>=3.1,<4
#   SQLAlchemy>=2.0,<3
#   Flask-SQLAlchemy>=3.1,<4
#   markupsafe>=2.1          # now a direct dependency (was bundled in Flask 1.x)
#   blinker>=1.6             # now a hard Flask dependency (signals)
#
# TEST dependencies (add to requirements-dev.txt or [dev] extras):
#   pytest>=8.0
#   pytest-flask>=1.3        # Flask test fixtures for pytest
#   pytest-sqlalchemy>=0.2   # SQLAlchemy session fixtures (or use conftest.py above)
#   pytest-cov>=5.0          # coverage (replaces jest --coverage for Python layer)
#   factory-boy>=3.3         # recommended for fixture data generation
#
# TODO: Pin exact versions after running pip-compile or pip install --dry-run.
# TODO: Add pip-audit or safety to CI for dependency vulnerability scanning.
# See spec.md: "Add CI/CD pipeline with dependency vulnerability scanning".
"""


def print_requirements_diff() -> None:
    print(REQUIREMENTS_DIFF)


# ===========================================================================
# SECTION 7 — Source file scanner
# ===========================================================================
#
# Scans Python source files under a given directory and reports patterns that
# need manual migration. Does NOT modify files.
# ===========================================================================

_PATTERNS = [
    (
        r"from\s+flask\.ext\.",
        "flask.ext.* namespace removed in Flask 1.0+. Use direct package imports.",
    ),
    (
        r"from\s+flask\s+import\s+.*\b(Markup|escape)\b",
        "flask.Markup / flask.escape removed in Flask 3.x. "
        "Use: from markupsafe import Markup, escape",
    ),
    (
        r"@app\.before_first_request",
        "@app.before_first_request removed in Flask 2.3/3.x. "
        "Move logic into create_app() or a CLI command.",
    ),
    (
        r"attachment_filename\s*=",
        "attachment_filename kwarg removed in Flask 2.0+. Use download_name=.",
    ),
    (
        r"from\s+sqlalchemy\.ext\.declarative\s+import\s+declarative_base",
        "sqlalchemy.ext.declarative.declarative_base moved to sqlalchemy.orm "
        "in SQLAlchemy 2.0.",
    ),
    (
        r"session\.query\(",
        "session.query() is deprecated in SQLAlchemy 2.0. "
        "Use session.execute(select(...)).scalars().",
    ),
    (
        r"engine\.execute\(",
        "engine.execute() removed in SQLAlchemy 2.0. "
        "Use engine.connect() + conn.execute().",
    ),
    (
        r"import\s+unittest",
        "unittest import detected. Migrate to pytest. "
        "See spec.md: 'Replace unittest with pytest'.",
    ),
    (
        r"class\s+\w+\(.*TestCase.*\)",
        "unittest.TestCase subclass detected. "
        "Migrate to plain pytest class or function. "
        "Note: pytest fixtures are NOT injected into TestCase methods.",
    ),
    (
        r"SQLALCHEMY_TRACK_MODIFICATIONS\s*=\s*True",
        "SQLALCHEMY_TRACK_MODIFICATIONS=True is an error in Flask-SQLAlchemy 3.x. "
        "Set to False or remove.",
    ),
]


def scan_sources(root_dir: str = ".") -> Dict[str, list]:
    """
    Walk *root_dir* recursively, scan .py files for known migration patterns,
    and return a dict mapping file paths to lists of (line_no, message) tuples.
    """
    findings: Dict[str, list] = {}
    compiled = [(re.compile(pat), msg) for pat, msg in _PATTERNS]

    for dirpath, _dirnames, filenames in os.walk(root_dir):
        # Skip virtual environments and hidden directories
        _dirnames[:] = [
            d for d in _dirnames
            if d not in {"venv", ".venv", "env", ".env", "__pycache__", ".git", "node_modules"}
        ]
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            except OSError:
                continue
            file_findings = []
            for lineno, line in enumerate(lines, start=1):
                for pattern, message in compiled:
                    if pattern.search(line):
                        file_findings.append((lineno, message, line.rstrip()))
            if file_findings:
                findings[fpath] = file_findings

    return findings


def print_scan_report(findings: Dict[str, list]) -> None:
    if not findings:
        print("[scan] No migration issues found in Python source files.")
        return
    total = sum(len(v) for v in findings.values())
    print(f"\n[scan] Found {total} migration issue(s) across {len(findings)} file(s):\n")
    for fpath, issues in sorted(findings.items()):
        print(f"  {fpath}")
        for lineno, message, line_text in issues:
            print(f"    Line {lineno:4d}: {message}")
            print(f"             > {line_text}")
        print()


# ===========================================================================
# SECTION 8 — pytest.ini / setup.cfg migration helper
# ===========================================================================
#
# Writes a minimal pytest.ini if one does not already exist.
# TODO: Review and extend with your project-specific settings.
# ===========================================================================

PYTEST_INI_TEMPLATE = textwrap.dedent(
    """\
    # pytest.ini — generated by migration_shim.py
    # TODO: Adjust testpaths, python_files, and markers for your project layout.
    # TODO: Add --cov flags once pytest-cov is installed.

    [pytest]
    testpaths = tests
    python_files = test_*.py *_test.py
    python_classes = Test*
    python_functions = test_*
    addopts =
        -v
        --tb=short
        # TODO: Uncomment after installing pytest-cov:
        # --cov=myapp
        # --cov-report=term-missing
        # --cov-report=xml:coverage.xml
    markers =
        unit: marks tests as unit tests (no I/O)
        integration: marks tests as integration tests (requires DB)
        slow: marks tests as slow (deselect with -m "not slow")
    """
)


def write_pytest_ini(dry_run: bool = False) -> None:
    dest = "pytest.ini"
    if dry_run:
        print(f"[DRY-RUN] Would write: {dest}")
        print(PYTEST_INI_TEMPLATE)
        return
    if os.path.exists(dest):
        print(f"[SKIP] {dest} already exists — not overwriting.")
        return
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(PYTEST_INI_TEMPLATE)
    print(f"[WRITTEN] {dest}")


# ===========================================================================
# SECTION 9 — Node.js / Jest layer notice
# ===========================================================================
#
# The user-management service is Node.js + Jest. pytest does NOT apply there.
# The spec acknowledges this conflict. Manual steps are required.
#
# TODO (manual): The user-management service uses Jest 29.7.0. If the intent
# is to keep it in Node.js, do NOT replace Jest with pytest — they are
# different language ecosystems. Instead:
#   1. Add beforeEach(() => { repo = new InMemoryUserRepository(); }) in each
#      Jest describe block to reset shared state (DB isolation equivalent).
#   2. Consider jest.isolateModules() for module-level isolation.
#   3. If migrating user-management to Python, implement Python equivalents of:
#      - InMemoryUserRepository (user-management/src/adapters/outbound/persistence/)
#      - RegisterUser, LoginUser, RecoverPassword, VerifyAccount use cases
#      - NodemailerEmailAdapter (replace with smtplib or an email library)
#   4. Only after Python equivalents exist should the conftest.py fixtures
#      in Section 3 be wired up.
# See spec.md: "Note: The source code provided is a Node.js/JavaScript codebase".
# ===========================================================================

NODEJS_JEST_ISOLATION_SNIPPET = textwrap.dedent(
    """\
    // Jest DB isolation snippet for InMemoryUserRepository
    // Add this pattern to each describe() block that uses the repository.
    //
    // TODO: Apply this pattern to all test files under user-management/src/__tests__/
    // See spec.md: "DB isolation gap — InMemoryUserRepository shared Map".

    const InMemoryUserRepository = require(
      '../adapters/outbound/persistence/InMemoryUserRepository'
    );

    describe('MyUseCase', () => {
      let repo;

      beforeEach(() => {
        // Fresh repository instance per test — eliminates shared mutable state.
        repo = new InMemoryUserRepository();
      });

      test('example test', async () => {
        // repo._store is empty at the start of every test
      });
    });
    """
)


# ===========================================================================
# SECTION 10 — Main entry point
# ===========================================================================

def main(dry_run: bool = False) -> None:
    print("=" * 70)
    print("migration_shim.py — Flask 1.x→3.1 / SQLAlchemy 1.3→2.0 / pytest")
    print("=" * 70)

    # 1. Scan Python sources
    print("\n--- Step 1: Scanning Python source files ---")
    findings = scan_sources(".")
    print_scan_report(findings)

    # 2. Write conftest.py
    print("\n--- Step 2: Writing tests/conftest.py ---")
    write_conftest(target_dir="tests", dry_run=dry_run)

    # 3. Write pytest.ini
    print("\n--- Step 3: Writing pytest.ini ---")
    write_pytest_ini(dry_run=dry_run)

    # 4. Print requirements diff
    print("\n--- Step 4: Requirements changes ---")
    print_requirements_diff()

    # 5. Demo config migration
    print("\n--- Step 5: Demo config migration ---")
    example_old_config = {
        "SECRET_KEY": "hardcoded-dev-secret",
        "SQLALCHEMY_DATABASE_URI": "postgresql://admin:password@localhost/mydb",
        "SQLALCHEMY_TRACK_MODIFICATIONS": True,
        "DEBUG": True,
    }
    print("Input config:", example_old_config)
    migrate_config(example_old_config)

    # 6. Node.js / Jest notice
    print("\n--- Step 6: Node.js / Jest isolation snippet ---")
    print("Write the following pattern to each Jest describe() block:")
    print(NODEJS_JEST_ISOLATION_SNIPPET)

    # 7. Final TODO summary
    print("\n--- Manual intervention required (TODOs) ---")
    todos = [
        "Upgrade Python runtime from 3.8 to 3.12 or 3.13 (update Dockerfile / pyenv).",
        "Run: pip install 'Flask>=3.1,<4' 'SQLAlchemy>=2.0,<3' 'Flask-SQLAlchemy>=3.1,<4'",
        "Run: pip install pytest pytest-flask pytest-cov factory-boy",
        "Refactor Flask app entry-point to use create_app() application factory.",
        "Replace @app.before_first_request with logic inside create_app().",
        "Replace all session.query() calls with select() / session.execute().",
        "Replace engine.execute() with engine.connect() + conn.execute().",
        "Move SECRET_KEY and DATABASE_URL to environment variables (.env file).",
        "Update tests/conftest.py stubs with real imports (see Section 3 TODOs).",
        "Apply Jest beforeEach isolation pattern to Node.js test files (Section 9).",
        "Add Dockerfile and GitHub Actions CI with pip-audit vulnerability scanning.",
        "Review SQLALCHEMY_ENGINE_OPTIONS pool settings for production.",
    ]
    for i, todo in enumerate(todos, start=1):
        print(f"  {i:2d}. TODO: {todo}")

    print("\nDone.")


if __name__ == "__main__":
    dry_run = "--check" in sys.argv
    main(dry_run=dry_run)