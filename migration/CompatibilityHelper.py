# migration_shim.py
# Compatibility shim for Flask 1.x -> 3.1 and SQLAlchemy 1.3 -> 2.0 migration
# Python 3.8 -> 3.12/3.13 upgrade helper
#
# Usage: import this module early in your application to apply shims,
# or run directly to perform config migration:
#   python migration_shim.py --migrate-config <old_config.py> <new_config.py>

from __future__ import annotations

import importlib
import logging
import os
import sys
import warnings
from typing import Any, Callable, Dict, Optional, Type

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Python version guard
# ---------------------------------------------------------------------------

if sys.version_info < (3, 12):
    warnings.warn(
        "This project targets Python 3.12 or 3.13. "
        f"You are running Python {sys.version}. "
        "Please upgrade your Python runtime.",
        DeprecationWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# Flask compatibility shims  (Flask 1.x -> 3.x)
# ---------------------------------------------------------------------------

try:
    import flask as _flask
    from flask import Flask

    _FLASK_MAJOR = int(_flask.__version__.split(".")[0])

    # ------------------------------------------------------------------
    # Flask 1.x used flask.json.jsonify / flask.json.dumps backed by
    # simplejson; Flask 3.x ships its own json provider system.
    # Re-export a stable surface so call-sites don't need to change.
    # ------------------------------------------------------------------
    try:
        from flask import json as flask_json  # noqa: F401 – re-export
    except ImportError:
        flask_json = None  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # flask.ext.* namespace was removed in Flask 1.0 and is definitely
    # absent in Flask 3.x.  Provide a clear error rather than an
    # AttributeError deep in user code.
    # ------------------------------------------------------------------
    class _FlaskExtShim:
        """Raises an informative ImportError for any flask.ext.* import."""

        def __getattr__(self, name: str) -> Any:
            raise ImportError(
                f"flask.ext.{name} is not available in Flask 3.x. "
                f"Import the extension directly (e.g. 'import flask_{name}')."
            )

    # Only patch if the attribute is missing (Flask 3 never had it)
    if not hasattr(_flask, "ext"):
        _flask.ext = _FlaskExtShim()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Application factory helper
    # Flask 3.x strongly recommends the application factory pattern.
    # This helper wraps a legacy "app = Flask(__name__)" module so it
    # can be used as a factory without rewriting the module immediately.
    # ------------------------------------------------------------------
    def create_app_from_legacy_module(
        module_path: str,
        app_attr: str = "app",
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> "Flask":
        """
        Import *module_path*, retrieve the Flask instance named *app_attr*,
        apply optional *config_overrides*, and return it.

        This is a transitional shim.  Migrate to a proper factory function
        (``create_app()``) as described in the Flask 3.x docs.

        # TODO (Flask 3.x migration): Replace this shim with a native
        #   application factory function in your package's __init__.py or
        #   app.py.  See https://flask.palletsprojects.com/en/3.0.x/patterns/appfactories/
        """
        mod = importlib.import_module(module_path)
        app: Flask = getattr(mod, app_attr)
        if not isinstance(app, Flask):
            raise TypeError(
                f"{module_path}.{app_attr} is not a Flask instance "
                f"(got {type(app)!r})."
            )
        if config_overrides:
            app.config.update(config_overrides)
        return app

    # ------------------------------------------------------------------
    # Flask 2.x removed before_first_request; Flask 3.x has no shim.
    # Provide a decorator that registers the callback via with app.app_context().
    # ------------------------------------------------------------------
    def before_first_request_shim(app: "Flask") -> Callable:
        """
        Decorator replacement for the removed ``@app.before_first_request``.

        Usage::

            @before_first_request_shim(app)
            def setup():
                ...

        # TODO (Flask 3.x migration): Replace usages of @app.before_first_request
        #   with explicit initialisation inside your application factory or
        #   use Flask's ``with app.app_context():`` block at startup.
        #   See https://flask.palletsprojects.com/en/3.0.x/api/#flask.Flask.before_request
        """
        _called = False

        def decorator(fn: Callable) -> Callable:
            @app.before_request
            def _wrapper() -> None:
                nonlocal _called
                if not _called:
                    _called = True
                    fn()

            return fn

        return decorator

    # ------------------------------------------------------------------
    # Flask 3.x removed flask.signals (blinker is now a hard dependency).
    # Provide a safe accessor.
    # ------------------------------------------------------------------
    def get_signal(name: str) -> Any:
        """
        Return a blinker Signal by name from flask.signals.

        # TODO (Flask 3.x migration): Ensure 'blinker' is listed in your
        #   requirements.txt / pyproject.toml — it is now a mandatory
        #   dependency of Flask 3.x.
        """
        try:
            from flask import signals as _signals  # noqa: PLC0415
            return getattr(_signals, name)
        except (ImportError, AttributeError) as exc:
            raise ImportError(
                f"Signal '{name}' not found in flask.signals. "
                "Ensure blinker>=1.6 is installed."
            ) from exc

    # ------------------------------------------------------------------
    # Werkzeug 3.x (bundled with Flask 3.x) removed several helpers.
    # ------------------------------------------------------------------
    try:
        # Removed in Werkzeug 2.1 — provide a shim
        from werkzeug.urls import url_encode  # noqa: F401
    except ImportError:
        try:
            from urllib.parse import urlencode as url_encode  # noqa: F401
        except ImportError:
            url_encode = None  # type: ignore[assignment]
        # TODO (Werkzeug/Flask 3.x migration): Replace all usages of
        #   werkzeug.urls.url_encode with urllib.parse.urlencode.

    try:
        from werkzeug.urls import url_decode  # noqa: F401
    except ImportError:
        try:
            from urllib.parse import parse_qs as url_decode  # noqa: F401
        except ImportError:
            url_decode = None  # type: ignore[assignment]
        # TODO (Werkzeug/Flask 3.x migration): Replace all usages of
        #   werkzeug.urls.url_decode with urllib.parse.parse_qs.

    logger.debug("Flask %s shims applied.", _flask.__version__)

except ImportError:
    warnings.warn(
        "Flask is not installed. Flask shims were not applied.",
        ImportWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# SQLAlchemy compatibility shims  (1.3 -> 2.0)
# ---------------------------------------------------------------------------

try:
    import sqlalchemy as _sa

    _SA_MAJOR = int(_sa.__version__.split(".")[0])

    # ------------------------------------------------------------------
    # Legacy Query API shim
    # SQLAlchemy 2.0 removed Session.query().  Provide a thin wrapper
    # that delegates to the new select() + Session.execute() pattern.
    # ------------------------------------------------------------------
    def legacy_query(session: Any, model: Type) -> Any:
        """
        Compatibility wrapper for ``session.query(Model)``.

        Returns a SQLAlchemy 2.x ``Select`` statement pre-configured for
        *model* so that callers can chain ``.filter()`` / ``.all()`` etc.

        .. warning::
            This shim covers only the most common patterns.  Complex
            ``session.query()`` chains **must** be migrated manually.

        # TODO (SQLAlchemy 2.0 migration): Replace all session.query(Model)
        #   usages with:
        #       from sqlalchemy import select
        #       stmt = select(Model).where(...)
        #       results = session.execute(stmt).scalars().all()
        #   See https://docs.sqlalchemy.org/en/20/orm/queryguide/
        """
        from sqlalchemy import select  # noqa: PLC0415

        class _LegacyQueryShim:
            def __init__(self, stmt: Any, _session: Any) -> None:
                self._stmt = stmt
                self._session = _session

            def filter(self, *criteria: Any) -> "_LegacyQueryShim":
                self._stmt = self._stmt.where(*criteria)
                return self

            def filter_by(self, **kwargs: Any) -> "_LegacyQueryShim":
                for key, value in kwargs.items():
                    self._stmt = self._stmt.where(
                        getattr(model, key) == value
                    )
                return self

            def order_by(self, *clauses: Any) -> "_LegacyQueryShim":
                self._stmt = self._stmt.order_by(*clauses)
                return self

            def limit(self, n: int) -> "_LegacyQueryShim":
                self._stmt = self._stmt.limit(n)
                return self

            def offset(self, n: int) -> "_LegacyQueryShim":
                self._stmt = self._stmt.offset(n)
                return self

            def all(self) -> list:
                return self._session.execute(self._stmt).scalars().all()

            def first(self) -> Any:
                return self._session.execute(self._stmt).scalars().first()

            def one(self) -> Any:
                return self._session.execute(self._stmt).scalars().one()

            def one_or_none(self) -> Any:
                return (
                    self._session.execute(self._stmt).scalars().one_or_none()
                )

            def count(self) -> int:
                from sqlalchemy import func, select as _select  # noqa: PLC0415

                count_stmt = _select(func.count()).select_from(
                    self._stmt.subquery()
                )
                return self._session.execute(count_stmt).scalar_one()

            def get(self, pk: Any) -> Any:
                # TODO (SQLAlchemy 2.0 migration): Replace .get(pk) with
                #   session.get(Model, pk)
                return self._session.get(model, pk)

        return _LegacyQueryShim(select(model), session)

    # ------------------------------------------------------------------
    # Engine creation shim
    # SQLAlchemy 2.0 deprecated create_engine keyword arguments such as
    # convert_unicode and encoding.  Strip them silently with a warning.
    # ------------------------------------------------------------------
    _REMOVED_ENGINE_KWARGS = frozenset(
        {
            "convert_unicode",
            "encoding",
            "implicit_returning",  # moved to dialect level
        }
    )

    def create_engine_compat(url: str, **kwargs: Any) -> Any:
        """
        Drop-in replacement for ``sqlalchemy.create_engine`` that removes
        keyword arguments that were valid in 1.3 but raise errors in 2.0.

        # TODO (SQLAlchemy 2.0 migration): After migrating all call-sites,
        #   replace create_engine_compat(...) with sqlalchemy.create_engine(...)
        #   directly and remove this shim.
        """
        from sqlalchemy import create_engine  # noqa: PLC0415

        removed = _REMOVED_ENGINE_KWARGS & kwargs.keys()
        if removed:
            warnings.warn(
                f"create_engine_compat: removing deprecated kwargs {removed}. "
                "These are not supported in SQLAlchemy 2.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            for key in removed:
                kwargs.pop(key)
        return create_engine(url, **kwargs)

    # ------------------------------------------------------------------
    # Declarative base shim
    # SQLAlchemy 1.3: from sqlalchemy.ext.declarative import declarative_base
    # SQLAlchemy 2.0: from sqlalchemy.orm import DeclarativeBase (class-based)
    #                 or sqlalchemy.orm.declarative_base() (still available
    #                 but emits a deprecation warning in 2.x).
    # ------------------------------------------------------------------
    try:
        # 2.0 path
        from sqlalchemy.orm import DeclarativeBase as _DeclarativeBase  # noqa: F401

        class Base(_DeclarativeBase):
            """
            Project-wide declarative base compatible with SQLAlchemy 2.0.

            # TODO (SQLAlchemy 2.0 migration): Replace all occurrences of
            #   ``Base = declarative_base()`` (from sqlalchemy.ext.declarative)
            #   with an import of this Base class from migration_shim, or
            #   define your own subclass of sqlalchemy.orm.DeclarativeBase.
            """

    except ImportError:
        # Fallback for SQLAlchemy 1.4 transitional mode
        from sqlalchemy.orm import declarative_base as _declarative_base  # type: ignore[no-redef]

        Base = _declarative_base()  # type: ignore[assignment,misc]
        # TODO (SQLAlchemy 2.0 migration): Upgrade to SQLAlchemy 2.x and
        #   switch to the class-based DeclarativeBase API.

    # ------------------------------------------------------------------
    # Session factory shim
    # Encourage use of sessionmaker / Session context manager pattern.
    # ------------------------------------------------------------------
    def make_session_factory(engine: Any, **kwargs: Any) -> Any:
        """
        Return a ``sessionmaker`` bound to *engine*.

        In SQLAlchemy 2.0 the recommended pattern is::

            with Session(engine) as session:
                ...

        # TODO (SQLAlchemy 2.0 migration): Migrate long-lived scoped_session
        #   usages to the new Session context-manager pattern or to
        #   async_sessionmaker if adopting asyncio.
        #   See https://docs.sqlalchemy.org/en/20/orm/session_basics.html
        """
        from sqlalchemy.orm import sessionmaker  # noqa: PLC0415

        return sessionmaker(bind=engine, **kwargs)

    # ------------------------------------------------------------------
    # Column type aliases removed or moved in SQLAlchemy 2.0
    # ------------------------------------------------------------------
    try:
        from sqlalchemy import String, Integer, Boolean, DateTime, Text, Float  # noqa: F401
    except ImportError:
        pass  # Should never happen; guard for unusual environments.

    # TODO (SQLAlchemy 2.0 migration): Replace sqlalchemy.types.* imports
    #   with sqlalchemy.* top-level imports where applicable.

    logger.debug("SQLAlchemy %s shims applied.", _sa.__version__)

except ImportError:
    warnings.warn(
        "SQLAlchemy is not installed. SQLAlchemy shims were not applied.",
        ImportWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# Configuration migration helper
# ---------------------------------------------------------------------------

# Mapping of old config keys -> new config keys (rename only)
_CONFIG_KEY_RENAMES: Dict[str, str] = {
    # Flask 1.x -> 3.x renames
    "FLASK_ENV": "FLASK_DEBUG",          # FLASK_ENV removed in Flask 3.x
    "JSON_SORT_KEYS": "JSON_SORT_KEYS",  # still valid but via app.json.sort_keys
    # SQLAlchemy 1.3 -> 2.0 renames (SQLAlchemy-Flask / Flask-SQLAlchemy)
    "SQLALCHEMY_TRACK_MODIFICATIONS": None,  # None = key should be removed
}

# Config keys that contained hardcoded credentials and must be moved to env vars
_CREDENTIAL_KEYS = frozenset(
    {
        "SECRET_KEY",
        "SQLALCHEMY_DATABASE_URI",
        "DATABASE_URL",
        "DB_PASSWORD",
        "DB_USER",
        "DB_HOST",
        "MAIL_PASSWORD",
        "API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ACCESS_KEY_ID",
    }
)


def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform an old-style flat config dict to the new format.

    Handles:
    - Renamed keys (Flask 3.x, SQLAlchemy 2.0)
    - Removed keys (emits warnings)
    - Credential keys (emits warnings and suggests env-var equivalents)

    Returns the migrated config dict.  The caller is responsible for
    persisting the result.
    """
    new_config: Dict[str, Any] = {}

    for key, value in old_config.items():
        # Handle credential keys
        if key in _CREDENTIAL_KEYS:
            env_var = key.upper()
            warnings.warn(
                f"Config key '{key}' appears to contain a credential or "
                f"sensitive value. Move it to an environment variable: "
                f"os.environ['{env_var}'] and load it with "
                f"os.environ.get('{env_var}'). "
                "Hardcoded credentials are a security risk.",
                UserWarning,
                stacklevel=2,
            )
            # Still include in migrated config so the app doesn't break,
            # but flag it clearly.
            # TODO (security): Remove hardcoded credential '{key}' from config
            #   and load from environment variable '{env_var}' or a secrets
            #   manager.  See project security guidelines.
            new_config[key] = value
            continue

        if key in _CONFIG_KEY_RENAMES:
            new_key = _CONFIG_KEY_RENAMES[key]
            if new_key is None:
                warnings.warn(
                    f"Config key '{key}' has been removed in the new stack "
                    "and will be dropped from the migrated config.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                # TODO (Flask 3.x / SQLAlchemy 2.0 migration): Verify that
                #   removing '{key}' does not affect application behaviour.
                continue
            if new_key != key:
                warnings.warn(
                    f"Config key '{key}' has been renamed to '{new_key}'.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            new_config[new_key] = value
        else:
            new_config[key] = value

    # ------------------------------------------------------------------
    # Flask 3.x: FLASK_ENV is gone; set DEBUG based on its old value.
    # ------------------------------------------------------------------
    if "FLASK_ENV" in old_config:
        old_env = old_config["FLASK_ENV"]
        new_config["FLASK_DEBUG"] = old_env == "development"
        # TODO (Flask 3.x migration): Remove FLASK_ENV from all environment
        #   files (.env, docker-compose, CI) and replace with FLASK_DEBUG=1
        #   for development environments.

    # ------------------------------------------------------------------
    # Flask 3.x: JSON configuration moved to app.json provider.
    # ------------------------------------------------------------------
    if "JSON_AS_ASCII" in old_config:
        warnings.warn(
            "JSON_AS_ASCII is no longer a top-level config key in Flask 3.x. "
            "Set app.json.ensure_ascii = False instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # TODO (Flask 3.x migration): Replace app.config['JSON_AS_ASCII'] with
        #   app.json.ensure_ascii = <value> inside your application factory.

    # ------------------------------------------------------------------
    # SQLAlchemy 2.0: SQLALCHEMY_DATABASE_URI should use the new dialect
    # strings where applicable (e.g. postgresql+psycopg instead of
    # postgresql+psycopg2 for async usage).
    # ------------------------------------------------------------------
    db_uri = new_config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri and "postgres://" in db_uri:
        new_config["SQLALCHEMY_DATABASE_URI"] = db_uri.replace(
            "postgres://", "postgresql+psycopg2://", 1
        )
        warnings.warn(
            "SQLALCHEMY_DATABASE_URI: replaced deprecated 'postgres://' "
            "scheme with 'postgresql+psycopg2://'.",
            DeprecationWarning,
            stacklevel=2,
        )
        # TODO (SQLAlchemy 2.0 migration): Consider migrating to the
        #   'postgresql+psycopg' (psycopg3) driver for full async support.

    return new_config


def migrate_config_file(src_path: str, dst_path: str) -> None:
    """
    Read a Python config file at *src_path*, apply :func:`migrate_config`,
    and write the result as a new Python config file to *dst_path*.

    Only handles simple ``KEY = VALUE`` assignments at module level.
    Complex config files (classes, conditionals) require manual review.

    # TODO (manual): Review the generated config file at *dst_path* for
    #   correctness before deploying.  This function handles only simple
    #   key=value assignments.
    """
    import ast  # noqa: PLC0415
    import re   # noqa: PLC0415

    with open(src_path, "r", encoding="utf-8") as fh:
        source = fh.read()

    # Parse top-level assignments only
    old_config: Dict[str, Any] = {}
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        try:
                            old_config[target.id] = ast.literal_eval(node.value)
                        except (ValueError, TypeError):
                            # TODO (manual): Config key '{target.id}' has a
                            #   non-literal value and could not be migrated
                            #   automatically.  Review manually.
                            logger.warning(
                                "Skipping non-literal config key: %s", target.id
                            )
    except SyntaxError as exc:
        raise ValueError(
            f"Could not parse config file {src_path}: {exc}"
        ) from exc

    new_config = migrate_config(old_config)

    lines = [
        "# Auto-generated by migration_shim.py — review before use.",
        "# TODO (manual): Verify all values, especially credentials,",
        "#   before deploying this config file.",
        "",
    ]
    for key, value in new_config.items():
        lines.append(f"{key} = {value!r}")

    with open(dst_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    logger.info("Config migrated: %s -> %s", src_path, dst_path)


# ---------------------------------------------------------------------------
# Environment variable helpers
# (support removing hardcoded credentials — see upgrade target)
# ---------------------------------------------------------------------------

def require_env(name: str, default: Optional[str] = None) -> str:
    """
    Return the value of environment variable *name*.

    Raises ``RuntimeError`` if the variable is not set and no *default*
    is provided.

    # TODO (security): Ensure all sensitive values (SECRET_KEY,
    #   SQLALCHEMY_DATABASE_URI, etc.) are supplied via environment
    #   variables or a secrets manager, not hardcoded in source.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            "Set it in your shell, .env file, or secrets manager."
        )
    return value


def load_dotenv_if_available(dotenv_path: str = ".env") -> None:
    """
    Load a .env file using python-dotenv if available.

    # TODO (environment): Add python-dotenv to requirements.txt if not
    #   already present:  pip install python-dotenv
    #   Then call load_dotenv_if_available() at the top of your
    #   application entry point before reading any config.
    """
    try:
        from dotenv import load_dotenv  # noqa: PLC0415

        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
            logger.debug("Loaded environment from %s", dotenv_path)
        else:
            logger.debug(".env file not found at %s; skipping.", dotenv_path)
    except ImportError:
        warnings.warn(
            "python-dotenv is not installed; .env file was not loaded. "
            "Install it with: pip install python-dotenv",
            ImportWarning,
            stacklevel=2,
        )


# ---------------------------------------------------------------------------
# Flask-SQLAlchemy integration shim
# ---------------------------------------------------------------------------

def init_flask_sqlalchemy(app: Any, db: Any) -> None:
    """
    Initialise Flask-SQLAlchemy *db* with *app* using the application
    factory pattern required by Flask 3.x.

    Replaces the legacy pattern of passing ``app`` directly to
    ``SQLAlchemy(app)``.

    # TODO (Flask 3.x / SQLAlchemy 2.0 migration): Ensure you are using
    #   Flask-SQLAlchemy >= 3.0 which supports SQLAlchemy 2.0.
    #   Update requirements.txt: Flask-SQLAlchemy>=3.0
    """
    if not hasattr(db, "init_app"):
        raise TypeError(
            "db does not have an init_app method. "
            "Ensure Flask-SQLAlchemy >= 3.0 is installed."
        )
    db.init_app(app)
    logger.debug("Flask-SQLAlchemy initialised via init_app().")


# ---------------------------------------------------------------------------
# CLI entry point for config file migration
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(
        description="Migration helper for Flask 1.x->3.x and SQLAlchemy 1.3->2.0 upgrade."
    )
    subparsers = parser.add_subparsers(dest="command")

    migrate_cmd = subparsers.add_parser(
        "migrate-config",
        help="Migrate a Python config file to the new format.",
    )
    migrate_cmd.add_argument("src", help="Path to the old config file.")
    migrate_cmd.add_argument("dst", help="Path for the new config file.")

    check_cmd = subparsers.add_parser(
        "check-env",
        help="Check that required environment variables are set.",
    )
    check_cmd.add_argument(
        "vars",
        nargs="+",
        metavar="VAR",
        help="Environment variable names to check.",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.command == "migrate-config":
        migrate_config_file(args.src, args.dst)
        print(f"Config migrated: {args.src} -> {args.dst}")
        print("Review the output file before deploying.")

    elif args.command == "check-env":
        missing = [v for v in args.vars if not os.environ.get(v)]
        if missing:
            print("Missing environment variables:")
            for v in missing:
                print(f"  {v}")
            sys.exit(1)
        else:
            print("All required environment variables are set.")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    _cli()