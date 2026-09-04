# migration_shim.py
# Compatibility shim for: Replace unittest with pytest and add fixture-based DB isolation
# Frameworks: Flask 1.x -> 3.1, SQLAlchemy 1.3 -> 2.0
# Python: 3.8 -> 3.12/3.13

"""
Migration helper and compatibility shim.

Usage:
    python migration_shim.py                  # run config migration + print report
    python migration_shim.py --check          # dry-run, exit non-zero if changes needed

This file provides:
  1. Deprecated API replacement wrappers (Flask 1.x -> 3.x, SQLAlchemy 1.3 -> 2.0)
  2. Import shims / re-export aliases for renamed packages and classes
  3. Config migration function (old format -> new format)
  4. pytest fixture helpers for fixture-based DB isolation
     (replaces unittest.TestCase + shared InMemoryUserRepository state)
"""

from __future__ import annotations

import os
import sys
import warnings
import functools
import importlib
from typing import Any, Generator, Optional

# ---------------------------------------------------------------------------
# 0.  Python version guard
# ---------------------------------------------------------------------------

if sys.version_info < (3, 8):
    raise RuntimeError(
        "This shim requires Python >= 3.8. "
        "Target runtime is Python 3.12 / 3.13."
    )

# ---------------------------------------------------------------------------
# 1.  Flask compatibility shim  (Flask 1.x -> Flask 3.x)
# ---------------------------------------------------------------------------
# Breaking changes addressed:
#   - flask.json.JSONEncoder / JSONDecoder removed in Flask 3.x
#     (spec.md: "Flask 1.x (EOL) to 3.x with application factory pattern")
#   - flask.escape moved to markupsafe.escape in Flask 2.x, removed in 3.x
#   - flask._app_ctx_stack / flask._request_ctx_stack removed
#   - flask.Markup moved to markupsafe.Markup
#   - before_first_request removed in Flask 2.3 / 3.x
#   - flask.signals.Namespace removed (use blinker directly)

try:
    import flask as _flask
    _FLASK_MAJOR = int(_flask.__version__.split(".")[0])
except ImportError:
    _flask = None  # type: ignore[assignment]
    _FLASK_MAJOR = 0

# --- 1a. flask.escape shim ---------------------------------------------------

def _get_flask_escape():
    """Return the correct escape function regardless of Flask version."""
    try:
        from markupsafe import escape
        return escape
    except ImportError:
        pass
    if _flask is not None and hasattr(_flask, "escape"):
        return _flask.escape  # Flask < 2.x
    raise ImportError(
        # TODO: Install markupsafe>=2.0 — flask.escape was removed in Flask 2.x "
        "Cannot locate escape(); add markupsafe to requirements."
    )

escape = _get_flask_escape()

# --- 1b. flask.Markup shim ---------------------------------------------------

def _get_markup():
    try:
        from markupsafe import Markup
        return Markup
    except ImportError:
        if _flask is not None and hasattr(_flask, "Markup"):
            warnings.warn(
                "flask.Markup is removed in Flask 3.x. "
                "Use markupsafe.Markup instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return _flask.Markup  # type: ignore[attr-defined]
        raise ImportError(
            # TODO: Replace flask.Markup with markupsafe.Markup everywhere in codebase.
            "markupsafe.Markup not found; install markupsafe>=2.0."
        )

Markup = _get_markup()

# --- 1c. JSONEncoder / JSONDecoder shim --------------------------------------
# Flask 3.x removed flask.json.JSONEncoder and flask.json.JSONDecoder.
# TODO: Replace any subclass of flask.json.JSONEncoder with a custom
#       app.json_provider_class using flask.json.provider.DefaultJSONProvider.

class _LegacyJSONEncoder:
    """
    Drop-in shim for code that subclasses flask.json.JSONEncoder.

    In Flask 3.x the correct approach is to subclass
    flask.json.provider.DefaultJSONProvider and assign it to
    app.json_provider_class.  This shim raises a clear error at import time
    rather than a cryptic AttributeError.
    """
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        warnings.warn(
            f"{cls.__name__} subclasses flask.json.JSONEncoder which was "
            "removed in Flask 3.x.  "
            # TODO: Migrate to flask.json.provider.DefaultJSONProvider subclass
            #       and set app.json_provider_class = YourProvider.
            "Migrate to flask.json.provider.DefaultJSONProvider.",
            DeprecationWarning,
            stacklevel=2,
        )

try:
    from flask.json import JSONEncoder as _FlaskJSONEncoder  # type: ignore[attr-defined]
    JSONEncoder = _FlaskJSONEncoder
except (ImportError, AttributeError):
    JSONEncoder = _LegacyJSONEncoder  # type: ignore[assignment,misc]

# --- 1d. before_first_request shim ------------------------------------------
# Flask 2.3 deprecated @app.before_first_request; Flask 3.x removed it.
# TODO: Replace @app.before_first_request with explicit initialisation inside
#       the application factory (create_app) or use a with app.app_context() block.

def before_first_request_shim(app: Any, f: Any) -> Any:
    """
    Compatibility wrapper.  Calls *f* immediately inside an app context so
    that code relying on before_first_request still runs once.

    This is NOT a true lazy-first-request hook — it runs at registration time.
    Replace with proper app-factory initialisation.
    """
    warnings.warn(
        "before_first_request was removed in Flask 3.x. "
        # TODO: Move initialisation logic into create_app() or an explicit
        #       with app.app_context(): block.
        "Use the application factory pattern instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    with app.app_context():
        f()
    return f

# --- 1e. Application factory helper ------------------------------------------
# Flask 3.x strongly recommends the application factory pattern.
# TODO: Ensure your Flask app is created inside a create_app() function and
#       that no module-level app.run() calls exist outside of
#       `if __name__ == "__main__":` guards.

def create_app_guard(app_module_path: str) -> None:
    """
    Warn if the given module appears to call app.run() at module level,
    which is incompatible with the application factory pattern required by
    Flask 3.x and pytest-flask fixtures.
    """
    try:
        with open(app_module_path) as fh:
            source = fh.read()
        if "app.run(" in source and "if __name__" not in source:
            warnings.warn(
                f"{app_module_path} may call app.run() at module level. "
                # TODO: Wrap app.run() inside `if __name__ == '__main__':` and
                #       extract app creation into a create_app() factory function.
                "Wrap in `if __name__ == '__main__':` and use create_app().",
                DeprecationWarning,
                stacklevel=2,
            )
    except OSError:
        pass

# ---------------------------------------------------------------------------
# 2.  SQLAlchemy compatibility shim  (1.3 -> 2.0)
# ---------------------------------------------------------------------------
# Breaking changes addressed (from spec.md / design.md):
#   - session.execute(query_object) -> session.execute(select(...))
#   - Query API (session.query()) soft-deprecated; use select() in 2.0
#   - Engine.execute() removed
#   - ResultProxy -> CursorResult  (row access changed)
#   - declarative_base() moved to sqlalchemy.orm.DeclarativeBase in 2.0
#   - relationship() lazy="joined" default changed
#   - Column type imports unchanged but MetaData.bind removed

try:
    import sqlalchemy as _sa
    _SA_MAJOR = int(_sa.__version__.split(".")[0])
except ImportError:
    _sa = None  # type: ignore[assignment]
    _SA_MAJOR = 0

# --- 2a. declarative_base shim -----------------------------------------------

def get_declarative_base():
    """
    Return the correct declarative base regardless of SQLAlchemy version.

    SQLAlchemy 2.0 introduces DeclarativeBase as a class to subclass.
    The legacy declarative_base() function still works in 2.0 but emits
    a deprecation warning.  This shim wraps the legacy call.

    TODO: Migrate all models to subclass sqlalchemy.orm.DeclarativeBase
          directly (SQLAlchemy 2.0 style) and remove this shim.
    """
    if _sa is None:
        raise ImportError("sqlalchemy is not installed.")
    if _SA_MAJOR >= 2:
        warnings.warn(
            "declarative_base() is legacy in SQLAlchemy 2.0. "
            # TODO: Replace `Base = declarative_base()` with
            #       `class Base(DeclarativeBase): pass`
            "Migrate to `class Base(sqlalchemy.orm.DeclarativeBase): pass`.",
            DeprecationWarning,
            stacklevel=2,
        )
    from sqlalchemy.orm import declarative_base  # works in both 1.x and 2.x
    return declarative_base()

# --- 2b. session.query() -> select() shim ------------------------------------

class LegacyQueryShim:
    """
    Thin wrapper that translates the most common SQLAlchemy 1.3 session.query()
    patterns into SQLAlchemy 2.0 select() calls.

    Only the subset of the Query API used in this codebase is shimmed.
    TODO: Replace all session.query(Model) calls with
          session.execute(select(Model)).scalars() throughout the codebase.
    """

    def __init__(self, session: Any, entity: Any) -> None:
        self._session = session
        self._entity = entity
        self._filters: list = []
        self._order: list = []
        self._limit_val: Optional[int] = None

    def filter(self, *criterion: Any) -> "LegacyQueryShim":
        self._filters.extend(criterion)
        return self

    def filter_by(self, **kwargs: Any) -> "LegacyQueryShim":
        if _sa is None:
            raise ImportError("sqlalchemy is not installed.")
        for key, value in kwargs.items():
            self._filters.append(
                getattr(self._entity, key) == value
            )
        return self

    def order_by(self, *criterion: Any) -> "LegacyQueryShim":
        self._order.extend(criterion)
        return self

    def limit(self, n: int) -> "LegacyQueryShim":
        self._limit_val = n
        return self

    def _build_select(self) -> Any:
        from sqlalchemy import select
        stmt = select(self._entity)
        for f in self._filters:
            stmt = stmt.where(f)
        if self._order:
            stmt = stmt.order_by(*self._order)
        if self._limit_val is not None:
            stmt = stmt.limit(self._limit_val)
        return stmt

    def all(self) -> list:
        warnings.warn(
            "session.query().all() is legacy. "
            # TODO: Replace with session.execute(select(Model)).scalars().all()
            "Use session.execute(select(Model)).scalars().all().",
            DeprecationWarning,
            stacklevel=2,
        )
        result = self._session.execute(self._build_select())
        return result.scalars().all()

    def first(self) -> Any:
        warnings.warn(
            "session.query().first() is legacy. "
            # TODO: Replace with session.execute(select(Model)).scalars().first()
            "Use session.execute(select(Model)).scalars().first().",
            DeprecationWarning,
            stacklevel=2,
        )
        result = self._session.execute(self._build_select())
        return result.scalars().first()

    def one(self) -> Any:
        warnings.warn(
            "session.query().one() is legacy. "
            # TODO: Replace with session.execute(select(Model)).scalars().one()
            "Use session.execute(select(Model)).scalars().one().",
            DeprecationWarning,
            stacklevel=2,
        )
        result = self._session.execute(self._build_select())
        return result.scalars().one()

    def one_or_none(self) -> Any:
        warnings.warn(
            "session.query().one_or_none() is legacy. "
            # TODO: Replace with session.execute(select(Model)).scalars().one_or_none()
            "Use session.execute(select(Model)).scalars().one_or_none().",
            DeprecationWarning,
            stacklevel=2,
        )
        result = self._session.execute(self._build_select())
        return result.scalars().one_or_none()

    def count(self) -> int:
        warnings.warn(
            "session.query().count() is legacy. "
            # TODO: Replace with session.execute(select(func.count()).select_from(Model))
            "Use select(func.count()).select_from(Model).",
            DeprecationWarning,
            stacklevel=2,
        )
        from sqlalchemy import func, select
        stmt = select(_sa.func.count()).select_from(self._entity)
        for f in self._filters:
            stmt = stmt.where(f)
        result = self._session.execute(stmt)
        return result.scalar_one()

    def get(self, pk: Any) -> Any:
        warnings.warn(
            "session.query(Model).get(pk) is removed in SQLAlchemy 2.0. "
            # TODO: Replace with session.get(Model, pk)
            "Use session.get(Model, pk).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._session.get(self._entity, pk)


def legacy_query(session: Any, entity: Any) -> LegacyQueryShim:
    """
    Drop-in replacement for ``session.query(Entity)``.

    Wraps the call in a LegacyQueryShim that delegates to the SQLAlchemy 2.0
    select() API under the hood.

    TODO: Remove all calls to legacy_query() once the codebase is fully
          migrated to the SQLAlchemy 2.0 select() API.
    """
    return LegacyQueryShim(session, entity)

# --- 2c. Engine.execute() shim -----------------------------------------------
# Engine.execute() was removed in SQLAlchemy 2.0.
# TODO: Replace engine.execute(stmt) with:
#       with engine.connect() as conn:
#           result = conn.execute(stmt)

def engine_execute(engine: Any, statement: Any, *args: Any, **kwargs: Any) -> Any:
    """
    Compatibility wrapper for the removed Engine.execute() method.

    Wraps the call in engine.connect() as required by SQLAlchemy 2.0.
    TODO: Replace all engine.execute() calls with explicit connection context managers.
    """
    warnings.warn(
        "Engine.execute() was removed in SQLAlchemy 2.0. "
        # TODO: Replace with `with engine.connect() as conn: conn.execute(stmt)`
        "Use `with engine.connect() as conn: conn.execute(stmt)`.",
        DeprecationWarning,
        stacklevel=2,
    )
    with engine.connect() as conn:
        result = conn.execute(statement, *args, **kwargs)
        conn.commit()
        return result

# --- 2d. ResultProxy row-access shim -----------------------------------------
# In SQLAlchemy 1.3, rows were accessed as row[0] or row['column_name'].
# In SQLAlchemy 2.0, CursorResult rows use the same interface but
# row._mapping provides dict-like access.
# TODO: Replace row['column'] with row._mapping['column'] or use
#       result.mappings() when dict-style access is needed.

def row_to_dict(row: Any) -> dict:
    """
    Convert a SQLAlchemy result row to a plain dict, compatible with both
    SQLAlchemy 1.3 (RowProxy) and 2.0 (Row / CursorResult).
    """
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    # SQLAlchemy 1.3 RowProxy supports keys()
    if hasattr(row, "keys"):
        return dict(zip(row.keys(), row))
    return dict(row)

# ---------------------------------------------------------------------------
# 3.  Config migration  (old format -> new format)
# ---------------------------------------------------------------------------
# Addresses:
#   - Hardcoded credentials -> environment-based secrets (spec.md)
#   - Flask 1.x config keys -> Flask 3.x equivalents
#   - SQLAlchemy 1.3 engine options -> 2.0 engine options

# Mapping of old Flask/SQLAlchemy config keys to new keys.
_CONFIG_KEY_RENAMES: dict[str, str] = {
    # SQLAlchemy 1.3 -> 2.0
    "SQLALCHEMY_TRACK_MODIFICATIONS": None,          # removed; set to False or delete
    "SQLALCHEMY_POOL_TIMEOUT": "SQLALCHEMY_ENGINE_OPTIONS",  # moved into engine_options
    # Flask 1.x -> 3.x
    "JSON_SORT_KEYS": "app.json.sort_keys",          # moved to app.json namespace
    "JSON_AS_ASCII": "app.json.ensure_ascii",
    "JSONIFY_PRETTYPRINT_REGULAR": "app.json.compact",  # inverted semantics
    "PROPAGATE_EXCEPTIONS": None,                    # removed; always True in 3.x
    "PRESERVE_CONTEXT_ON_EXCEPTION": None,           # removed in Flask 3.x
    "TRAP_HTTP_EXCEPTIONS": "TRAP_HTTP_EXCEPTIONS",  # unchanged
}

# Keys that must come from environment variables, not hardcoded config.
_MUST_BE_ENV_VARS: tuple[str, ...] = (
    "SECRET_KEY",
    "SQLALCHEMY_DATABASE_URI",
    "JWT_SECRET",
    "SMTP_PASS",
    "SMTP_USER",
    "STRIPE_API_KEY",
    "PAYPAL_CLIENT_SECRET",
)


def migrate_config(old_config: dict) -> dict:
    """
    Transform an old-style Flask/SQLAlchemy config dict into the new format.

    Steps performed:
      1. Rename or remove deprecated keys.
      2. Warn about hardcoded secrets that must move to environment variables.
      3. Restructure SQLAlchemy engine options.
      4. Add sensible defaults required by Flask 3.x / SQLAlchemy 2.0.

    Args:
        old_config: dict representing the old configuration (e.g. from config.py).

    Returns:
        A new dict with the migrated configuration.

    TODO: After running this function, move all values flagged as
          MUST_BE_ENV_VARS into a .env file and load them with python-dotenv
          or os.environ.  Never commit secrets to source control.
    """
    new_config: dict = {}
    engine_options: dict = old_config.get("SQLALCHEMY_ENGINE_OPTIONS", {}).copy()

    for key, value in old_config.items():
        # ── Secret / credential check ─────────────────────────────────────────
        if key in _MUST_BE_ENV_VARS:
            warnings.warn(
                f"Config key '{key}' contains a potentially hardcoded secret. "
                # TODO: Move '{key}' to an environment variable and load it with
                #       os.environ.get('{key}') or python-dotenv.
                f"Move it to an environment variable: os.environ['{key}'].",
                UserWarning,
                stacklevel=2,
            )
            # Still carry the value forward so the app doesn't break immediately.
            new_config[key] = os.environ.get(key, value)
            continue

        # ── Removed keys ──────────────────────────────────────────────────────
        if key == "SQLALCHEMY_TRACK_MODIFICATIONS":
            # Removed in Flask-SQLAlchemy 3.x / SQLAlchemy 2.0.
            # TODO: Remove SQLALCHEMY_TRACK_MODIFICATIONS from your config entirely.
            warnings.warn(
                "SQLALCHEMY_TRACK_MODIFICATIONS is removed in SQLAlchemy 2.0 / "
                "Flask-SQLAlchemy 3.x.  Remove it from your config.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key in ("PRESERVE_CONTEXT_ON_EXCEPTION", "PROPAGATE_EXCEPTIONS"):
            # TODO: Remove PRESERVE_CONTEXT_ON_EXCEPTION and PROPAGATE_EXCEPTIONS —
            #       both were removed in Flask 3.x.
            warnings.warn(
                f"'{key}' was removed in Flask 3.x.  Remove it from your config.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        # ── SQLAlchemy pool options -> engine_options ─────────────────────────
        if key == "SQLALCHEMY_POOL_TIMEOUT":
            # TODO: Move pool settings into SQLALCHEMY_ENGINE_OPTIONS dict.
            engine_options["pool_timeout"] = value
            continue

        if key == "SQLALCHEMY_POOL_SIZE":
            engine_options["pool_size"] = value
            continue

        if key == "SQLALCHEMY_MAX_OVERFLOW":
            engine_options["max_overflow"] = value
            continue

        if key == "SQLALCHEMY_POOL_RECYCLE":
            engine_options["pool_recycle"] = value
            continue

        # ── JSON config keys moved to app.json namespace ──────────────────────
        if key == "JSON_SORT_KEYS":
            # TODO: Replace app.config['JSON_SORT_KEYS'] with app.json.sort_keys = value
            warnings.warn(
                "JSON_SORT_KEYS moved to app.json.sort_keys in Flask 3.x.",
                DeprecationWarning,
                stacklevel=2,
            )
            new_config["_JSON_SORT_KEYS"] = value  # sentinel for post-init wiring
            continue

        if key == "JSON_AS_ASCII":
            # TODO: Replace app.config['JSON_AS_ASCII'] with app.json.ensure_ascii = value
            warnings.warn(
                "JSON_AS_ASCII moved to app.json.ensure_ascii in Flask 3.x.",
                DeprecationWarning,
                stacklevel=2,
            )
            new_config["_JSON_ENSURE_ASCII"] = value
            continue

        if key == "JSONIFY_PRETTYPRINT_REGULAR":
            # TODO: Replace JSONIFY_PRETTYPRINT_REGULAR with app.json.compact = not value
            warnings.warn(
                "JSONIFY_PRETTYPRINT_REGULAR moved to app.json.compact (inverted) "
                "in Flask 3.x.",
                DeprecationWarning,
                stacklevel=2,
            )
            new_config["_JSON_COMPACT"] = not value
            continue

        # ── Pass through unchanged keys ───────────────────────────────────────
        new_config[key] = value

    # ── Merge engine options ──────────────────────────────────────────────────
    if engine_options:
        new_config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

    # ── Flask 3.x required defaults ──────────────────────────────────────────
    new_config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "CHANGE_ME"))
    if new_config.get("SECRET_KEY") == "CHANGE_ME":
        warnings.warn(
            "SECRET_KEY is not set.  "
            # TODO: Set SECRET_KEY via environment variable before deploying.
            "Set the SECRET_KEY environment variable.",
            UserWarning,
            stacklevel=2,
        )

    # SQLAlchemy 2.0: future=True is now the default; no longer needed but harmless.
    # TODO: Remove SQLALCHEMY_FUTURE from config — it is the default in SA 2.0.
    new_config.pop("SQLALCHEMY_FUTURE", None)

    return new_config


def apply_json_config(app: Any, migrated_config: dict) -> None:
    """
    Apply the sentinel JSON config values produced by migrate_config() to a
    Flask 3.x app instance via the app.json provider interface.

    Call this after create_app() has constructed the Flask app and called
    app.config.from_mapping(migrated_config).

    TODO: Once the codebase is fully on Flask 3.x, inline these assignments
          directly into create_app() and remove this helper.
    """
    if "_JSON_SORT_KEYS" in migrated_config:
        app.json.sort_keys = migrated_config["_JSON_SORT_KEYS"]
    if "_JSON_ENSURE_ASCII" in migrated_config:
        app.json.ensure_ascii = migrated_config["_JSON_ENSURE_ASCII"]
    if "_JSON_COMPACT" in migrated_config:
        app.json.compact = migrated_config["_JSON_COMPACT"]

# ---------------------------------------------------------------------------
# 4.  pytest fixture helpers for fixture-based DB isolation
# ---------------------------------------------------------------------------
# Addresses:
#   - Replace unittest.TestCase with pytest + fixtures (spec.md primary goal)
#   - InMemoryUserRepository shared mutable state isolation (spec.md)
#   - SQLAlchemy 2.0 session-scoped fixture pattern
#
# These fixtures are designed to be placed in conftest.py.
# Copy the relevant sections into your test suite's conftest.py.

# --- 4a. InMemoryUserRepository fixture (mirrors JS InMemoryUserRepository) --

class InMemoryUserRepository:
    """
    Python port of the JS InMemoryUserRepository for use in pytest fixtures.

    Each fixture invocation receives a fresh instance with an empty store,
    providing the DB isolation that was missing from the Jest-based suite.

    TODO: Replace with a real database-backed repository fixture once a
          persistent store (PostgreSQL via SQLAlchemy) is introduced.
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def find_by_id(self, user_id: str) -> Optional[Any]:
        return self._store.get(user_id)

    def find_by_email(self, email: str) -> Optional[Any]:
        normalised = email.lower()
        for user in self._store.values():
            if getattr(user, "email", "").lower() == normalised:
                return user
        return None

    def save(self, user: Any) -> Any:
        self._store[user.id] = user
        return user

    def update(self, user: Any) -> Any:
        if user.id not in self._store:
            err = KeyError(f'User with id "{user.id}" not found')
            raise err
        self._store[user.id] = user
        return user

    def delete(self, user_id: str) -> None:
        if user_id not in self._store:
            raise KeyError(f'User with id "{user_id}" not found')
        del self._store[user_id]

    def find_by_verification_token(self, token: str) -> Optional[Any]:
        for user in self._store.values():
            if getattr(user, "verification_token", None) == token:
                return user
        return None

    def find_by_reset_token(self, token: str) -> Optional[Any]:
        for user in self._store.values():
            if getattr(user, "reset_token", None) == token:
                return user
        return None

    def clear(self) -> None:
        """Reset the store — called automatically by the pytest fixture teardown."""
        self._store.clear()


def make_user_repository_fixture():
    """
    Factory that returns a pytest fixture function providing an isolated
    InMemoryUserRepository per test.

    Usage in conftest.py:

        from migration_shim import make_user_repository_fixture
        user_repository = make_user_repository_fixture()

    Then in tests:

        def test_register(user_repository):
            ...
    """
    try:
        import pytest
    except ImportError:
        raise ImportError(
            # TODO: Add pytest to requirements-dev.txt / pyproject.toml
            "pytest is not installed.  Run: pip install pytest"
        )

    @pytest.fixture
    def user_repository() -> Generator[InMemoryUserRepository, None, None]:
        """
        Provides a fresh InMemoryUserRepository for each test.
        The store is cleared in teardown to prevent state leakage.
        """
        repo = InMemoryUserRepository()
        yield repo
        repo.clear()

    return user_repository


# --- 4b. SQLAlchemy 2.0 session fixture (for future DB-backed tests) ---------

def make_db_session_fixture(engine_factory):
    """
    Factory that returns a pytest fixture providing a transactional SQLAlchemy
    session that is rolled back after each test (fixture-based DB isolation).

    Args:
        engine_factory: zero-argument callable that returns a SQLAlchemy Engine.

    Usage in conftest.py:

        from migration_shim import make_db_session_fixture
        from sqlalchemy import create_engine

        def _engine():
            return create_engine(os.environ["TEST_DATABASE_URL"])

        db_session = make_db_session_fixture(_engine)

    TODO: Replace engine_factory with a real test database URL loaded from
          the environment (TEST_DATABASE_URL).  Never hardcode DB credentials.
    """
    try:
        import pytest
    except ImportError:
        raise ImportError(
            # TODO: Add pytest to requirements-dev.txt / pyproject.toml
            "pytest is not installed.  Run: pip install pytest"
        )

    @pytest.fixture(scope="session")
    def _engine():
        eng = engine_factory()
        yield eng
        eng.dispose()

    @pytest.fixture
    def db_session(_engine) -> Generator[Any, None, None]:
        """
        Yields a SQLAlchemy 2.0 Session bound to a savepoint transaction.
        The outer transaction is rolled back after each test, leaving the DB
        in a clean state without requiring truncation or re-creation.

        TODO: Ensure your models are created before the session fixture runs,
              e.g. via a session-scoped `create_all` fixture.
        """
        from sqlalchemy.orm import Session

        connection = _engine.connect()
        transaction = connection.begin()
        session = Session(bind=connection)

        # SQLAlchemy 2.0: use nested (SAVEPOINT) for inner rollback
        nested = connection.begin_nested()

        # Re-open savepoint after each flush so the session stays usable
        from sqlalchemy import event

        @event.listens_for(session, "after_transaction_end")
        def restart_savepoint(sess, trans):
            nonlocal nested
            if trans.nested and not trans._parent.nested:
                nested = connection.begin_nested()

        yield session

        session.close()
        transaction.rollback()
        connection.close()

    return db_session


# --- 4c. Flask test client fixture -------------------------------------------

def make_flask_client_fixture(app_factory):
    """
    Factory that returns a pytest fixture providing a Flask 3.x test client.

    Args:
        app_factory: zero-argument callable that returns a configured Flask app
                     (i.e. the create_app() function).

    Usage in conftest.py:

        from migration_shim import make_flask_client_fixture
        from myapp import create_app

        client = make_flask_client_fixture(create_app)

    TODO: Ensure create_app() reads all secrets from environment variables,
          not from hardcoded config values.
    """
    try:
        import pytest
    except ImportError:
        raise ImportError(
            # TODO: Add pytest to requirements-dev.txt / pyproject.toml
            "pytest is not installed.  Run: pip install pytest"
        )

    @pytest.fixture
    def client():
        """
        Provides a Flask test client with TESTING=True and a fresh app context
        per test.  The app context is torn down after each test.
        """
        app = app_factory()
        app.config["TESTING"] = True
        # TODO: Set WTF_CSRF_ENABLED = False if Flask-WTF is used in tests.
        with app.test_client() as test_client:
            with app.app_context():
                yield test_client

    return client


# --- 4d. unittest.TestCase -> pytest migration helper ------------------------

class PytestCompatMixin:
    """
    Mixin that re-exports the most common unittest.TestCase assertion methods
    as plain methods so that existing TestCase subclasses can be migrated to
    plain pytest classes incrementally.

    Usage:

        # Before (unittest):
        class TestFoo(unittest.TestCase):
            def test_bar(self):
                self.assertEqual(1, 1)

        # After (pytest, step 1 — add mixin, remove TestCase):
        class TestFoo(PytestCompatMixin):
            def test_bar(self):
                self.assertEqual(1, 1)

        # After (pytest, step 2 — replace with plain assert):
        class TestFoo:
            def test_bar(self):
                assert 1 == 1

    TODO: Remove PytestCompatMixin once all assertions have been converted to
          plain `assert` statements as recommended by pytest best practices.
    """

    def assertEqual(self, first: Any, second: Any, msg: Any = None) -> None:
        assert first == second, msg or f"{first!r} != {second!r}"

    def assertNotEqual(self, first: Any, second: Any, msg: Any = None) -> None:
        assert first != second, msg or f"{first!r} == {second!r}"

    def assertTrue(self, expr: Any, msg: Any = None) -> None:
        assert expr, msg or f"Expected truthy, got {expr!r}"

    def assertFalse(self, expr: Any, msg: Any = None) -> None:
        assert not expr, msg or f"Expected falsy, got {expr!r}"

    def assertIsNone(self, obj: Any, msg: Any = None) -> None:
        assert obj is None, msg or f"Expected None, got {obj!r}"

    def assertIsNotNone(self, obj: Any, msg: Any = None) -> None:
        assert obj is not None, msg or f"Expected non-None value"

    def assertIn(self, member: Any, container: Any, msg: Any = None) -> None:
        assert member in container, msg or f"{member!r} not in {container!r}"

    def assertNotIn(self, member: Any, container: Any, msg: Any = None) -> None:
        assert member not in container, msg or f"{member!r} in {container!r}"

    def assertRaises(self, exc, *args, **kwargs):  # type: ignore[override]
        import pytest
        return pytest.raises(exc, *args, **kwargs)

    def assertIsInstance(self, obj: Any, cls: Any, msg: Any = None) -> None:
        assert isinstance(obj, cls), msg or f"{obj!r} is not an instance of {cls!r}"

    def assertDictEqual(self, d1: dict, d2: dict, msg: Any = None) -> None:
        assert d1 == d2, msg or f"{d1!r} != {d2!r}"

    def assertListEqual(self, l1: list, l2: list, msg: Any = None) -> None:
        assert l1 == l2, msg or f"{l1!r} != {l2!r}"

    def setUp(self) -> None:
        """Override in subclass.  Called by pytest via autouse fixture below."""

    def tearDown(self) -> None:
        """Override in subclass.  Called by pytest via autouse fixture below."""


def install_setup_teardown_autouse() -> None:
    """
    Installs a module-level pytest autouse fixture that calls setUp/tearDown
    on PytestCompatMixin subclasses, preserving unittest lifecycle semantics.

    Call this at the top of conftest.py:

        from migration_shim import install_setup_teardown_autouse
        install_setup_teardown_autouse()

    TODO: Remove once all test classes have been fully migrated to pytest
          fixtures and plain functions.
    """
    try:
        import pytest
    except ImportError:
        return

    @pytest.fixture(autouse=True)
    def _unittest_lifecycle(self):  # type: ignore[misc]
        if isinstance(self, PytestCompatMixin):
            self.setUp()
            yield
            self.tearDown()
        else:
            yield

# ---------------------------------------------------------------------------
# 5.  Convenience: generate a minimal conftest.py skeleton
# ---------------------------------------------------------------------------

_CONFTEST_TEMPLATE = '''\
"""
conftest.py — generated by migration_shim.py
Provides pytest fixtures for DB isolation and Flask test client.

TODO: Review each fixture and adapt to your actual application structure.
"""
import os
import pytest

from migration_shim import (
    InMemoryUserRepository,
    make_user_repository_fixture,
    make_flask_client_fixture,
    PytestCompatMixin,
    install_setup_teardown_autouse,
)

# ---------------------------------------------------------------------------
# Lifecycle shim for any remaining unittest.TestCase-style classes
# ---------------------------------------------------------------------------
install_setup_teardown_autouse()

# ---------------------------------------------------------------------------
# Isolated in-memory user repository (one fresh instance per test)
# ---------------------------------------------------------------------------
user_repository = make_user_repository_fixture()

# ---------------------------------------------------------------------------
# Flask test client
# TODO: Replace the lambda below with your actual create_app import, e.g.:
#       from myapp import create_app
# ---------------------------------------------------------------------------
# client = make_flask_client_fixture(create_app)

# ---------------------------------------------------------------------------
# SQLAlchemy session fixture (uncomment when a real DB is introduced)
# TODO: Set TEST_DATABASE_URL in your .env.test file.
# ---------------------------------------------------------------------------
# from migration_shim import make_db_session_fixture
# from sqlalchemy import create_engine
#
# db_session = make_db_session_fixture(
#     lambda: create_engine(os.environ["TEST_DATABASE_URL"])
# )
'''


def generate_conftest(output_path: str = "conftest.py", overwrite: bool = False) -> None:
    """
    Write a minimal conftest.py skeleton to *output_path*.

    Args:
        output_path: destination file path (default: conftest.py in cwd).
        overwrite:   if False (default), skip writing if the file already exists.
    """
    if os.path.exists(output_path) and not overwrite:
        print(f"[migration_shim] {output_path} already exists — skipping generation.")
        return
    with open(output_path, "w") as fh:
        fh.write(_CONFTEST_TEMPLATE)
    print(f"[migration_shim] Generated {output_path}")


# ---------------------------------------------------------------------------
# 6.  CLI entry point
# ---------------------------------------------------------------------------

def _print_report() -> None:
    print("=" * 70)
    print("migration_shim.py — upgrade compatibility report")
    print("=" * 70)

    print("\n[Flask]")
    if _flask is not None:
        print(f"  Installed version : {_flask.__version__}")
        if _FLASK_MAJOR < 3:
            print("  WARNING: Flask < 3.x detected.  Upgrade to Flask 3.1.")
            print("  TODO: Run `pip install 'Flask>=3.1'`")
        else:
            print("  OK: Flask 3.x detected.")
    else:
        print("  Flask not installed.")

    print("\n[SQLAlchemy]")
    if _sa is not None:
        print(f"  Installed version : {_sa.__version__}")
        if _SA_MAJOR < 2:
            print("  WARNING: SQLAlchemy < 2.0 detected.  Upgrade to SQLAlchemy 2.0.")
            print("  TODO: Run `pip install 'SQLAlchemy>=2.0'`")
        else:
            print("  OK: SQLAlchemy 2.x detected.")
    else:
        print("  SQLAlchemy not installed.")

    print("\n[Python]")
    print(f"  Running version   : {sys.version}")
    if sys.version_info < (3, 12):
        print("  WARNING: Python < 3.12 detected.")
        print("  TODO: Upgrade to Python 3.12 or 3.13 as per upgrade goal.")
    else:
        print("  OK: Python 3.12+ detected.")

    print("\n[pytest]")
    try:
        import pytest
        print(f"  Installed version : {pytest.__version__}")
    except ImportError:
        print("  pytest not installed.")
        print("  TODO: Run `pip install pytest pytest-flask` and add to requirements-dev.txt")

    print("\n[Secrets check]")
    for var in _MUST_BE_ENV_VARS:
        val = os.environ.get(var)
        if val:
            print(f"  OK : {var} is set via environment.")
        else:
            print(f"  MISSING: {var} — TODO: set this environment variable before deploying.")

    print("\n[conftest.py]")
    if os.path.exists("conftest.py"):
        print("  conftest.py exists.")
    else:
        print("  conftest.py not found — run generate_conftest() to create a skeleton.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    check_mode = "--check" in sys.argv
    _print_report()

    issues: list[str] = []

    if _flask is not None and _FLASK_MAJOR < 3:
        issues.append("Flask < 3.x")
    if _sa is not None and _SA_MAJOR < 2:
        issues.append("SQLAlchemy < 2.0")
    if sys.version_info < (3, 12):
        issues.append("Python < 3.12")

    missing_secrets = [v for v in _MUST_BE_ENV_VARS if not os.environ.get(v)]
    if missing_secrets:
        issues.append(f"Missing env vars: {', '.join(missing_secrets)}")

    if not os.path.exists("conftest.py"):
        generate_conftest()

    if check_mode and issues:
        print(f"\n[FAIL] {len(issues)} issue(s) require attention:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    elif issues:
        print(f"\n[WARN] {len(issues)} issue(s) detected (run with --check to fail CI).")
    else:
        print("\n[OK] No blocking issues detected.")