# migration_shim.py
# Compatibility shim for Flask 1.x -> 3.1 and SQLAlchemy 1.3 -> 2.0 migration
# Python 3.8 -> 3.12/3.13 upgrade helper
#
# Usage: import this module early in your application bootstrap to apply shims,
# or run it directly as a script to perform config migration:
#   python migration_shim.py --migrate-config <old_config.py> --output <new_config.py>

from __future__ import annotations

import importlib
import logging
import os
import sys
import types
import warnings
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Python version guard
# ---------------------------------------------------------------------------

if sys.version_info < (3, 10):
    warnings.warn(
        "This shim targets Python 3.12/3.13. You are running "
        f"{sys.version}. Upgrade Python before deploying to production.",
        DeprecationWarning,
        stacklevel=2,
    )

# ===========================================================================
# SECTION 1 — Flask 1.x → 3.1 compatibility shims
# ===========================================================================

# ---------------------------------------------------------------------------
# 1a. Application factory helper
#     Flask 3.x strongly recommends the application factory pattern.
#     If your project calls Flask(__name__) at module level, wrap it here.
# ---------------------------------------------------------------------------

def create_app_factory(config_object: Optional[Any] = None) -> "flask.Flask":
    """
    Drop-in application factory compatible with Flask 3.1.

    Replace any module-level ``app = Flask(__name__)`` with::

        from migration_shim import create_app_factory
        app = create_app_factory()

    TODO: Move all ``app.route`` decorators and extension initialisation
    (db.init_app, login_manager.init_app, etc.) inside this factory.
    See Flask 3.x breaking change: application context is no longer pushed
    automatically outside of a request/app context.
    """
    try:
        import flask
    except ImportError as exc:
        raise ImportError("Flask is not installed. Run: pip install flask>=3.1") from exc

    app = flask.Flask(__name__)

    if config_object is not None:
        app.config.from_object(config_object)

    # TODO: Register blueprints here after converting route modules to blueprints.
    # TODO: Initialise extensions (SQLAlchemy, LoginManager, etc.) via init_app().

    return app


# ---------------------------------------------------------------------------
# 1b. Deprecated Flask globals / helpers
#     flask.json.jsonify, flask.escape, flask.Markup were moved or removed.
# ---------------------------------------------------------------------------

def _patch_flask_deprecated_globals() -> None:
    """
    Re-export symbols that were removed from the top-level ``flask`` namespace
    in Flask 2.x/3.x back onto the module so that existing ``from flask import X``
    statements continue to work during the transition period.

    Affected symbols:
      - flask.escape        → markupsafe.escape
      - flask.Markup        → markupsafe.Markup
      - flask._app_ctx_err_msg (removed)
    """
    try:
        import flask
        import markupsafe
    except ImportError:
        return

    if not hasattr(flask, "escape"):
        flask.escape = markupsafe.escape  # type: ignore[attr-defined]
        logger.debug("Shim applied: flask.escape -> markupsafe.escape")

    if not hasattr(flask, "Markup"):
        flask.Markup = markupsafe.Markup  # type: ignore[attr-defined]
        logger.debug("Shim applied: flask.Markup -> markupsafe.Markup")

    # TODO: Replace all ``flask.escape`` / ``flask.Markup`` usages in source
    # files with ``markupsafe.escape`` / ``markupsafe.Markup`` directly.
    # Flask 3.x breaking change: these aliases are permanently removed.


# ---------------------------------------------------------------------------
# 1c. flask.ext.* import shim (Flask 0.x/1.x extension namespace)
#     Extensions were accessed as flask.ext.sqlalchemy, etc.
# ---------------------------------------------------------------------------

class _FlaskExtShim(types.ModuleType):
    """
    Proxy module that redirects ``flask.ext.<name>`` imports to
    ``flask_<name>`` (the modern package naming convention).

    TODO: Replace every ``from flask.ext import <name>`` or
    ``import flask.ext.<name>`` in the codebase with
    ``import flask_<name>`` directly.
    Flask 1.x breaking change: flask.ext namespace was removed in Flask 1.0.
    """

    def __getattr__(self, name: str) -> types.ModuleType:
        new_name = f"flask_{name}"
        warnings.warn(
            f"flask.ext.{name} is removed. Use '{new_name}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return importlib.import_module(new_name)


def _patch_flask_ext_namespace() -> None:
    try:
        import flask
    except ImportError:
        return

    ext_module = _FlaskExtShim("flask.ext")
    sys.modules["flask.ext"] = ext_module
    flask.ext = ext_module  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 1d. Request / Response API changes
# ---------------------------------------------------------------------------

def shim_flask_request_environ(request: Any) -> Dict[str, Any]:
    """
    In Flask 3.x, ``request.environ`` access patterns are unchanged, but
    ``request.is_json`` and ``request.get_json()`` behaviour changed for
    silent error handling.

    This helper wraps ``get_json`` with the old default (silent=False).

    TODO: Audit all ``request.get_json()`` call sites. Flask 3.x breaking
    change: the default for ``force`` and ``silent`` parameters changed.
    Pass keyword arguments explicitly.
    """
    # Old behaviour: raises 400 on bad JSON by default
    return request.get_json(force=False, silent=False)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# 1e. before_first_request removal
#     Flask 3.x removed @app.before_first_request.
# ---------------------------------------------------------------------------

_before_first_request_ran: bool = False


def before_first_request_shim(app: Any, func: Callable) -> None:
    """
    Emulates the removed ``@app.before_first_request`` decorator using
    ``@app.before_request``.

    Usage::

        from migration_shim import before_first_request_shim
        before_first_request_shim(app, my_setup_function)

    TODO: Replace all ``@app.before_first_request`` decorators in the
    codebase with this helper or with explicit initialisation inside the
    application factory.
    Flask 3.x breaking change: @app.before_first_request was removed.
    """
    global _before_first_request_ran

    @app.before_request
    def _wrapper() -> None:
        global _before_first_request_ran
        if not _before_first_request_ran:
            _before_first_request_ran = True
            func()


# ===========================================================================
# SECTION 2 — SQLAlchemy 1.3 → 2.0 compatibility shims
# ===========================================================================

# ---------------------------------------------------------------------------
# 2a. Legacy Query API shim
#     SQLAlchemy 2.0 removes Session.query() in favour of select().
# ---------------------------------------------------------------------------

def legacy_query(session: Any, model_class: Any) -> Any:
    """
    Compatibility wrapper that translates the SQLAlchemy 1.3 ``session.query(Model)``
    pattern to the SQLAlchemy 2.0 ``select(Model)`` pattern.

    Returns a ``Select`` statement; call ``session.execute(...).scalars()`` on it.

    Usage::

        stmt = legacy_query(db.session, User)
        results = db.session.execute(stmt).scalars().all()

    TODO: Replace all ``session.query(Model).filter(...).all()`` call sites
    with ``session.execute(select(Model).where(...)).scalars().all()``.
    SQLAlchemy 2.0 breaking change: Query API is removed.
    """
    try:
        from sqlalchemy import select
    except ImportError as exc:
        raise ImportError(
            "SQLAlchemy is not installed. Run: pip install sqlalchemy>=2.0"
        ) from exc

    return select(model_class)


def query_filter_shim(session: Any, model_class: Any, *criterion: Any) -> Any:
    """
    Wraps the common ``session.query(Model).filter(*criterion)`` pattern.

    Returns a ``Select`` statement with WHERE clauses applied.

    TODO: Inline the ``select(Model).where(...)`` pattern directly at each
    call site for clarity. This shim is a temporary bridge only.
    SQLAlchemy 2.0 breaking change: Query.filter() is removed.
    """
    try:
        from sqlalchemy import select
    except ImportError as exc:
        raise ImportError("SQLAlchemy >= 2.0 required") from exc

    stmt = select(model_class)
    if criterion:
        stmt = stmt.where(*criterion)
    return stmt


def execute_query(session: Any, stmt: Any) -> list:
    """
    Execute a SQLAlchemy 2.0 ``select()`` statement and return a list of
    model instances, mirroring the old ``.all()`` behaviour.

    TODO: Replace direct ``.all()`` calls on Query objects with this helper
    or with ``session.execute(stmt).scalars().all()`` inline.
    SQLAlchemy 2.0 breaking change: Query.all() is removed.
    """
    return session.execute(stmt).scalars().all()


# ---------------------------------------------------------------------------
# 2b. Column type renames
# ---------------------------------------------------------------------------

def get_sqlalchemy_types() -> types.ModuleType:
    """
    Returns a namespace object exposing both old and new SQLAlchemy type names.

    SQLAlchemy 2.0 breaking changes:
      - ``sqlalchemy.orm.declarative_base()`` replaces
        ``sqlalchemy.ext.declarative.declarative_base()``
      - ``sqlalchemy.orm.DeclarativeBase`` (class-based) is the new preferred API.

    TODO: Replace ``from sqlalchemy.ext.declarative import declarative_base``
    with ``from sqlalchemy.orm import declarative_base`` (2.0 transitional) or
    subclass ``sqlalchemy.orm.DeclarativeBase`` (2.0 native style).
    """
    try:
        import sqlalchemy.orm as orm
    except ImportError as exc:
        raise ImportError("SQLAlchemy >= 2.0 required") from exc

    # Provide the old import path as an alias
    try:
        from sqlalchemy.ext.declarative import declarative_base as _old_base  # noqa: F401
    except ImportError:
        # Already removed in this SQLAlchemy version; patch it back
        import sqlalchemy.ext.declarative as _ext_decl  # type: ignore[import]
        _ext_decl.declarative_base = orm.declarative_base  # type: ignore[attr-defined]
        logger.debug(
            "Shim applied: sqlalchemy.ext.declarative.declarative_base "
            "-> sqlalchemy.orm.declarative_base"
        )

    return orm


# ---------------------------------------------------------------------------
# 2c. Session / engine creation changes
# ---------------------------------------------------------------------------

def create_engine_shim(url: str, **kwargs: Any) -> Any:
    """
    Wraps ``sqlalchemy.create_engine`` to enforce 2.0-compatible defaults:
      - ``future=True`` is the default in 2.0 (parameter removed; always on).
      - Removes the deprecated ``convert_unicode`` parameter.

    TODO: Remove ``future=True`` from any existing ``create_engine()`` calls
    (it is now the default and passing it raises a warning in 2.0).
    SQLAlchemy 2.0 breaking change: ``future`` parameter removed.
    """
    try:
        from sqlalchemy import create_engine
    except ImportError as exc:
        raise ImportError("SQLAlchemy >= 2.0 required") from exc

    # Strip deprecated kwargs silently during migration
    kwargs.pop("future", None)  # future=True is now the only mode
    kwargs.pop("convert_unicode", None)  # removed in 2.0

    # TODO: Audit connection pool settings — pool_pre_ping=True is now
    # recommended for all production deployments.
    kwargs.setdefault("pool_pre_ping", True)

    return create_engine(url, **kwargs)


def get_session_factory(engine: Any) -> Any:
    """
    Returns a ``sessionmaker`` bound to the provided engine using 2.0 conventions.

    TODO: Replace ``scoped_session(sessionmaker(...))`` patterns with
    ``async_sessionmaker`` if migrating to async, or keep synchronous
    ``sessionmaker`` with ``autobegin=True`` (the new default).
    SQLAlchemy 2.0 breaking change: autocommit mode removed from Session.
    """
    try:
        from sqlalchemy.orm import sessionmaker
    except ImportError as exc:
        raise ImportError("SQLAlchemy >= 2.0 required") from exc

    # autocommit=True is removed in 2.0; use explicit transaction management
    # TODO: Audit all session.commit() / session.rollback() call sites to
    # ensure explicit transaction boundaries are set.
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ---------------------------------------------------------------------------
# 2d. Relationship loading — lazy="dynamic" removed in 2.0
# ---------------------------------------------------------------------------

def warn_dynamic_relationships() -> None:
    """
    Emits a warning about ``lazy='dynamic'`` relationships which are removed
    in SQLAlchemy 2.0.

    TODO: Replace all ``relationship(..., lazy='dynamic')`` definitions with
    ``lazy='select'`` (default) or use ``write_only=True`` for large
    collections.
    SQLAlchemy 2.0 breaking change: lazy='dynamic' is removed.
    """
    warnings.warn(
        "lazy='dynamic' relationships are removed in SQLAlchemy 2.0. "
        "Replace with lazy='select' or write_only=True.",
        DeprecationWarning,
        stacklevel=2,
    )


# ===========================================================================
# SECTION 3 — Environment-based secrets management shim
# ===========================================================================

# ---------------------------------------------------------------------------
# 3a. Hardcoded credential detection and replacement helpers
# ---------------------------------------------------------------------------

_SENSITIVE_KEYS = frozenset({
    "SECRET_KEY",
    "DATABASE_URL",
    "DB_PASSWORD",
    "DB_USER",
    "DB_HOST",
    "SQLALCHEMY_DATABASE_URI",
    "PASSWORD",
    "API_KEY",
    "JWT_SECRET",
})


def get_secret(key: str, default: Optional[str] = None) -> str:
    """
    Retrieves a configuration secret from environment variables.

    Replaces hardcoded credential patterns such as::

        app.config['SECRET_KEY'] = 'hardcoded-value'

    with::

        app.config['SECRET_KEY'] = get_secret('SECRET_KEY')

    TODO: Audit all ``app.config[...]`` assignments and ``os.environ.get(...)``
    calls for hardcoded credentials. Move all secrets to a ``.env`` file
    (excluded from version control) or a secrets manager.
    Breaking change: hardcoded credentials must be removed before deployment.
    """
    value = os.environ.get(key, default)
    if value is None:
        raise EnvironmentError(
            f"Required secret '{key}' is not set in the environment. "
            f"Add it to your .env file or environment before starting the application."
        )
    return value


def build_database_url() -> str:
    """
    Constructs a SQLAlchemy 2.0-compatible database URL from environment variables,
    replacing any hardcoded ``SQLALCHEMY_DATABASE_URI`` values.

    Expected environment variables:
      DB_DRIVER   (e.g. postgresql+psycopg2)
      DB_USER
      DB_PASSWORD
      DB_HOST
      DB_PORT     (default: 5432)
      DB_NAME

    TODO: Set these variables in your deployment environment or .env file.
    TODO: If using SQLite for development, set DATABASE_URL=sqlite:///dev.db
    and bypass this function.
    """
    driver = os.environ.get("DB_DRIVER", "postgresql+psycopg2")
    user = get_secret("DB_USER")
    password = get_secret("DB_PASSWORD")
    host = get_secret("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = get_secret("DB_NAME")
    return f"{driver}://{user}:{password}@{host}:{port}/{name}"


# ===========================================================================
# SECTION 4 — Config format migration
# ===========================================================================

def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a Flask 1.x / SQLAlchemy 1.3 config dictionary into a
    Flask 3.1 / SQLAlchemy 2.0 compatible config dictionary.

    Parameters
    ----------
    old_config : dict
        The old configuration dictionary (e.g. loaded from config.py).

    Returns
    -------
    dict
        A new configuration dictionary with deprecated keys replaced.

    Breaking changes addressed:
      - SQLALCHEMY_TRACK_MODIFICATIONS default changed (must be explicit).
      - SQLALCHEMY_DATABASE_URI should come from environment.
      - SECRET_KEY must not be hardcoded.
      - PROPAGATE_EXCEPTIONS behaviour changed in Flask 3.x.
      - JSON_SORT_KEYS removed (use app.json.sort_keys).
      - JSONIFY_PRETTYPRINT_REGULAR removed.
      - JSONIFY_MIMETYPE removed (use app.json.mimetype).
      - TEMPLATES_AUTO_RELOAD moved to app.jinja_env.auto_reload.
    """
    new_config: Dict[str, Any] = {}

    for key, value in old_config.items():

        # --- Removed Flask config keys ---
        if key == "JSON_SORT_KEYS":
            # TODO: Set app.json.sort_keys = <value> after app creation.
            # Flask 3.x breaking change: JSON_SORT_KEYS config key removed.
            logger.warning(
                "Config key JSON_SORT_KEYS is removed in Flask 3.x. "
                "Set app.json.sort_keys = %r after app creation instead.", value
            )
            continue

        if key == "JSONIFY_PRETTYPRINT_REGULAR":
            # TODO: Set app.json.compact = not <value> after app creation.
            # Flask 3.x breaking change: JSONIFY_PRETTYPRINT_REGULAR removed.
            logger.warning(
                "Config key JSONIFY_PRETTYPRINT_REGULAR is removed in Flask 3.x. "
                "Set app.json.compact = %r after app creation instead.", not value
            )
            continue

        if key == "JSONIFY_MIMETYPE":
            # TODO: Set app.json.mimetype = <value> after app creation.
            # Flask 3.x breaking change: JSONIFY_MIMETYPE removed.
            logger.warning(
                "Config key JSONIFY_MIMETYPE is removed in Flask 3.x. "
                "Set app.json.mimetype = %r after app creation instead.", value
            )
            continue

        if key == "TEMPLATES_AUTO_RELOAD":
            # TODO: Set app.jinja_env.auto_reload = <value> after app creation.
            # Flask 3.x breaking change: TEMPLATES_AUTO_RELOAD removed.
            logger.warning(
                "Config key TEMPLATES_AUTO_RELOAD is removed in Flask 3.x. "
                "Set app.jinja_env.auto_reload = %r after app creation instead.", value
            )
            continue

        # --- SQLAlchemy config migration ---
        if key == "SQLALCHEMY_DATABASE_URI":
            env_val = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
            if env_val:
                new_config[key] = env_val
            else:
                # TODO: Move SQLALCHEMY_DATABASE_URI to environment variable DATABASE_URL.
                # Breaking change: hardcoded database URIs must be replaced with env vars.
                logger.warning(
                    "SQLALCHEMY_DATABASE_URI is hardcoded. "
                    "Set DATABASE_URL environment variable instead."
                )
                new_config[key] = value
            continue

        if key == "SQLALCHEMY_TRACK_MODIFICATIONS":
            # SQLAlchemy 2.0 / Flask-SQLAlchemy 3.x: this must be False.
            if value is True:
                logger.warning(
                    "SQLALCHEMY_TRACK_MODIFICATIONS=True causes significant overhead "
                    "and is unsupported in SQLAlchemy 2.0. Forcing to False."
                )
            new_config[key] = False
            continue

        # --- Secret key migration ---
        if key == "SECRET_KEY":
            env_val = os.environ.get("SECRET_KEY")
            if env_val:
                new_config[key] = env_val
            else:
                # TODO: Set SECRET_KEY as an environment variable.
                # Breaking change: hardcoded SECRET_KEY is a security vulnerability.
                logger.warning(
                    "SECRET_KEY is hardcoded in config. "
                    "Set the SECRET_KEY environment variable instead."
                )
                new_config[key] = value
            continue

        # --- Pass-through for unrecognised keys ---
        new_config[key] = value

    # Ensure SQLALCHEMY_TRACK_MODIFICATIONS is always present and False
    new_config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # TODO: Add SESSION_COOKIE_SAMESITE and SESSION_COOKIE_SECURE for
    # Flask 3.x security defaults if not already present.
    new_config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    new_config.setdefault("SESSION_COOKIE_SECURE", True)

    return new_config


# ===========================================================================
# SECTION 5 — Flask-SQLAlchemy extension shim
# ===========================================================================

def get_flask_sqlalchemy_db() -> Any:
    """
    Returns a Flask-SQLAlchemy ``SQLAlchemy`` instance configured for
    SQLAlchemy 2.0 compatibility.

    TODO: Ensure flask-sqlalchemy>=3.0 is installed (required for
    SQLAlchemy 2.0 support). Run: pip install flask-sqlalchemy>=3.0
    Flask-SQLAlchemy 3.x breaking change: db.session.query() is removed;
    use db.session.execute(select(...)) instead.
    """
    try:
        from flask_sqlalchemy import SQLAlchemy
    except ImportError as exc:
        raise ImportError(
            "flask-sqlalchemy is not installed or is too old. "
            "Run: pip install flask-sqlalchemy>=3.0"
        ) from exc

    # TODO: Pass model_class=db.Model subclassing DeclarativeBase for
    # Flask-SQLAlchemy 3.x native style.
    db = SQLAlchemy()
    return db


# ===========================================================================
# SECTION 6 — Python 3.8 → 3.12/3.13 compatibility helpers
# ===========================================================================

# ---------------------------------------------------------------------------
# 6a. Removed / changed stdlib APIs
# ---------------------------------------------------------------------------

def shim_importlib_resources() -> None:
    """
    Python 3.9+ changed ``importlib.resources`` API.
    ``importlib.resources.open_text`` and ``open_binary`` are deprecated in 3.11
    and removed in 3.13.

    TODO: Replace ``importlib.resources.open_text(package, resource)`` with
    ``importlib.resources.files(package).joinpath(resource).open('r')``.
    Python 3.13 breaking change: open_text / open_binary removed.
    """
    import importlib.resources as _ir

    if not hasattr(_ir, "open_text"):
        # Already removed; provide a shim
        def open_text(package: str, resource: str, encoding: str = "utf-8", errors: str = "strict"):  # noqa: E501
            return _ir.files(package).joinpath(resource).open("r", encoding=encoding, errors=errors)  # type: ignore[attr-defined]

        def open_binary(package: str, resource: str):
            return _ir.files(package).joinpath(resource).open("rb")  # type: ignore[attr-defined]

        _ir.open_text = open_text  # type: ignore[attr-defined]
        _ir.open_binary = open_binary  # type: ignore[attr-defined]
        logger.debug("Shim applied: importlib.resources.open_text / open_binary")


def shim_collections_abc() -> None:
    """
    Python 3.10+ removed ``collections.MutableMapping`` etc. (moved to
    ``collections.abc`` in 3.3, aliases removed in 3.10).

    TODO: Replace all ``collections.MutableMapping``, ``collections.Callable``,
    etc. with ``collections.abc.MutableMapping``, ``collections.abc.Callable``.
    Python 3.10 breaking change: direct collections aliases removed.
    """
    import collections
    import collections.abc

    _aliases = [
        "Awaitable", "Coroutine", "AsyncIterable", "AsyncIterator",
        "AsyncGenerator", "Hashable", "Iterable", "Iterator", "Generator",
        "Reversible", "Container", "Collection", "Callable", "Set",
        "MutableSet", "Mapping", "MutableMapping", "MappingView",
        "KeysView", "ItemsView", "ValuesView", "Sequence", "MutableSequence",
        "ByteString",
    ]
    for name in _aliases:
        if not hasattr(collections, name) and hasattr(collections.abc, name):
            setattr(collections, name, getattr(collections.abc, name))
            logger.debug("Shim applied: collections.%s -> collections.abc.%s", name, name)


# ---------------------------------------------------------------------------
# 6b. distutils removal (Python 3.12)
# ---------------------------------------------------------------------------

def shim_distutils() -> None:
    """
    ``distutils`` was removed in Python 3.12.

    TODO: Replace any ``from distutils.version import LooseVersion`` or
    ``from distutils.util import strtobool`` usages with ``packaging.version``
    and a manual boolean parser respectively.
    Python 3.12 breaking change: distutils module removed.
    """
    try:
        import distutils  # noqa: F401
    except ImportError:
        # Provide minimal shims for the most common distutils usages
        _distutils = types.ModuleType("distutils")
        _distutils_version = types.ModuleType("distutils.version")
        _distutils_util = types.ModuleType("distutils.util")

        try:
            from packaging.version import Version as _PkgVersion

            class LooseVersion:  # type: ignore[no-redef]
                def __init__(self, vstring: str) -> None:
                    self.vstring = vstring
                    self._v = _PkgVersion(vstring)

                def __str__(self) -> str:
                    return self.vstring

                def __lt__(self, other: "LooseVersion") -> bool:
                    return self._v < other._v

                def __le__(self, other: "LooseVersion") -> bool:
                    return self._v <= other._v

                def __eq__(self, other: object) -> bool:
                    if isinstance(other, LooseVersion):
                        return self._v == other._v
                    return NotImplemented

                def __ge__(self, other: "LooseVersion") -> bool:
                    return self._v >= other._v

                def __gt__(self, other: "LooseVersion") -> bool:
                    return self._v > other._v

            _distutils_version.LooseVersion = LooseVersion  # type: ignore[attr-defined]
        except ImportError:
            # TODO: Install packaging: pip install packaging
            pass

        def strtobool(val: str) -> int:
            val = val.lower()
            if val in ("y", "yes", "t", "true", "on", "1"):
                return 1
            if val in ("n", "no", "f", "false", "off", "0"):
                return 0
            raise ValueError(f"invalid truth value {val!r}")

        _distutils_util.strtobool = strtobool  # type: ignore[attr-defined]

        sys.modules["distutils"] = _distutils
        sys.modules["distutils.version"] = _distutils_version
        sys.modules["distutils.util"] = _distutils_util
        logger.debug("Shim applied: distutils (removed in Python 3.12)")


# ===========================================================================
# SECTION 7 — Apply all shims
# ===========================================================================

def apply_all_shims() -> None:
    """
    Apply all compatibility shims in the correct order.

    Call this function as early as possible in your application entry point,
    before any other imports::

        import migration_shim
        migration_shim.apply_all_shims()

        from myapp import create_app
        app = create_app()
    """
    shim_distutils()
    shim_collections_abc()
    shim_importlib_resources()
    _patch_flask_deprecated_globals()
    _patch_flask_ext_namespace()
    get_sqlalchemy_types()
    logger.info("migration_shim: all compatibility shims applied.")


# ===========================================================================
# SECTION 8 — CLI: config file migration
# ===========================================================================

def _migrate_config_file(input_path: str, output_path: str) -> None:
    """
    Reads a Python config file (as a dict literal or module), applies
    ``migrate_config()``, and writes the result to ``output_path``.

    TODO: Review the generated output file manually before using it in
    production. Automated migration cannot handle all edge cases.
    """
    import ast

    with open(input_path, "r", encoding="utf-8") as fh:
        source = fh.read()

    # Attempt to parse as a simple dict assignment: CONFIG = { ... }
    old_config: Dict[str, Any] = {}
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.upper() in (
                        "CONFIG", "APP_CONFIG", "SETTINGS"
                    ):
                        old_config = ast.literal_eval(node.value)
                        break
    except Exception as exc:
        logger.warning("Could not parse config file as AST: %s. Attempting exec().", exc)
        _ns: Dict[str, Any] = {}
        exec(compile(source, input_path, "exec"), _ns)  # noqa: S102
        old_config = {
            k: v for k, v in _ns.items()
            if not k.startswith("_") and isinstance(v, (str, int, float, bool, type(None)))
        }

    new_config = migrate_config(old_config)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("# Auto-generated by migration_shim.py — review before use\n")
        fh.write("# TODO: Verify all values and remove this file once migration is complete.\n\n")
        fh.write("import os\n\n")
        fh.write("CONFIG = {\n")
        for k, v in new_config.items():
            fh.write(f"    {k!r}: {v!r},\n")
        fh.write("}\n")

    print(f"Migrated config written to: {output_path}")


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Migration helper for Flask 1.x→3.1 / SQLAlchemy 1.3→2.0 upgrade."
    )
    parser.add_argument(
        "--migrate-config",
        metavar="INPUT",
        help="Path to old config.py to migrate.",
    )
    parser.add_argument(
        "--output",
        metavar="OUTPUT",
        default="config_migrated.py",
        help="Output path for migrated config (default: config_migrated.py).",
    )
    parser.add_argument(
        "--apply-shims",
        action="store_true",
        help="Apply all runtime shims and report what was patched.",
    )

    args = parser.parse_args()

    if args.apply_shims:
        apply_all_shims()

    if args.migrate_config:
        _migrate_config_file(args.migrate_config, args.output)

    if not args.migrate_config and not args.apply_shims:
        parser.print_help()