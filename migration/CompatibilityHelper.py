# migration_shim.py
# Compatibility shim for Flask 1.x → 3.1 and SQLAlchemy 1.3 → 2.0 upgrade.
# Addresses session lifecycle fixes, deprecated API replacements, renamed
# packages/classes, and config format changes.
#
# Usage:
#   1. Import this module early in your application entry point (before other
#      app imports) to activate the compatibility shims.
#   2. Run migrate_config(old_config) to transform legacy config dicts.
#   3. Search for TODO comments in this file for items requiring manual review.

import warnings
import functools
import logging
import os
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Python version guard
# ---------------------------------------------------------------------------
import sys

if sys.version_info < (3, 8):
    raise RuntimeError(
        "This shim requires Python 3.8 or newer. "
        "Target runtime is Python 3.12/3.13 per upgrade spec."
    )

# ---------------------------------------------------------------------------
# SQLAlchemy 1.3 → 2.0 compatibility shim
# ---------------------------------------------------------------------------
# Breaking changes addressed:
#   - Session.execute() now requires text() wrapper for raw SQL strings.
#   - Query API (session.query()) is legacy; select() / scalars() is canonical.
#   - autocommit=True on Session is removed in 2.0.
#   - Session.get() replaces Query.get() for primary-key lookup.
#   - scoped_session behaviour is unchanged but must be removed via
#     session.remove() not session.close() at request teardown.
#   - Connection.execute(string) removed; use text() explicitly.
#   - engine.execute() removed entirely.
# ---------------------------------------------------------------------------

try:
    import sqlalchemy
    from sqlalchemy import text, select
    from sqlalchemy.orm import Session, scoped_session, sessionmaker
    from sqlalchemy.exc import SQLAlchemyError

    _SA_VERSION = tuple(int(x) for x in sqlalchemy.__version__.split(".")[:2])
    _SA_20 = _SA_VERSION >= (2, 0)

    if not _SA_20:
        warnings.warn(
            "SQLAlchemy < 2.0 detected. This shim provides forward-compatible "
            "wrappers but you MUST upgrade to SQLAlchemy 2.0 for production. "
            "See spec.md: 'Upgrade SQLAlchemy from 1.3 (EOL) to 2.0'.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ------------------------------------------------------------------
    # Session factory helper — replaces ad-hoc Session() construction
    # ------------------------------------------------------------------

    def make_session_factory(engine, **kwargs):
        """
        Create a sessionmaker bound to *engine* with 2.0-safe defaults.

        Replaces direct ``Session(bind=engine)`` calls that were common in
        SQLAlchemy 1.3 and are removed in 2.0.

        Args:
            engine: A SQLAlchemy Engine instance.
            **kwargs: Additional keyword arguments forwarded to sessionmaker.

        Returns:
            A sessionmaker factory.
        """
        # TODO (SQLAlchemy 2.0 breaking change): 'autocommit' parameter is
        # removed from Session in 2.0. If your legacy code passes
        # autocommit=True, remove it and manage transactions explicitly with
        # session.begin() / session.commit().
        kwargs.pop("autocommit", None)

        # TODO (SQLAlchemy 2.0 breaking change): 'bind' keyword on Session
        # constructor is removed. Pass engine to sessionmaker instead.
        kwargs.pop("bind", None)

        return sessionmaker(bind=engine, expire_on_commit=False, **kwargs)

    # ------------------------------------------------------------------
    # Scoped session lifecycle manager (Flask request scope)
    # ------------------------------------------------------------------

    def make_scoped_session(engine, **kwargs):
        """
        Create a request-scoped session registry.

        In Flask 3.x use this with ``teardown_appcontext`` to ensure the
        session is removed (not just closed) at the end of every request,
        returning the connection to the HikariCP / SQLAlchemy pool.

        Example::

            Session = make_scoped_session(engine)

            @app.teardown_appcontext
            def shutdown_session(exception=None):
                Session.remove()   # <-- must be remove(), not close()

        Returns:
            A scoped_session proxy.
        """
        factory = make_session_factory(engine, **kwargs)
        return scoped_session(factory)

    # ------------------------------------------------------------------
    # Context manager for explicit transaction boundaries
    # ------------------------------------------------------------------

    @contextmanager
    def managed_session(session_factory):
        """
        Context manager that provides a session with explicit commit/rollback.

        Addresses the spec requirement:
        "PaymentApplicationService performs multi-step persistence operations
        (save → gateway call → update) with no explicit transaction boundary,
        meaning partial failures can leave the database in an inconsistent
        state and sessions may not be released."

        Usage::

            with managed_session(SessionFactory) as session:
                session.add(entity)
                # ... gateway call ...
                session.add(updated_entity)
            # auto-committed or rolled back; session always closed.

        Args:
            session_factory: A sessionmaker or scoped_session instance.

        Yields:
            An active SQLAlchemy Session.
        """
        session = session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Database error — transaction rolled back: %s", exc)
            raise
        except Exception as exc:
            session.rollback()
            logger.error("Unexpected error — transaction rolled back: %s", exc)
            raise
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Legacy Query.get() → Session.get() shim
    # ------------------------------------------------------------------

    def session_get(session, model_class, primary_key):
        """
        Portable primary-key lookup compatible with both SA 1.3 and 2.0.

        In SQLAlchemy 1.3 the idiom was::

            session.query(MyModel).get(pk)

        In SQLAlchemy 2.0 ``Query.get()`` is removed; use::

            session.get(MyModel, pk)

        Args:
            session: Active SQLAlchemy Session.
            model_class: The mapped ORM class.
            primary_key: The primary key value (scalar or tuple).

        Returns:
            The mapped instance or None.
        """
        if _SA_20:
            return session.get(model_class, primary_key)
        else:
            # TODO (SQLAlchemy 2.0 breaking change): session.query().get() is
            # removed in 2.0. Replace all call sites with session.get(Model, pk)
            # once you have fully migrated to SQLAlchemy 2.0.
            return session.query(model_class).get(primary_key)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Legacy engine.execute() shim (removed in SA 2.0)
    # ------------------------------------------------------------------

    def engine_execute(engine, statement, *args, **kwargs):
        """
        Shim for the removed ``engine.execute()`` API.

        ``engine.execute()`` was deprecated in SQLAlchemy 1.4 and removed in
        2.0. This wrapper uses an explicit connection context instead.

        Args:
            engine: A SQLAlchemy Engine.
            statement: A string SQL statement or a SQLAlchemy Executable.
            *args: Positional parameters forwarded to execute().
            **kwargs: Keyword parameters forwarded to execute().

        Returns:
            A CursorResult.
        """
        # TODO (SQLAlchemy 2.0 breaking change): engine.execute() is removed.
        # All call sites must be migrated to use an explicit connection:
        #   with engine.connect() as conn:
        #       result = conn.execute(text("SELECT ..."), {"param": value})
        if isinstance(statement, str):
            statement = text(statement)
        with engine.connect() as conn:
            result = conn.execute(statement, *args, **kwargs)
            conn.commit()
            return result

    # ------------------------------------------------------------------
    # Legacy session.execute(string) shim
    # ------------------------------------------------------------------

    def session_execute(session, statement, params=None):
        """
        Shim for raw-string ``session.execute()`` calls.

        In SQLAlchemy 1.3 you could pass a plain string::

            session.execute("SELECT * FROM users WHERE id = :id", {"id": 1})

        In SQLAlchemy 2.0 the string must be wrapped in ``text()``::

            session.execute(text("SELECT * FROM users WHERE id = :id"), {"id": 1})

        Args:
            session: Active SQLAlchemy Session.
            statement: A string or SQLAlchemy Executable.
            params: Optional dict of bind parameters.

        Returns:
            A CursorResult.
        """
        # TODO (SQLAlchemy 2.0 breaking change): Wrap all raw SQL strings
        # passed to session.execute() in sqlalchemy.text(). This shim does it
        # automatically but every call site should be updated explicitly.
        if isinstance(statement, str):
            statement = text(statement)
        if params is not None:
            return session.execute(statement, params)
        return session.execute(statement)

    # ------------------------------------------------------------------
    # Legacy Query API → 2.0 select() shim helpers
    # ------------------------------------------------------------------

    def legacy_query_all(session, model_class, **filter_kwargs):
        """
        Portable replacement for ``session.query(Model).filter_by(**kw).all()``.

        Uses the 2.0 ``select()`` API when available, falls back to the
        legacy Query API on SQLAlchemy 1.3.

        Args:
            session: Active SQLAlchemy Session.
            model_class: The mapped ORM class.
            **filter_kwargs: Column equality filters.

        Returns:
            A list of mapped instances.
        """
        # TODO (SQLAlchemy 2.0 breaking change): The legacy Query API
        # (session.query()) is in "legacy" mode in 2.0 and will be removed in
        # a future version. Migrate all query call sites to use select():
        #   stmt = select(MyModel).where(MyModel.col == value)
        #   results = session.scalars(stmt).all()
        if _SA_20:
            stmt = select(model_class)
            for attr, value in filter_kwargs.items():
                stmt = stmt.where(getattr(model_class, attr) == value)
            return list(session.scalars(stmt).all())
        else:
            return session.query(model_class).filter_by(**filter_kwargs).all()  # type: ignore[attr-defined]

    def legacy_query_first(session, model_class, **filter_kwargs):
        """
        Portable replacement for ``session.query(Model).filter_by(**kw).first()``.

        Args:
            session: Active SQLAlchemy Session.
            model_class: The mapped ORM class.
            **filter_kwargs: Column equality filters.

        Returns:
            The first matching instance or None.
        """
        # TODO (SQLAlchemy 2.0 breaking change): Migrate to:
        #   stmt = select(MyModel).where(...).limit(1)
        #   result = session.scalars(stmt).first()
        if _SA_20:
            stmt = select(model_class)
            for attr, value in filter_kwargs.items():
                stmt = stmt.where(getattr(model_class, attr) == value)
            return session.scalars(stmt).first()
        else:
            return session.query(model_class).filter_by(**filter_kwargs).first()  # type: ignore[attr-defined]

except ImportError:
    logger.warning(
        "SQLAlchemy is not installed. SQLAlchemy shims are not active. "
        "Install sqlalchemy>=2.0 as required by the upgrade spec."
    )

# ---------------------------------------------------------------------------
# Flask 1.x → 3.1 compatibility shim
# ---------------------------------------------------------------------------
# Breaking changes addressed:
#   - flask.json.provider replaces flask.json module-level helpers in 3.x.
#   - before_first_request decorator is removed in Flask 2.3+.
#   - flask.escape() moved to markupsafe.escape().
#   - flask.Markup moved to markupsafe.Markup.
#   - Flask.run() debug pin is removed; use FLASK_DEBUG env var.
#   - Application factory pattern is now required (no module-level app).
#   - PROPAGATE_EXCEPTIONS config key behaviour changed.
#   - flask.signals (blinker) is now a hard dependency in Flask 3.x.
# ---------------------------------------------------------------------------

try:
    import flask
    from flask import Flask

    _FLASK_VERSION = tuple(int(x) for x in flask.__version__.split(".")[:2])
    _FLASK_3 = _FLASK_VERSION >= (3, 0)

    if _FLASK_VERSION < (2, 0):
        warnings.warn(
            "Flask < 2.0 detected. This shim provides forward-compatible "
            "wrappers but you MUST upgrade to Flask 3.1 for production. "
            "See spec.md: 'Upgrade Flask from 1.x (EOL) to 3.x'.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ------------------------------------------------------------------
    # flask.escape / flask.Markup → markupsafe shim
    # ------------------------------------------------------------------

    try:
        from markupsafe import escape as markup_escape
        from markupsafe import Markup
    except ImportError:
        # Fallback for environments where markupsafe is not yet installed.
        # TODO (Flask 3.x breaking change): markupsafe is a required dependency
        # of Flask 3.x. Add 'markupsafe>=2.1' to requirements.txt / setup.cfg.
        from flask import escape as markup_escape  # type: ignore[attr-defined,no-redef]
        from flask import Markup  # type: ignore[attr-defined,no-redef]

    # Re-export under the old flask.* names for call sites that have not yet
    # been migrated.
    escape = markup_escape

    # ------------------------------------------------------------------
    # before_first_request shim
    # ------------------------------------------------------------------

    def register_before_first_request(app, func):
        """
        Portable replacement for the removed ``@app.before_first_request``
        decorator (removed in Flask 2.3, absent in Flask 3.x).

        Registers *func* to run once before the first request is handled,
        using an ``app.before_request`` guard instead.

        Args:
            app: A Flask application instance.
            func: A zero-argument callable to invoke before the first request.

        Example::

            def init_db():
                db.create_all()

            register_before_first_request(app, init_db)
        """
        # TODO (Flask 2.3+ breaking change): @app.before_first_request is
        # removed. Replace all usages with this helper or move initialisation
        # into the application factory (create_app). See Flask 2.3 changelog.
        _called = {"done": False}

        @app.before_request
        def _wrapper():
            if not _called["done"]:
                _called["done"] = True
                func()

    # ------------------------------------------------------------------
    # Application factory helper
    # ------------------------------------------------------------------

    def create_app_with_session(config: dict, session_factory=None) -> "Flask":
        """
        Application factory that wires a SQLAlchemy scoped session into the
        Flask request lifecycle, preventing connection leaks.

        This implements the pattern required by the upgrade spec:
        - Flask 3.x application factory pattern.
        - SQLAlchemy session removed (not just closed) at teardown.
        - Environment-based configuration (no hardcoded credentials).

        Args:
            config: A dict of Flask/SQLAlchemy configuration values.
                    See ``migrate_config()`` to convert legacy config dicts.
            session_factory: An optional scoped_session instance. If None,
                             no session teardown is registered.

        Returns:
            A configured Flask application instance.
        """
        app = Flask(__name__)

        # Apply migrated config
        migrated = migrate_config(config)
        app.config.update(migrated)

        if session_factory is not None:
            # TODO (SQLAlchemy 2.0 + Flask 3.x): Ensure session_factory is
            # created via make_scoped_session(engine) from this shim so that
            # the correct 2.0-compatible sessionmaker defaults are applied.
            @app.teardown_appcontext
            def shutdown_session(exception=None):
                """
                Remove the scoped session at the end of every request context.

                Using session.remove() (not session.close()) ensures the
                connection is returned to the pool and the session registry
                entry is cleared, preventing connection leaks under load.
                """
                session_factory.remove()

        return app

    # ------------------------------------------------------------------
    # JSON helpers shim (flask.json module-level API changed in 3.x)
    # ------------------------------------------------------------------

    def flask_jsonify_safe(data):
        """
        Portable wrapper around Flask's JSON serialisation.

        In Flask 1.x/2.x ``flask.json.dumps()`` was available as a
        module-level function. In Flask 3.x JSON handling is delegated to
        the app's ``json_provider_class``. Use ``flask.json.dumps()`` inside
        an application context, or use this helper.

        Args:
            data: A JSON-serialisable Python object.

        Returns:
            A JSON string.
        """
        # TODO (Flask 3.x breaking change): flask.json module-level helpers
        # (flask.json.dumps, flask.json.loads) still exist in 3.x but are
        # routed through the app's json_provider_class. If you have a custom
        # JSON encoder subclassing flask.json.JSONEncoder, migrate it to
        # implement flask.json.provider.JSONProvider instead.
        import json as _json
        try:
            from flask import json as flask_json
            return flask_json.dumps(data)
        except RuntimeError:
            # Outside application context — fall back to stdlib json.
            return _json.dumps(data)

except ImportError:
    logger.warning(
        "Flask is not installed. Flask shims are not active. "
        "Install flask>=3.1 as required by the upgrade spec."
    )

# ---------------------------------------------------------------------------
# Config migration function
# ---------------------------------------------------------------------------
# Transforms a legacy (Flask 1.x / SQLAlchemy 1.3) config dict into the
# format expected by Flask 3.1 / SQLAlchemy 2.0.
# ---------------------------------------------------------------------------

# Mapping of old config keys → new config keys
_CONFIG_KEY_RENAMES = {
    # SQLAlchemy 1.3 → 2.0 key renames
    "SQLALCHEMY_DATABASE_URI": "SQLALCHEMY_DATABASE_URI",  # unchanged, but validated
    "SQLALCHEMY_POOL_SIZE": "SQLALCHEMY_POOL_SIZE",        # unchanged
    "SQLALCHEMY_MAX_OVERFLOW": "SQLALCHEMY_MAX_OVERFLOW",  # unchanged
    "SQLALCHEMY_POOL_TIMEOUT": "SQLALCHEMY_POOL_TIMEOUT",  # unchanged
    "SQLALCHEMY_POOL_RECYCLE": "SQLALCHEMY_POOL_RECYCLE",  # unchanged
    # Flask 1.x → 3.x key renames
    "PROPAGATE_EXCEPTIONS": "PROPAGATE_EXCEPTIONS",        # unchanged but see TODO
    "JSON_SORT_KEYS": "JSON_SORT_KEYS",                    # removed in Flask 3.x
    "JSONIFY_PRETTYPRINT_REGULAR": "JSONIFY_PRETTYPRINT_REGULAR",  # removed in 3.x
    "JSONIFY_MIMETYPE": "JSONIFY_MIMETYPE",                # removed in 3.x
}

# Config keys that are removed in Flask 3.x and must not be forwarded.
_FLASK3_REMOVED_KEYS = {
    "JSON_SORT_KEYS",
    "JSONIFY_PRETTYPRINT_REGULAR",
    "JSONIFY_MIMETYPE",
    "JSON_AS_ASCII",
    # TODO (Flask 3.x breaking change): The following keys were removed.
    # If your code reads these at runtime, migrate to the new JSON provider
    # API (flask.json.provider.JSONProvider) or remove the configuration.
}

# SQLAlchemy 1.3 engine options that map to 2.0 engine_options dict.
_SA_ENGINE_OPTION_KEYS = {
    "SQLALCHEMY_POOL_SIZE",
    "SQLALCHEMY_MAX_OVERFLOW",
    "SQLALCHEMY_POOL_TIMEOUT",
    "SQLALCHEMY_POOL_RECYCLE",
    "SQLALCHEMY_POOL_PRE_PING",
    "SQLALCHEMY_ECHO",
}


def migrate_config(old_config: dict) -> dict:
    """
    Transform a legacy Flask 1.x / SQLAlchemy 1.3 config dict into the
    format expected by Flask 3.1 / SQLAlchemy 2.0.

    Transformations applied:
    - Removes Flask 3.x-incompatible JSON config keys.
    - Warns about hardcoded DATABASE_URL / credentials.
    - Ensures SQLALCHEMY_TRACK_MODIFICATIONS is False (removed in SA 2.0
      Flask-SQLAlchemy extension; was deprecated since 1.4).
    - Adds SQLALCHEMY_ENGINE_OPTIONS with pool_pre_ping=True to detect
      stale connections and prevent pool exhaustion.
    - Replaces any autocommit session option with explicit transaction advice.
    - Promotes environment variables for secrets if hardcoded values are found.

    Args:
        old_config: The legacy configuration dictionary.

    Returns:
        A new configuration dictionary suitable for Flask 3.1 / SA 2.0.
    """
    new_config = {}

    for key, value in old_config.items():
        # Drop keys removed in Flask 3.x
        if key in _FLASK3_REMOVED_KEYS:
            warnings.warn(
                f"Config key '{key}' is removed in Flask 3.x and has been "
                f"dropped from the migrated config. "
                f"See Flask 3.x changelog for replacements.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        new_config[key] = value

    # ------------------------------------------------------------------
    # SQLALCHEMY_TRACK_MODIFICATIONS — removed in Flask-SQLAlchemy 3.x
    # ------------------------------------------------------------------
    if new_config.get("SQLALCHEMY_TRACK_MODIFICATIONS", True):
        # TODO (SQLAlchemy 2.0 / Flask-SQLAlchemy 3.x breaking change):
        # SQLALCHEMY_TRACK_MODIFICATIONS is removed. Ensure it is set to
        # False (or absent) in all config files and environment configs.
        new_config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ------------------------------------------------------------------
    # SQLALCHEMY_ENGINE_OPTIONS — add pool_pre_ping for connection health
    # ------------------------------------------------------------------
    # pool_pre_ping=True causes SQLAlchemy to test connections before use,
    # discarding stale ones and preventing "connection already closed" errors
    # that contribute to apparent connection leaks.
    engine_options = new_config.get("SQLALCHEMY_ENGINE_OPTIONS", {})
    engine_options.setdefault("pool_pre_ping", True)
    # pool_recycle prevents connections from being held past the database's
    # wait_timeout (default 3600 seconds matches common MySQL/PostgreSQL config).
    engine_options.setdefault("pool_recycle", int(
        old_config.get("SQLALCHEMY_POOL_RECYCLE", 3600)
    ))
    new_config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

    # ------------------------------------------------------------------
    # Hardcoded credential detection
    # ------------------------------------------------------------------
    db_uri = new_config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri and _looks_like_hardcoded_credential(db_uri):
        # TODO (Security / upgrade spec): Hardcoded database credentials
        # detected in SQLALCHEMY_DATABASE_URI. Remove credentials from
        # source code and load from environment variables instead:
        #   SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
        # See spec: "Remove hardcoded credentials and introduce
        # environment-based secrets management."
        warnings.warn(
            "SQLALCHEMY_DATABASE_URI appears to contain hardcoded credentials. "
            "Move the database URL to the DATABASE_URL environment variable "
            "and load it with os.environ['DATABASE_URL'].",
            UserWarning,
            stacklevel=2,
        )
        # Attempt to promote from environment if available.
        env_db_url = os.environ.get("DATABASE_URL")
        if env_db_url:
            new_config["SQLALCHEMY_DATABASE_URI"] = env_db_url
            logger.info(
                "migrate_config: SQLALCHEMY_DATABASE_URI replaced with "
                "value from DATABASE_URL environment variable."
            )

    # ------------------------------------------------------------------
    # SECRET_KEY hardcoded credential detection
    # ------------------------------------------------------------------
    secret_key = new_config.get("SECRET_KEY", "")
    if secret_key and secret_key not in ("", None):
        if _looks_like_hardcoded_secret(secret_key):
            # TODO (Security / upgrade spec): SECRET_KEY appears to be a
            # hardcoded or weak value. Load it from an environment variable:
            #   SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
            warnings.warn(
                "Flask SECRET_KEY appears to be hardcoded or weak. "
                "Load it from the FLASK_SECRET_KEY environment variable.",
                UserWarning,
                stacklevel=2,
            )
            env_secret = os.environ.get("FLASK_SECRET_KEY")
            if env_secret:
                new_config["SECRET_KEY"] = env_secret

    # ------------------------------------------------------------------
    # SQLALCHEMY_AUTOCOMMIT removal
    # ------------------------------------------------------------------
    if new_config.pop("SQLALCHEMY_AUTOCOMMIT", False):
        # TODO (SQLAlchemy 2.0 breaking change): autocommit=True on Session
        # is removed in SQLAlchemy 2.0. Replace all autocommit usage with
        # explicit session.begin() / session.commit() blocks, or use the
        # managed_session() context manager provided by this shim.
        warnings.warn(
            "SQLALCHEMY_AUTOCOMMIT=True is removed in SQLAlchemy 2.0. "
            "Use explicit transaction management (session.commit() / "
            "session.rollback()) or the managed_session() context manager "
            "from this shim.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ------------------------------------------------------------------
    # TESTING / DEBUG flags
    # ------------------------------------------------------------------
    # TODO (Flask 3.x breaking change): TESTING=True no longer suppresses
    # exception propagation by default. Set PROPAGATE_EXCEPTIONS=True
    # explicitly in test configs if you relied on this behaviour.

    return new_config


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _looks_like_hardcoded_credential(uri: str) -> bool:
    """
    Heuristic check for credentials embedded in a database URI.

    Returns True if the URI contains a password component that is not
    sourced from an environment variable placeholder.
    """
    import re
    # Matches postgresql://user:password@host or mysql://user:pass@host
    pattern = re.compile(r"://[^:]+:[^@]+@")
    return bool(pattern.search(uri))


def _looks_like_hardcoded_secret(secret: str) -> bool:
    """
    Heuristic check for weak or obviously hardcoded Flask secret keys.
    """
    weak_values = {
        "secret", "secret_key", "dev", "development", "change_me",
        "changeme", "password", "flask_secret", "mysecret", "test",
        "testing", "insecure",
    }
    return len(secret) < 24 or secret.lower() in weak_values


# ---------------------------------------------------------------------------
# Deprecated import aliases (renamed packages / classes)
# ---------------------------------------------------------------------------
# Provide re-exports under old names so that existing import statements
# continue to work while the codebase is being migrated.
# ---------------------------------------------------------------------------

# TODO (SQLAlchemy 2.0 breaking change): sqlalchemy.orm.Query is in legacy
# mode. All usages of Query (including type annotations) should be replaced
# with select() statements. The alias below keeps existing isinstance() checks
# working but does not restore the removed .get() method.
try:
    from sqlalchemy.orm import Query as LegacyQuery  # noqa: F401
except ImportError:
    pass

# TODO (SQLAlchemy 2.0 breaking change): sqlalchemy.ext.declarative.declarative_base
# is moved to sqlalchemy.orm.declarative_base in SQLAlchemy 1.4+ and the
# ext.declarative path is removed in 2.0. Update all imports:
#   OLD: from sqlalchemy.ext.declarative import declarative_base
#   NEW: from sqlalchemy.orm import declarative_base
try:
    from sqlalchemy.orm import declarative_base  # noqa: F401 (2.0 canonical location)
except ImportError:
    try:
        from sqlalchemy.ext.declarative import declarative_base  # type: ignore[no-redef]  # noqa: F401
        warnings.warn(
            "sqlalchemy.ext.declarative.declarative_base is removed in "
            "SQLAlchemy 2.0. Update imports to: "
            "'from sqlalchemy.orm import declarative_base'.",
            DeprecationWarning,
            stacklevel=2,
        )
    except ImportError:
        pass

# TODO (SQLAlchemy 2.0 breaking change): sqlalchemy.orm.mapper() (classical
# mapping) is removed in 2.0. Migrate to declarative mapping using
# declarative_base() or the new registry() API.

# ---------------------------------------------------------------------------
# Flask signal / blinker dependency check
# ---------------------------------------------------------------------------
# TODO (Flask 3.x breaking change): blinker is now a hard dependency of
# Flask 3.x (it was optional in Flask 1.x/2.x). Add 'blinker>=1.6' to
# requirements.txt / setup.cfg / pyproject.toml.
try:
    import blinker  # noqa: F401
except ImportError:
    warnings.warn(
        "blinker is not installed. Flask 3.x requires blinker as a hard "
        "dependency. Add 'blinker>=1.6' to your requirements.",
        ImportWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# Public API summary
# ---------------------------------------------------------------------------
__all__ = [
    # SQLAlchemy session lifecycle helpers
    "make_session_factory",
    "make_scoped_session",
    "managed_session",
    "session_get",
    "engine_execute",
    "session_execute",
    "legacy_query_all",
    "legacy_query_first",
    # Flask helpers
    "create_app_with_session",
    "register_before_first_request",
    "flask_jsonify_safe",
    "escape",
    "Markup",
    # Config migration
    "migrate_config",
    # Re-exported SA aliases
    "declarative_base",
    "LegacyQuery",
]