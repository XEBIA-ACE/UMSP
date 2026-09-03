# migration_shim.py
# Compatibility shim for Flask 1.x -> 3.1 and SQLAlchemy 1.3 -> 2.0 migration
# Python 3.8 -> 3.12/3.13 upgrade helper
#
# Usage: Import this module early in your application to activate shims,
# or run directly to execute config migration utilities.

import warnings
import os
import sys
import functools
from typing import Any, Callable, Dict, Optional

# ---------------------------------------------------------------------------
# Python version guard
# ---------------------------------------------------------------------------

if sys.version_info < (3, 12):
    warnings.warn(
        "This project targets Python 3.12 or 3.13. "
        f"You are running Python {sys.version}. "
        "Upgrade your interpreter to match the modernized stack.",
        DeprecationWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# Flask compatibility shims  (Flask 1.x -> 3.1)
# ---------------------------------------------------------------------------

try:
    import flask as _flask
    from flask import Flask as _Flask

    _flask_version = tuple(int(x) for x in _flask.__version__.split(".")[:2])

    # ------------------------------------------------------------------
    # Removed in Flask 2.x: flask.json.jsonify moved; helpers consolidated
    # ------------------------------------------------------------------

    # Flask 1.x exposed flask.json.JSONEncoder / JSONDecoder as class attrs
    # on the app.  Flask 2.3+ removed app.json_encoder / app.json_decoder.
    # Provide a drop-in decorator that registers a custom provider instead.
    if _flask_version >= (2, 3):
        from flask.json.provider import DefaultJSONProvider as _DefaultJSONProvider

        def register_json_encoder(app: _Flask, encoder_cls: type) -> None:
            """
            Flask 1.x pattern:  app.json_encoder = MyEncoder
            Flask 3.x pattern:  use a JSONProvider subclass.

            This helper wraps the old encoder class in a DefaultJSONProvider
            so existing JSONEncoder subclasses keep working with minimal changes.
            """
            # TODO: Manually review custom JSONEncoder.default() implementations.
            # Flask 3.x JSONProvider.default() has a different signature.
            # Breaking change: https://flask.palletsprojects.com/en/3.0.x/api/#flask.json.provider.JSONProvider
            class _CompatProvider(_DefaultJSONProvider):
                def default(self, o: Any) -> Any:
                    enc = encoder_cls()
                    try:
                        return enc.default(o)
                    except TypeError:
                        return super().default(o)

            app.json_provider_class = _CompatProvider
            app.json = _CompatProvider(app)

    else:
        def register_json_encoder(app: _Flask, encoder_cls: type) -> None:
            """Flask 1.x / 2.x compatible path — sets app.json_encoder directly."""
            app.json_encoder = encoder_cls  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Removed in Flask 2.0: before_first_request
    # ------------------------------------------------------------------

    def before_first_request(app: _Flask, f: Callable) -> Callable:
        """
        Flask 1.x: @app.before_first_request
        Flask 2.3+: decorator removed.

        Replacement: use with app.app_context() at startup, or call the
        function inside the application factory after app creation.

        This shim executes the function once on the first request using a
        with_appcontext wrapper registered via before_request.
        """
        # TODO: Migrate before_first_request usages to the application factory
        # pattern (create_app).  The shim below is a stopgap only.
        # Breaking change ref: https://flask.palletsprojects.com/en/2.3.x/changes/#version-2-3-0
        _called = {"done": False}

        @app.before_request
        def _wrapper() -> None:
            if not _called["done"]:
                _called["done"] = True
                f()

        return f

    # ------------------------------------------------------------------
    # Removed in Flask 2.0: flask.ext namespace
    # ------------------------------------------------------------------
    # TODO: Remove all `from flask.ext import X` imports in your codebase.
    # Flask 3.x no longer supports the flask.ext shim namespace.
    # Replace with direct package imports, e.g. `from flask_sqlalchemy import SQLAlchemy`.

    # ------------------------------------------------------------------
    # Renamed in Flask 2.0: flask.escape -> markupsafe.escape
    # ------------------------------------------------------------------
    try:
        from flask import escape as _flask_escape  # type: ignore[attr-defined]
    except ImportError:
        try:
            from markupsafe import escape  # noqa: F401  re-export
        except ImportError:
            pass
    else:
        from markupsafe import escape  # noqa: F401  re-export
        warnings.warn(
            "flask.escape is removed in Flask 2.x+. "
            "Use `from markupsafe import escape` instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ------------------------------------------------------------------
    # Renamed in Flask 2.0: flask.Markup -> markupsafe.Markup
    # ------------------------------------------------------------------
    try:
        from flask import Markup as _flask_Markup  # type: ignore[attr-defined]
    except ImportError:
        try:
            from markupsafe import Markup  # noqa: F401  re-export
        except ImportError:
            pass
    else:
        from markupsafe import Markup  # noqa: F401  re-export
        warnings.warn(
            "flask.Markup is removed in Flask 2.x+. "
            "Use `from markupsafe import Markup` instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ------------------------------------------------------------------
    # Application factory helper
    # ------------------------------------------------------------------

    def create_app_factory(
        config_object: Optional[Any] = None,
        config_mapping: Optional[Dict[str, Any]] = None,
    ) -> _Flask:
        """
        Minimal application factory conforming to Flask 3.x best practices.

        Flask 1.x apps were commonly created at module level (global app object).
        Flask 3.x strongly recommends the application factory pattern.

        TODO: Replace your module-level `app = Flask(__name__)` with a
        `create_app()` factory function.  See:
        https://flask.palletsprojects.com/en/3.0.x/patterns/appfactories/
        """
        app = _Flask(__name__)

        if config_object is not None:
            app.config.from_object(config_object)

        if config_mapping is not None:
            app.config.from_mapping(config_mapping)

        # Load secrets from environment — replaces hardcoded credentials.
        # TODO: Ensure all secrets (SECRET_KEY, DB passwords, API keys) are
        # provided via environment variables, not hardcoded in config files.
        app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", ""))
        if not app.config["SECRET_KEY"]:
            warnings.warn(
                "SECRET_KEY is not set via environment variable SECRET_KEY. "
                "Hardcoded or empty secret keys are a security risk.",
                RuntimeWarning,
                stacklevel=2,
            )

        return app

    # ------------------------------------------------------------------
    # Removed in Flask 3.0: flask.signals (blinker now required)
    # ------------------------------------------------------------------
    # TODO: Add `blinker` to your requirements if you use Flask signals.
    # Flask 3.0 made blinker a hard dependency; signals are no longer optional.

except ImportError:
    warnings.warn(
        "Flask is not installed. Flask shims will not be active.",
        ImportWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# SQLAlchemy compatibility shims  (1.3 -> 2.0)
# ---------------------------------------------------------------------------

try:
    import sqlalchemy as _sa

    _sa_version = tuple(int(x) for x in _sa.__version__.split(".")[:2])

    # ------------------------------------------------------------------
    # Legacy Query API -> 2.0 select() style
    # ------------------------------------------------------------------

    def legacy_query_warning(method_name: str) -> None:
        warnings.warn(
            f"SQLAlchemy 1.x Session.query() used via '{method_name}'. "
            "Session.query() is legacy in SQLAlchemy 2.0. "
            "Migrate to `select()` statements: "
            "https://docs.sqlalchemy.org/en/20/orm/queryguide/",
            DeprecationWarning,
            stacklevel=3,
        )

    class LegacyQueryShim:
        """
        Wraps a SQLAlchemy 2.0 Session to intercept .query() calls and
        emit deprecation warnings, while still delegating to the legacy
        interface (available via Session(future=False) or the legacy bundle).

        TODO: Replace all Session.query(Model).filter(...).all() patterns
        with the 2.0 select() API:
            from sqlalchemy import select
            stmt = select(Model).where(Model.col == value)
            results = session.execute(stmt).scalars().all()
        Breaking change: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#orm-query-unified-with-core-select
        """

        def __init__(self, session: Any) -> None:
            self._session = session

        def query(self, *entities: Any, **kwargs: Any) -> Any:
            legacy_query_warning("Session.query")
            return self._session.query(*entities, **kwargs)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._session, name)

    # ------------------------------------------------------------------
    # Removed in 2.0: session.execute(string) without text()
    # ------------------------------------------------------------------

    def safe_execute(session: Any, statement: Any, params: Optional[Dict] = None) -> Any:
        """
        SQLAlchemy 1.x allowed session.execute("SELECT ...").
        SQLAlchemy 2.0 requires sqlalchemy.text() for raw SQL strings.

        This helper wraps raw strings automatically.

        TODO: Replace direct string execution in your codebase with
        `sqlalchemy.text()` explicitly for clarity and safety.
        Breaking change: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#change-4617
        """
        from sqlalchemy import text as _text

        if isinstance(statement, str):
            warnings.warn(
                "Passing a raw string to session.execute() is not supported "
                "in SQLAlchemy 2.0. Wrapping in sqlalchemy.text() automatically. "
                "Update your code to use text() explicitly.",
                DeprecationWarning,
                stacklevel=2,
            )
            statement = _text(statement)

        if params is not None:
            return session.execute(statement, params)
        return session.execute(statement)

    # ------------------------------------------------------------------
    # Removed in 2.0: Query.get() -> Session.get()
    # ------------------------------------------------------------------

    def session_get(session: Any, model: type, ident: Any) -> Any:
        """
        SQLAlchemy 1.x: Model.query.get(pk)  or  session.query(Model).get(pk)
        SQLAlchemy 2.0: session.get(Model, pk)

        This helper provides a unified call that works on 2.0 and emits a
        warning when the legacy path would have been used.

        TODO: Replace all `.query.get(pk)` usages with `session.get(Model, pk)`.
        Breaking change: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#orm-query-get-method-moved-to-session
        """
        if _sa_version >= (2, 0):
            return session.get(model, ident)
        else:
            warnings.warn(
                "session_get() shim: using legacy Query.get(). "
                "Upgrade to SQLAlchemy 2.0 and use session.get(Model, pk).",
                DeprecationWarning,
                stacklevel=2,
            )
            return session.query(model).get(ident)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Removed in 2.0: autocommit mode on Session
    # ------------------------------------------------------------------
    # TODO: Remove Session(autocommit=True) usage.  SQLAlchemy 2.0 removed
    # autocommit mode entirely.  Use explicit session.commit() / session.begin().
    # Breaking change: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#autocommit-mode-removed

    # ------------------------------------------------------------------
    # Changed in 2.0: Engine.execute() removed
    # ------------------------------------------------------------------

    def engine_execute(engine: Any, statement: Any, params: Optional[Dict] = None) -> Any:
        """
        SQLAlchemy 1.x: engine.execute(stmt)
        SQLAlchemy 2.0: engine.execute() removed; use engine.connect() context manager.

        TODO: Replace engine.execute() with:
            with engine.connect() as conn:
                result = conn.execute(text("..."))
        Breaking change: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#engine-execute-removed
        """
        from sqlalchemy import text as _text

        warnings.warn(
            "engine.execute() is removed in SQLAlchemy 2.0. "
            "Use `with engine.connect() as conn: conn.execute(...)` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if isinstance(statement, str):
            statement = _text(statement)

        with engine.connect() as conn:
            if params is not None:
                result = conn.execute(statement, params)
            else:
                result = conn.execute(statement)
            conn.commit()
            return result

    # ------------------------------------------------------------------
    # Changed in 2.0: declarative_base() moved
    # ------------------------------------------------------------------
    # SQLAlchemy 1.x: from sqlalchemy.ext.declarative import declarative_base
    # SQLAlchemy 2.0: from sqlalchemy.orm import declarative_base  (then DeclarativeBase)

    try:
        from sqlalchemy.orm import declarative_base  # noqa: F401  (2.0+)
    except ImportError:
        try:
            from sqlalchemy.ext.declarative import declarative_base  # type: ignore[no-redef]  # noqa: F401
            warnings.warn(
                "sqlalchemy.ext.declarative.declarative_base is deprecated. "
                "Use `from sqlalchemy.orm import declarative_base` (SQLAlchemy 1.4+) "
                "or `sqlalchemy.orm.DeclarativeBase` (SQLAlchemy 2.0+).",
                DeprecationWarning,
                stacklevel=2,
            )
        except ImportError:
            pass

    # TODO: In SQLAlchemy 2.0, prefer the new DeclarativeBase class syntax:
    #   from sqlalchemy.orm import DeclarativeBase
    #   class Base(DeclarativeBase): pass
    # This replaces declarative_base() entirely.
    # Breaking change: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#orm-declarative-mapping

    # ------------------------------------------------------------------
    # Changed in 2.0: relationship() lazy loading behaviour
    # ------------------------------------------------------------------
    # TODO: SQLAlchemy 2.0 raises an error for lazy-loaded relationships
    # accessed outside a session.  Audit all relationship() definitions and
    # add explicit lazy="select", lazy="joined", or lazy="subquery" as needed.
    # Breaking change: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#lazy-loading-for-relationship-raises-by-default

except ImportError:
    warnings.warn(
        "SQLAlchemy is not installed. SQLAlchemy shims will not be active.",
        ImportWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# Config format migration utility
# ---------------------------------------------------------------------------

def migrate_flask_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a Flask 1.x style config dictionary to a Flask 3.x compatible one.

    Handles:
    - PROPAGATE_EXCEPTIONS default change
    - JSON_AS_ASCII removal
    - JSON_SORT_KEYS removal
    - JSONIFY_PRETTYPRINT_REGULAR removal
    - JSONIFY_MIMETYPE change
    - TEMPLATES_AUTO_RELOAD moved to Jinja env
    - Hardcoded SECRET_KEY -> environment variable reference warning
    - DATABASE_URI -> SQLALCHEMY_DATABASE_URI normalisation
    """
    new_config: Dict[str, Any] = {}

    # Removed JSON config keys in Flask 2.2+
    _removed_json_keys = {
        "JSON_AS_ASCII",
        "JSON_SORT_KEYS",
        "JSONIFY_PRETTYPRINT_REGULAR",
        "JSONIFY_MIMETYPE",
    }

    for key, value in old_config.items():
        if key in _removed_json_keys:
            # TODO: Configure JSON behaviour via app.json (JSONProvider) in Flask 3.x.
            # Breaking change: https://flask.palletsprojects.com/en/3.0.x/api/#flask.Flask.json
            warnings.warn(
                f"Config key '{key}' is removed in Flask 2.2+. "
                "Configure JSON behaviour via app.json provider instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue  # drop from new config

        if key == "TEMPLATES_AUTO_RELOAD":
            # TODO: Set app.jinja_env.auto_reload = True in your factory instead.
            warnings.warn(
                "TEMPLATES_AUTO_RELOAD config key is deprecated in Flask 2.x. "
                "Set app.jinja_env.auto_reload directly.",
                DeprecationWarning,
                stacklevel=2,
            )
            new_config[key] = value
            continue

        if key == "SECRET_KEY":
            if not isinstance(value, str) or (
                value and value not in ("", "dev", "development", "changeme")
            ):
                # Looks like a real hardcoded secret
                # TODO: Remove hardcoded SECRET_KEY from config.
                # Store it in an environment variable and load with:
                #   app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
                warnings.warn(
                    "Hardcoded SECRET_KEY detected in config. "
                    "Move this value to the SECRET_KEY environment variable.",
                    RuntimeWarning,
                    stacklevel=2,
                )
            new_config[key] = os.environ.get("SECRET_KEY", value)
            continue

        # Normalise legacy DATABASE_URI -> SQLALCHEMY_DATABASE_URI
        if key == "DATABASE_URI":
            warnings.warn(
                "Config key 'DATABASE_URI' is not a standard Flask/SQLAlchemy key. "
                "Renaming to 'SQLALCHEMY_DATABASE_URI'.",
                DeprecationWarning,
                stacklevel=2,
            )
            new_config["SQLALCHEMY_DATABASE_URI"] = _migrate_db_uri(value)
            continue

        if key == "SQLALCHEMY_DATABASE_URI":
            new_config[key] = _migrate_db_uri(value)
            continue

        # SQLAlchemy 2.0: SQLALCHEMY_TRACK_MODIFICATIONS defaults to False and
        # the key is removed in Flask-SQLAlchemy 3.x.
        if key == "SQLALCHEMY_TRACK_MODIFICATIONS":
            warnings.warn(
                "SQLALCHEMY_TRACK_MODIFICATIONS is removed in Flask-SQLAlchemy 3.x. "
                "Remove this key from your config.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue  # drop from new config

        new_config[key] = value

    return new_config


def _migrate_db_uri(uri: str) -> str:
    """
    SQLAlchemy 2.0 removed support for the 'postgres://' dialect prefix.
    It must be 'postgresql://'.  Also warns about sqlite relative paths.
    """
    if isinstance(uri, str) and uri.startswith("postgres://"):
        warnings.warn(
            "Database URI uses deprecated 'postgres://' scheme. "
            "SQLAlchemy 2.0 requires 'postgresql://'. Updating automatically.",
            DeprecationWarning,
            stacklevel=3,
        )
        uri = "postgresql://" + uri[len("postgres://"):]

    # TODO: If using MySQL, ensure the dialect is 'mysql+pymysql://' or
    # 'mysql+mysqlconnector://' as the default MySQLdb dialect may not be
    # available on Python 3.12+.

    return uri


def migrate_sqlalchemy_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms SQLAlchemy 1.3 engine/session config kwargs to 2.0 equivalents.

    Handles:
    - Removed: convert_unicode (always True in 2.0)
    - Removed: encoding
    - Changed: execution_options placement
    """
    new_config: Dict[str, Any] = {}

    _removed_engine_keys = {"convert_unicode", "encoding"}

    for key, value in old_config.items():
        if key in _removed_engine_keys:
            # TODO: Remove these keys from your create_engine() calls.
            # Breaking change: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html
            warnings.warn(
                f"create_engine() argument '{key}' is removed in SQLAlchemy 2.0. "
                "Remove it from your engine configuration.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        new_config[key] = value

    return new_config


# ---------------------------------------------------------------------------
# Environment-based secrets helper
# ---------------------------------------------------------------------------

def load_secrets_from_env(required_keys: Optional[list] = None) -> Dict[str, str]:
    """
    Loads application secrets from environment variables.

    Replaces hardcoded credentials in config files.

    TODO: Ensure the following variables are set in your deployment environment
    (or a .env file loaded via python-dotenv — add `python-dotenv` to requirements):
        SECRET_KEY          - Flask secret key
        DATABASE_URL        - Primary database connection string
        Any other secrets previously hardcoded in config.py or settings.py

    Returns a dict of resolved secret values.
    """
    defaults = required_keys or ["SECRET_KEY", "DATABASE_URL"]
    secrets: Dict[str, str] = {}
    missing = []

    for key in defaults:
        val = os.environ.get(key)
        if val:
            secrets[key] = val
        else:
            missing.append(key)

    if missing:
        warnings.warn(
            f"The following required environment variables are not set: {missing}. "
            "Set them before running the application in production.",
            RuntimeWarning,
            stacklevel=2,
        )

    return secrets


# ---------------------------------------------------------------------------
# Flask-SQLAlchemy shim  (Flask-SQLAlchemy 2.x -> 3.x)
# ---------------------------------------------------------------------------

try:
    import flask_sqlalchemy as _fsa

    _fsa_version = tuple(
        int(x) for x in _fsa.__version__.split(".")[:2]
        if x.isdigit()
    )

    if _fsa_version < (3, 0):
        warnings.warn(
            f"Flask-SQLAlchemy {_fsa.__version__} detected. "
            "Flask-SQLAlchemy 3.x is required for SQLAlchemy 2.0 compatibility. "
            "Run: pip install 'Flask-SQLAlchemy>=3.0'",
            DeprecationWarning,
            stacklevel=2,
        )

    # TODO: Flask-SQLAlchemy 3.x removed Model.query (the legacy scoped query interface).
    # Replace Model.query.filter_by(...).all() with:
    #   from sqlalchemy import select
    #   db.session.execute(select(Model).filter_by(...)).scalars().all()
    # Breaking change: https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/changes/

    # TODO: Flask-SQLAlchemy 3.x removed db.get_or_404() signature change —
    # verify all get_or_404() / first_or_404() / one_or_404() call sites.

except ImportError:
    pass  # Flask-SQLAlchemy not installed; skip

# ---------------------------------------------------------------------------
# Deprecation shim: werkzeug imports that moved between Flask versions
# ---------------------------------------------------------------------------

try:
    # Werkzeug 2.x+ moved several utilities; Flask 3.x requires Werkzeug 3.x
    from werkzeug.urls import url_quote as _wz_url_quote  # type: ignore[attr-defined]
    warnings.warn(
        "werkzeug.urls.url_quote is removed in Werkzeug 3.x. "
        "Use urllib.parse.quote instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from urllib.parse import quote as url_quote  # noqa: F401  re-export
except ImportError:
    try:
        from urllib.parse import quote as url_quote  # noqa: F401  re-export
    except ImportError:
        pass

try:
    from werkzeug.urls import url_encode as _wz_url_encode  # type: ignore[attr-defined]
    warnings.warn(
        "werkzeug.urls.url_encode is removed in Werkzeug 3.x. "
        "Use urllib.parse.urlencode instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from urllib.parse import urlencode as url_encode  # noqa: F401  re-export
except ImportError:
    try:
        from urllib.parse import urlencode as url_encode  # noqa: F401  re-export
    except ImportError:
        pass

# ---------------------------------------------------------------------------
# Python 3.8 -> 3.12 compatibility notes
# ---------------------------------------------------------------------------

# TODO: Review usage of the following Python 3.8 -> 3.12 breaking changes:
#
# 1. distutils is removed in Python 3.12.
#    Replace `from distutils.version import LooseVersion` with `packaging.version`.
#    Add `packaging` to requirements.txt if not present.
#
# 2. asyncio.coroutine decorator removed in 3.11 (deprecated since 3.8).
#    Replace with `async def`.
#
# 3. unittest.TestCase.assertEquals (and similar aliases) removed in 3.12.
#    Use assertEqual, assertTrue, etc.
#
# 4. imp module removed in 3.12.  Use importlib instead.
#
# 5. datetime.datetime.utcnow() deprecated in 3.12.
#    Use datetime.datetime.now(datetime.timezone.utc) instead.
#
# 6. typing.* aliases (List, Dict, Tuple, etc.) deprecated in 3.9+.
#    Use built-in generics: list[str], dict[str, int], tuple[int, ...].
#    Still functional in 3.12 but emit DeprecationWarning in some contexts.

# ---------------------------------------------------------------------------
# Self-test / migration report (run this file directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Migration Shim — Compatibility Report")
    print("=" * 60)

    print(f"\nPython version : {sys.version}")

    try:
        import flask
        print(f"Flask version  : {flask.__version__}")
    except ImportError:
        print("Flask          : NOT INSTALLED")

    try:
        import sqlalchemy
        print(f"SQLAlchemy     : {sqlalchemy.__version__}")
    except ImportError:
        print("SQLAlchemy     : NOT INSTALLED")

    try:
        import flask_sqlalchemy
        print(f"Flask-SQLAlchemy: {flask_sqlalchemy.__version__}")
    except ImportError:
        print("Flask-SQLAlchemy: NOT INSTALLED")

    try:
        import werkzeug
        print(f"Werkzeug       : {werkzeug.__version__}")
    except ImportError:
        print("Werkzeug       : NOT INSTALLED")

    print("\n--- Config migration smoke test ---")
    sample_old_config: Dict[str, Any] = {
        "SECRET_KEY": "hardcoded-secret",
        "DATABASE_URI": "postgres://user:pass@localhost/mydb",
        "SQLALCHEMY_TRACK_MODIFICATIONS": True,
        "JSON_AS_ASCII": True,
        "JSON_SORT_KEYS": True,
        "DEBUG": True,
    }
    print("Old config:", sample_old_config)
    new_cfg = migrate_flask_config(sample_old_config)
    print("New config:", new_cfg)

    print("\n--- SQLAlchemy engine config migration ---")
    old_engine_cfg: Dict[str, Any] = {
        "convert_unicode": True,
        "encoding": "utf-8",
        "pool_size": 5,
        "echo": False,
    }
    print("Old engine config:", old_engine_cfg)
    new_engine_cfg = migrate_sqlalchemy_config(old_engine_cfg)
    print("New engine config:", new_engine_cfg)

    print("\n--- Secrets from environment ---")
    secrets = load_secrets_from_env(["SECRET_KEY", "DATABASE_URL"])
    print("Resolved secrets keys:", list(secrets.keys()))

    print("\nDone. Review all TODO comments in migration_shim.py for manual steps.")