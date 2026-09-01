# migration_shim.py
# Compatibility shim for Flask 1.x -> 3.1 and SQLAlchemy 1.3 -> 2.0 migration
# Python 3.8 -> 3.12/3.13 upgrade helper
#
# Usage: import this module early in your application to activate shims,
# or run directly to execute config migration utilities.

import os
import sys
import warnings
import functools
import importlib
from typing import Any, Callable, Dict, Optional

# ---------------------------------------------------------------------------
# Python version guard
# ---------------------------------------------------------------------------

if sys.version_info < (3, 12):
    warnings.warn(
        "This project targets Python 3.12 or 3.13. "
        f"You are running Python {sys.version}. "
        "Please upgrade your runtime.",
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

    # Flask 1.x exposed flask.json.jsonify directly; still works in 3.x but
    # the underlying encoder API changed.  Re-export for safe import.
    try:
        from flask import jsonify  # noqa: F401  (re-export)
    except ImportError:
        from flask.json import jsonify  # noqa: F401  # type: ignore[no-redef]

    # ------------------------------------------------------------------
    # Removed in Flask 2.x: before_first_request decorator
    # Flask 1.x: @app.before_first_request
    # Flask 3.x: use app.with_appcontext / startup signal or init in factory
    # ------------------------------------------------------------------

    def before_first_request_shim(app: _Flask, func: Callable) -> Callable:
        """
        Replacement for the removed @app.before_first_request decorator.

        Registers *func* to run once before the first request is handled,
        using a flag stored on the app object.

        Usage (Flask 3.x):
            before_first_request_shim(app, my_setup_function)

        # TODO: Replace all @app.before_first_request usages in your codebase
        #       with explicit initialisation inside the application factory or
        #       via Flask 3.x startup hooks.  See Flask 3.x migration guide:
        #       https://flask.palletsprojects.com/en/3.1.x/changes/
        """
        _sentinel_attr = "_shim_first_request_done"

        @app.before_request
        @functools.wraps(func)
        def _wrapper():
            if not getattr(app, _sentinel_attr, False):
                setattr(app, _sentinel_attr, True)
                return func()

        return _wrapper

    # ------------------------------------------------------------------
    # Application factory helper
    # Flask 1.x apps were often created at module level (global app object).
    # Flask 3.x strongly recommends the application factory pattern.
    # ------------------------------------------------------------------

    def create_app_factory(
        config: Optional[Dict[str, Any]] = None,
        *,
        import_name: str = __name__,
    ) -> _Flask:
        """
        Minimal application factory scaffold.

        # TODO: Move your existing module-level `app = Flask(__name__)` into a
        #       function like this one.  Wire up blueprints, extensions, and
        #       database initialisation inside the factory.
        #       See: https://flask.palletsprojects.com/en/3.1.x/patterns/appfactories/
        """
        app = _Flask(import_name)

        if config:
            app.config.from_mapping(config)

        # TODO: Register blueprints here, e.g.:
        #   from .blueprints.api import api_bp
        #   app.register_blueprint(api_bp)

        # TODO: Initialise extensions here, e.g.:
        #   db.init_app(app)

        return app

    # ------------------------------------------------------------------
    # Removed in Flask 2.x: flask.ext namespace
    # ------------------------------------------------------------------

    class _FlaskExtShim:
        """
        Shim for the removed `flask.ext.*` import namespace (Flask 1.x).

        # TODO: Replace all `from flask.ext import <name>` imports with the
        #       direct package import, e.g. `import flask_<name>`.
        """

        def __getattr__(self, name: str):
            warnings.warn(
                f"flask.ext.{name} is not available in Flask 2+. "
                f"Use `import flask_{name}` directly.",
                DeprecationWarning,
                stacklevel=2,
            )
            return importlib.import_module(f"flask_{name}")

    # Inject shim into sys.modules so `from flask.ext import x` still resolves
    # during the transition period.
    if "flask.ext" not in sys.modules:
        sys.modules["flask.ext"] = _FlaskExtShim()  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # Removed in Flask 3.x: flask._app_ctx_stack / flask._request_ctx_stack
    # ------------------------------------------------------------------

    try:
        from flask.globals import _app_ctx_stack  # noqa: F401
    except ImportError:
        # Flask 3.x removed these; provide a no-op sentinel
        class _CtxStackShim:
            """
            Shim for removed flask._app_ctx_stack / _request_ctx_stack.

            # TODO: Remove all direct references to flask._app_ctx_stack and
            #       flask._request_ctx_stack.  Use flask.g or the current_app
            #       proxy instead.
            """

            top = None

            def push(self, *a, **kw):  # noqa: D401
                warnings.warn(
                    "_app_ctx_stack is removed in Flask 3.x. Use flask.g.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            def pop(self, *a, **kw):
                warnings.warn(
                    "_app_ctx_stack is removed in Flask 3.x. Use flask.g.",
                    DeprecationWarning,
                    stacklevel=2,
                )

        sys.modules.setdefault("flask._app_ctx_stack", _CtxStackShim())  # type: ignore[assignment]
        sys.modules.setdefault("flask._request_ctx_stack", _CtxStackShim())  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # Flask 2.x: PROPAGATE_EXCEPTIONS default changed; JSON_SORT_KEYS removed
    # ------------------------------------------------------------------

    def patch_flask_config(app: _Flask) -> None:
        """
        Apply config key renames / removals introduced between Flask 1.x and 3.x.

        Call this immediately after creating your Flask app instance.

        # TODO: Audit your config for the following removed/renamed keys and
        #       update them manually:
        #         - JSON_SORT_KEYS        -> removed; set app.json.sort_keys
        #         - JSON_PRETTYPRINT_REGULAR -> removed
        #         - JSONIFY_PRETTYPRINT_REGULAR -> removed
        #         - JSONIFY_MIMETYPE      -> removed; set app.json.mimetype
        #         - TEMPLATES_AUTO_RELOAD -> still supported but configure via
        #                                    app.jinja_env.auto_reload
        """
        _legacy_json_keys = {
            "JSON_SORT_KEYS",
            "JSON_PRETTYPRINT_REGULAR",
            "JSONIFY_PRETTYPRINT_REGULAR",
            "JSONIFY_MIMETYPE",
        }
        for key in _legacy_json_keys:
            if key in app.config:
                warnings.warn(
                    f"Flask config key '{key}' is removed in Flask 2+/3.x. "
                    "See Flask changelog for the replacement.",
                    DeprecationWarning,
                    stacklevel=2,
                )

        # JSON_SORT_KEYS shim
        if "JSON_SORT_KEYS" in app.config and hasattr(app, "json"):
            app.json.sort_keys = app.config.pop("JSON_SORT_KEYS")  # type: ignore[attr-defined]

        # JSONIFY_MIMETYPE shim
        if "JSONIFY_MIMETYPE" in app.config and hasattr(app, "json"):
            app.json.mimetype = app.config.pop("JSONIFY_MIMETYPE")  # type: ignore[attr-defined]

except ImportError:
    warnings.warn("Flask is not installed; Flask shims skipped.", ImportWarning, stacklevel=2)


# ---------------------------------------------------------------------------
# SQLAlchemy compatibility shims  (1.3 -> 2.0)
# ---------------------------------------------------------------------------

try:
    import sqlalchemy as _sa

    _sa_version = tuple(int(x) for x in _sa.__version__.split(".")[:2])

    # ------------------------------------------------------------------
    # Declarative base: sqlalchemy.ext.declarative.declarative_base (1.3)
    #                -> sqlalchemy.orm.DeclarativeBase subclass (2.0)
    # ------------------------------------------------------------------

    try:
        # 2.0 preferred path
        from sqlalchemy.orm import DeclarativeBase as _DeclarativeBase

        class Base(_DeclarativeBase):
            """
            New-style declarative base for SQLAlchemy 2.0.

            Replace all occurrences of:
                from sqlalchemy.ext.declarative import declarative_base
                Base = declarative_base()

            with:
                from migration_shim import Base

            # TODO: After migration, define your own Base subclass in your
            #       models package and remove this shim import.
            """

    except ImportError:
        # Fallback for SQLAlchemy 1.4 legacy path
        from sqlalchemy.ext.declarative import declarative_base as _declarative_base  # type: ignore[no-redef]

        Base = _declarative_base()  # type: ignore[assignment]

    # Re-export legacy import path
    try:
        from sqlalchemy.ext.declarative import declarative_base  # noqa: F401
    except ImportError:
        # Removed in 2.0 — provide shim
        def declarative_base(**kwargs):  # type: ignore[misc]
            """
            Shim for removed sqlalchemy.ext.declarative.declarative_base.

            # TODO: Replace `declarative_base()` calls with a subclass of
            #       sqlalchemy.orm.DeclarativeBase (SQLAlchemy 2.0 style).
            #       See: https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html
            """
            warnings.warn(
                "sqlalchemy.ext.declarative.declarative_base is removed in "
                "SQLAlchemy 2.0. Use sqlalchemy.orm.DeclarativeBase instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            from sqlalchemy.orm import DeclarativeBase

            class _DynBase(DeclarativeBase):
                pass

            return _DynBase

    # ------------------------------------------------------------------
    # Session: Session.execute() result API changed in 2.0
    # 1.3: session.execute(text_or_query) -> ResultProxy (list-like)
    # 2.0: session.execute(statement)     -> CursorResult (use .scalars(), .all(), etc.)
    # ------------------------------------------------------------------

    try:
        from sqlalchemy.orm import Session as _Session

        class LegacySessionMixin:
            """
            Mixin that adds 1.x-style convenience wrappers around the 2.0 Session.

            # TODO: Replace usages of these wrapper methods with native 2.0
            #       session.execute() / session.scalars() calls.
            """

            def legacy_query(self, *entities, **kwargs):
                """
                Thin wrapper around the legacy Query API.

                # TODO: Migrate all session.query(Model).filter(...) chains to
                #       select(Model).where(...) with session.execute() or
                #       session.scalars().
                #       See: https://docs.sqlalchemy.org/en/20/orm/queryguide/
                """
                warnings.warn(
                    "Session.query() is legacy in SQLAlchemy 2.0. "
                    "Use select() + session.execute() / session.scalars().",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return self.query(*entities, **kwargs)  # type: ignore[attr-defined]

    except ImportError:
        pass

    # ------------------------------------------------------------------
    # Engine creation: create_engine flag changes
    # 1.3: create_engine(url, ...)
    # 2.0: future=True is now the default (and the flag is removed)
    # ------------------------------------------------------------------

    from sqlalchemy import create_engine as _orig_create_engine

    def create_engine(url: str, **kwargs) -> Any:
        """
        Shim for sqlalchemy.create_engine that strips the legacy `future`
        keyword (always True in 2.0) and warns about removed options.

        # TODO: Remove this shim once all create_engine() call sites have been
        #       updated to SQLAlchemy 2.0 style.
        """
        if "future" in kwargs:
            warnings.warn(
                "The `future` keyword for create_engine() is removed in "
                "SQLAlchemy 2.0 (it is always True). Remove the argument.",
                DeprecationWarning,
                stacklevel=2,
            )
            kwargs.pop("future")

        # TODO: If you use `convert_unicode=True`, remove it — it is gone in 2.0.
        if kwargs.pop("convert_unicode", None) is not None:
            warnings.warn(
                "create_engine(convert_unicode=...) is removed in SQLAlchemy 2.0.",
                DeprecationWarning,
                stacklevel=2,
            )

        return _orig_create_engine(url, **kwargs)

    # ------------------------------------------------------------------
    # Removed: sqlalchemy.orm.mapper() (classical mapping)
    # 2.0: use registry.map_imperatively()
    # ------------------------------------------------------------------

    try:
        from sqlalchemy.orm import mapper  # noqa: F401  (still present in 1.4)
    except ImportError:
        def mapper(*args, **kwargs):  # type: ignore[misc]
            """
            Shim for removed sqlalchemy.orm.mapper (classical mapping).

            # TODO: Replace classical mapper() calls with
            #       registry.map_imperatively().
            #       See: https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#imperative-mapping
            """
            raise RuntimeError(
                "sqlalchemy.orm.mapper() is removed in SQLAlchemy 2.0. "
                "Use registry().map_imperatively() instead.\n"
                "# TODO: Migrate all classical mapper() usages."
            )

    # ------------------------------------------------------------------
    # Removed: Query.get() -> Session.get()
    # ------------------------------------------------------------------

    def session_get_shim(session: Any, model: Any, ident: Any) -> Any:
        """
        Replacement for the removed Query.get() pattern.

        Old (1.3):  session.query(Model).get(pk)
        New (2.0):  session.get(Model, pk)

        # TODO: Replace all `session.query(Model).get(pk)` calls with
        #       `session.get(Model, pk)`.
        """
        warnings.warn(
            "Query.get() is removed in SQLAlchemy 2.0. "
            "Use session.get(Model, pk) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return session.get(model, ident)

    # ------------------------------------------------------------------
    # Removed: implicit autocommit on Session
    # 2.0: explicit session.commit() / session.rollback() required
    # ------------------------------------------------------------------

    def get_scoped_session(engine: Any) -> Any:
        """
        Returns a scoped session factory configured for SQLAlchemy 2.0.

        # TODO: Replace any Session(autocommit=True) usage with explicit
        #       transaction management (session.begin() / session.commit()).
        #       See: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
        """
        from sqlalchemy.orm import sessionmaker, scoped_session

        factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return scoped_session(factory)

except ImportError:
    warnings.warn(
        "SQLAlchemy is not installed; SQLAlchemy shims skipped.",
        ImportWarning,
        stacklevel=2,
    )


# ---------------------------------------------------------------------------
# Config format migration utility
# ---------------------------------------------------------------------------

def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a legacy (Flask 1.x / SQLAlchemy 1.3) config dict into the
    format expected by Flask 3.1 / SQLAlchemy 2.0.

    Returns a new dict; does not mutate the input.

    # TODO: Extend this function with any application-specific config keys
    #       that are renamed or restructured in your project.
    """
    new_config: Dict[str, Any] = {}

    _key_renames: Dict[str, str] = {
        # Flask renames / removals
        # (removed keys are handled separately below)
        "SERVER_NAME": "SERVER_NAME",  # unchanged but validate format
        "SQLALCHEMY_DATABASE_URI": "SQLALCHEMY_DATABASE_URI",  # unchanged
        # TODO: Add project-specific key renames here.
    }

    _removed_keys = {
        "JSON_SORT_KEYS",
        "JSON_PRETTYPRINT_REGULAR",
        "JSONIFY_PRETTYPRINT_REGULAR",
        "JSONIFY_MIMETYPE",
        # SQLAlchemy-Flask extension keys removed/renamed in Flask-SQLAlchemy 3.x
        "SQLALCHEMY_POOL_TIMEOUT",  # TODO: verify replacement in your FA-SQLAlchemy version
    }

    for key, value in old_config.items():
        if key in _removed_keys:
            warnings.warn(
                f"Config key '{key}' is no longer supported and has been dropped. "
                "Review the Flask 3.x / SQLAlchemy 2.0 changelogs for replacements.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        new_key = _key_renames.get(key, key)
        new_config[new_key] = value

    # ------------------------------------------------------------------
    # Hardcoded credentials guard
    # ------------------------------------------------------------------
    _credential_keys = {
        "SECRET_KEY",
        "SQLALCHEMY_DATABASE_URI",
        "DATABASE_URL",
        "PASSWORD",
        "DB_PASSWORD",
        "API_KEY",
        "API_SECRET",
    }
    for cred_key in _credential_keys:
        if cred_key in new_config:
            val = new_config[cred_key]
            if isinstance(val, str) and not val.startswith("${") and not val.startswith("%("):
                # Attempt to pull from environment instead
                env_val = os.environ.get(cred_key)
                if env_val:
                    new_config[cred_key] = env_val
                else:
                    warnings.warn(
                        f"Config key '{cred_key}' appears to contain a hardcoded value. "
                        "# TODO: Remove hardcoded credentials and inject via environment "
                        "variables or a secrets manager.",
                        UserWarning,
                        stacklevel=2,
                    )

    # ------------------------------------------------------------------
    # SQLAlchemy 2.0: SQLALCHEMY_TRACK_MODIFICATIONS default changed
    # ------------------------------------------------------------------
    if new_config.get("SQLALCHEMY_TRACK_MODIFICATIONS") is True:
        warnings.warn(
            "SQLALCHEMY_TRACK_MODIFICATIONS=True adds overhead and is disabled "
            "by default in Flask-SQLAlchemy 3.x. Set it to False unless required.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ------------------------------------------------------------------
    # SQLAlchemy 2.0: connection URL scheme changes (e.g. postgres:// -> postgresql://)
    # ------------------------------------------------------------------
    db_uri = new_config.get("SQLALCHEMY_DATABASE_URI", "")
    if isinstance(db_uri, str) and db_uri.startswith("postgres://"):
        new_config["SQLALCHEMY_DATABASE_URI"] = db_uri.replace(
            "postgres://", "postgresql://", 1
        )
        warnings.warn(
            "SQLALCHEMY_DATABASE_URI: 'postgres://' scheme is deprecated in "
            "SQLAlchemy 1.4+ and removed in 2.0. Automatically rewritten to "
            "'postgresql://'.",
            DeprecationWarning,
            stacklevel=2,
        )

    # TODO: If using MySQL, verify the driver string (e.g. mysql+pymysql://)
    #       is compatible with SQLAlchemy 2.0.

    return new_config


# ---------------------------------------------------------------------------
# Dockerfile / CI reminder  (non-code, emitted as warnings at import time)
# ---------------------------------------------------------------------------

# TODO: Add a Dockerfile targeting Python 3.12 or 3.13.
#       Recommended base image: python:3.12-slim
#       See top upgrade targets in the project spec.

# TODO: Add a CI/CD pipeline (e.g. GitHub Actions) that includes:
#       - dependency vulnerability scanning (e.g. pip-audit, safety)
#       - automated tests on Python 3.12 and 3.13
#       See top upgrade targets in the project spec.


# ---------------------------------------------------------------------------
# Convenience: print migration checklist
# ---------------------------------------------------------------------------

def print_migration_checklist() -> None:
    """Print a human-readable checklist of manual migration steps."""
    checklist = """
=============================================================
  Migration Checklist: Flask 1.x->3.1 / SQLAlchemy 1.3->2.0
=============================================================

Python runtime
  [ ] Upgrade runtime from Python 3.8 to Python 3.12 or 3.13
  [ ] Update .python-version / pyproject.python_requires accordingly

Flask 1.x -> 3.1
  [ ] Replace module-level `app = Flask(__name__)` with application factory
  [ ] Remove all @app.before_first_request decorators (removed in Flask 2.x)
  [ ] Remove flask.ext.* imports; use flask_<name> directly
  [ ] Remove JSON_SORT_KEYS, JSONIFY_PRETTYPRINT_REGULAR config keys
  [ ] Replace JSON_SORT_KEYS with app.json.sort_keys
  [ ] Replace JSONIFY_MIMETYPE with app.json.mimetype
  [ ] Remove direct use of flask._app_ctx_stack / _request_ctx_stack
  [ ] Audit all error handlers for changed signature requirements
  [ ] Review Werkzeug 2.x/3.x breaking changes (Flask dependency)
      https://werkzeug.palletsprojects.com/en/3.0.x/changes/

SQLAlchemy 1.3 -> 2.0
  [ ] Replace declarative_base() with DeclarativeBase subclass
  [ ] Replace session.query(Model).filter(...) with select(Model).where(...)
  [ ] Replace session.query(Model).get(pk) with session.get(Model, pk)
  [ ] Remove future=True from create_engine() calls
  [ ] Remove convert_unicode=True from create_engine() calls
  [ ] Replace classical mapper() with registry.map_imperatively()
  [ ] Replace autocommit=True sessions with explicit transaction management
  [ ] Rewrite 'postgres://' URIs to 'postgresql://'
  [ ] Enable SQLALCHEMY_TRACK_MODIFICATIONS=False

Security / credentials
  [ ] Remove all hardcoded credentials from config files and source code
  [ ] Inject secrets via environment variables or a secrets manager

Containerisation & CI/CD
  [ ] Add Dockerfile (python:3.12-slim base recommended)
  [ ] Add CI/CD pipeline with pip-audit / safety vulnerability scanning
  [ ] Pin dependencies in requirements.txt / pyproject.toml

Documentation
  [ ] Update README runtime/version references
  [ ] Update setup/installation guides
  [ ] Update architecture docs to reflect application factory pattern
  [ ] Update contribution guidelines
  [ ] Remove references to deprecated components
=============================================================
"""
    print(checklist)


if __name__ == "__main__":
    print_migration_checklist()