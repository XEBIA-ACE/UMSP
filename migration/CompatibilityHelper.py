# migration_shim.py
# Compatibility shim for the Flask 1.x → 3.1, SQLAlchemy 1.3 → 2.0 upgrade,
# plus /health and /ready endpoint additions.
#
# Usage:
#   python migration_shim.py
#
# This script:
#   1. Provides deprecated-API replacement wrappers for Flask 1.x patterns.
#   2. Provides import shims / re-export aliases for renamed packages/classes.
#   3. Provides a config migration function (old format → new format).
#   4. Registers /api/health and /api/ready blueprints on any Flask app instance.
#   5. Emits TODO comments wherever manual intervention is still required.

from __future__ import annotations

import datetime
import importlib
import os
import sys
import warnings
from typing import Any, Callable, Dict, Optional

# ---------------------------------------------------------------------------
# 0.  Python version guard
# ---------------------------------------------------------------------------
# TODO: The upgrade goal targets Python 3.12 or 3.13 (current runtime is 3.8).
#       This shim is written to be compatible with 3.8+ so it can run during the
#       transition, but you MUST update your Dockerfile / CI matrix to use
#       python:3.12-slim (or 3.13-slim) before going to production.
if sys.version_info < (3, 8):
    raise RuntimeError("Python 3.8 or newer is required to run this shim.")

# ---------------------------------------------------------------------------
# 1.  Flask import shim  (Flask 1.x → 3.1)
# ---------------------------------------------------------------------------
# Flask 3.x removed several top-level helpers that existed in Flask 1.x.
# The shim below re-exports them from their new locations so that existing
# call-sites continue to work without immediate code changes.

try:
    import flask as _flask
    from flask import Flask, Blueprint, jsonify, request, g
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Flask is not installed. Run: pip install 'flask>=3.1,<4'."
    ) from exc

# -- 1a. flask.json.jsonify was not moved but flask.json module was refactored.
#        Provide a safe re-export so `from migration_shim import jsonify` works.
try:
    from flask import jsonify as _jsonify  # noqa: F401 – re-exported below
except ImportError:  # pragma: no cover
    # TODO: If jsonify is missing from your Flask 3.x install, verify the
    #       installed version with `pip show flask`.
    raise

# -- 1b. flask.escape was removed in Flask 2.x (moved to markupsafe).
#        Provide a shim so old `from flask import escape` call-sites work.
try:
    from flask import escape as flask_escape  # type: ignore[attr-defined]
except ImportError:
    try:
        from markupsafe import escape as flask_escape  # type: ignore[assignment]
    except ImportError:
        # TODO: Install markupsafe: pip install markupsafe
        flask_escape = None  # type: ignore[assignment]

# -- 1c. flask.Markup was removed in Flask 2.x (moved to markupsafe).
try:
    from flask import Markup as FlaskMarkup  # type: ignore[attr-defined]
except ImportError:
    try:
        from markupsafe import Markup as FlaskMarkup  # type: ignore[assignment]
    except ImportError:
        # TODO: Install markupsafe: pip install markupsafe
        FlaskMarkup = None  # type: ignore[assignment]

# -- 1d. flask.signals (blinker) — blinker is now a hard dependency in Flask 2+.
#        Old code that guarded `signals_available` must be updated.
# TODO: Remove any `try/except ImportError` guards around blinker/signals in
#       your codebase. In Flask 3.x, blinker is always present.

# -- 1e. Application factory pattern.
#        Flask 1.x apps often called app.run() at module level.
#        Flask 3.x strongly recommends the application factory pattern.
# TODO: Refactor any module-level `app = Flask(__name__)` + `app.run()` blocks
#       into a `create_app()` factory function.  See `create_flask_app()` below
#       for a reference implementation.

# -- 1f. before_first_request was removed in Flask 2.3.
# TODO: Replace any @app.before_first_request decorators with an explicit
#       with app.app_context(): block inside your create_app() factory, or use
#       the app.cli.with_appcontext() decorator for CLI commands.

# -- 1g. flask.ext.* namespace was removed long ago; raise a clear error.
class _FlaskExtShim:
    """Raises a helpful error when legacy flask.ext.* imports are attempted."""

    def __getattr__(self, name: str) -> Any:
        raise ImportError(
            f"flask.ext.{name} is not available in Flask 3.x. "
            "Install the extension directly and import from its own package. "
            # TODO: Replace `from flask.ext.<name> import ...` with the
            #       extension's own import path (e.g. `from flask_<name> import ...`).
        )


# Patch sys.modules so `import flask.ext` gives a useful error.
sys.modules.setdefault("flask.ext", _FlaskExtShim())  # type: ignore[arg-type]

# ---------------------------------------------------------------------------
# 2.  SQLAlchemy import shim  (1.3 → 2.0)
# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 removed the legacy Query API and changed several import paths.

try:
    import sqlalchemy as sa
    from sqlalchemy import text, select, insert, update, delete
    from sqlalchemy.orm import Session, DeclarativeBase, mapped_column, Mapped
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "SQLAlchemy is not installed. Run: pip install 'sqlalchemy>=2.0,<3'."
    ) from exc

# -- 2a. declarative_base() was soft-deprecated in 2.0; DeclarativeBase is preferred.
#        Provide a shim so old `Base = declarative_base()` call-sites keep working.
try:
    from sqlalchemy.orm import declarative_base as _declarative_base  # 2.0 compat shim
except ImportError:
    # In SQLAlchemy 2.0 the function still exists but emits a deprecation warning.
    # TODO: Replace `Base = declarative_base()` with:
    #
    #   class Base(DeclarativeBase):
    #       pass
    #
    # This is the canonical SQLAlchemy 2.0 pattern.
    _declarative_base = None  # type: ignore[assignment]


def declarative_base(*args: Any, **kwargs: Any) -> Any:
    """
    Shim for the legacy ``sqlalchemy.orm.declarative_base()`` call.

    Delegates to the real function while emitting a deprecation warning so
    developers know to migrate to the ``DeclarativeBase`` class pattern.
    """
    warnings.warn(
        "declarative_base() is deprecated in SQLAlchemy 2.0. "
        "Define a base class that inherits from sqlalchemy.orm.DeclarativeBase instead. "
        # TODO: Migrate all models to use `class Base(DeclarativeBase): pass`
        #       and remove this shim once migration is complete.
        ,
        DeprecationWarning,
        stacklevel=2,
    )
    if _declarative_base is not None:
        return _declarative_base(*args, **kwargs)
    # Fallback: return a DeclarativeBase subclass
    class _LegacyBase(DeclarativeBase):  # type: ignore[misc]
        pass
    return _LegacyBase


# -- 2b. Session.execute() now requires text() for raw SQL strings.
#        Provide a helper that wraps bare strings automatically.
def safe_execute(session: Session, statement: Any, params: Optional[Dict] = None) -> Any:
    """
    Execute *statement* on *session*, automatically wrapping bare strings in
    ``sqlalchemy.text()`` so that SQLAlchemy 2.0 does not raise
    ``ObjectNotExecutableError``.

    .. deprecated::
        Pass a proper ``select()`` / ``text()`` construct directly.
        # TODO: Replace all ``session.execute("SELECT ...")`` call-sites with
        #       ``session.execute(text("SELECT ..."))`` or a proper ORM construct.
    """
    if isinstance(statement, str):
        warnings.warn(
            "Passing a raw string to session.execute() is not supported in "
            "SQLAlchemy 2.0. Wrap the string with sqlalchemy.text(). "
            # TODO: Update the call-site to use text() or a select() construct.
            ,
            DeprecationWarning,
            stacklevel=2,
        )
        statement = text(statement)
    if params:
        return session.execute(statement, params)
    return session.execute(statement)


# -- 2c. Legacy Query API shim.
#        session.query(Model) was removed in SQLAlchemy 2.0.
#        This wrapper re-implements the most common patterns via select().
class LegacyQueryShim:
    """
    Minimal shim that translates the most common SQLAlchemy 1.x
    ``session.query(Model)`` patterns into SQLAlchemy 2.0 ``select()`` calls.

    Supported methods: .all(), .first(), .one(), .one_or_none(),
                       .filter(), .filter_by(), .order_by(), .limit(),
                       .offset(), .count(), .get()

    # TODO: Replace all session.query() call-sites with explicit select()
    #       statements.  This shim covers common cases but cannot handle
    #       every legacy query pattern (e.g. complex joins, subqueries).
    """

    def __init__(self, session: Session, entity: Any) -> None:
        self._session = session
        self._entity = entity
        self._stmt = select(entity)

    def filter(self, *criteria: Any) -> "LegacyQueryShim":
        self._stmt = self._stmt.where(*criteria)
        return self

    def filter_by(self, **kwargs: Any) -> "LegacyQueryShim":
        for key, value in kwargs.items():
            self._stmt = self._stmt.where(
                getattr(self._entity, key) == value
            )
        return self

    def order_by(self, *clauses: Any) -> "LegacyQueryShim":
        self._stmt = self._stmt.order_by(*clauses)
        return self

    def limit(self, n: int) -> "LegacyQueryShim":
        self._stmt = self._stmt.limit(n)
        return self

    def offset(self, n: int) -> "LegacyQueryShim":
        self._stmt = self._stmt.offset(n)
        return self

    def all(self) -> list:
        return list(self._session.scalars(self._stmt).all())

    def first(self) -> Any:
        return self._session.scalars(self._stmt).first()

    def one(self) -> Any:
        return self._session.scalars(self._stmt).one()

    def one_or_none(self) -> Any:
        return self._session.scalars(self._stmt).one_or_none()

    def count(self) -> int:
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(self._stmt.subquery())
        return self._session.execute(count_stmt).scalar_one()

    def get(self, pk: Any) -> Any:
        # TODO: session.query(Model).get(pk) → session.get(Model, pk)
        return self._session.get(self._entity, pk)


def legacy_query(session: Session, entity: Any) -> LegacyQueryShim:
    """
    Drop-in replacement for ``session.query(Model)``.

    Example::

        # Old (SQLAlchemy 1.3):
        users = session.query(User).filter_by(active=True).all()

        # Shim (temporary):
        users = legacy_query(session, User).filter_by(active=True).all()

        # New (SQLAlchemy 2.0 — target state):
        users = session.scalars(select(User).where(User.active == True)).all()

    # TODO: Remove all legacy_query() usages once the codebase is fully
    #       migrated to the SQLAlchemy 2.0 select() API.
    """
    warnings.warn(
        "legacy_query() is a temporary shim for session.query(). "
        "Migrate to session.scalars(select(Model)...) as per SQLAlchemy 2.0. "
        # TODO: Migrate each call-site to the new select() API.
        ,
        DeprecationWarning,
        stacklevel=2,
    )
    return LegacyQueryShim(session, entity)


# -- 2d. Column type import path changes.
#        In SQLAlchemy 2.0, types are still in sqlalchemy but mapped_column /
#        Mapped are the preferred way to declare columns.
# TODO: Replace `Column(String)` declarations with `mapped_column(String)` and
#       add `Mapped[str]` type annotations on your model attributes.

# -- 2e. relationship() lazy loading default changed.
# TODO: SQLAlchemy 2.0 raises an error for lazy-loaded relationships accessed
#       outside a session.  Audit all relationship() declarations and add
#       explicit lazy="select" (old default) or migrate to eager loading /
#       selectinload() where appropriate.

# ---------------------------------------------------------------------------
# 3.  Config format migration  (old → new)
# ---------------------------------------------------------------------------

def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform an old-style application config dict into the new format
    expected by Flask 3.x and SQLAlchemy 2.0.

    Old format (Flask 1.x era)::

        {
            "DEBUG": True,
            "TESTING": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///dev.db",
            "SQLALCHEMY_TRACK_MODIFICATIONS": True,   # removed in SQLAlchemy 2.0
            "SECRET_KEY": "hardcoded-secret",          # must move to env var
            "SERVER_NAME": "localhost:5000",
            "JSON_SORT_KEYS": True,                    # removed in Flask 2.3
            "JSON_AS_ASCII": True,                     # removed in Flask 2.3
            "JSONIFY_PRETTYPRINT_REGULAR": False,      # removed in Flask 2.3
            "PROPAGATE_EXCEPTIONS": None,
        }

    New format (Flask 3.x / SQLAlchemy 2.0)::

        {
            "DEBUG": True,
            "TESTING": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///dev.db",
            # SQLALCHEMY_TRACK_MODIFICATIONS removed
            "SECRET_KEY": "<from env>",
            # SERVER_NAME kept only if explicitly needed
            # JSON_* keys removed — configure via app.json provider instead
        }

    Returns the migrated config dict.  Emits warnings for keys that require
    manual intervention.
    """
    new_config: Dict[str, Any] = {}

    for key, value in old_config.items():

        # ── Removed Flask 2.3 / 3.x keys ─────────────────────────────────────
        if key == "JSON_SORT_KEYS":
            warnings.warn(
                "Config key 'JSON_SORT_KEYS' was removed in Flask 2.3. "
                "Set app.json.sort_keys = <bool> after app creation instead. "
                # TODO: Replace config['JSON_SORT_KEYS'] with
                #       app.json.sort_keys = True/False in your create_app().
                ,
                DeprecationWarning,
                stacklevel=2,
            )
            continue  # drop from new config

        if key == "JSON_AS_ASCII":
            warnings.warn(
                "Config key 'JSON_AS_ASCII' was removed in Flask 2.3. "
                "Set app.json.ensure_ascii = <bool> after app creation instead. "
                # TODO: Replace config['JSON_AS_ASCII'] with
                #       app.json.ensure_ascii = True/False in your create_app().
                ,
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "JSONIFY_PRETTYPRINT_REGULAR":
            warnings.warn(
                "Config key 'JSONIFY_PRETTYPRINT_REGULAR' was removed in Flask 2.3. "
                "Set app.json.mimetype or use app.json.compact = False instead. "
                # TODO: Replace with app.json.compact = not <old_value>.
                ,
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "JSONIFY_MIMETYPE":
            warnings.warn(
                "Config key 'JSONIFY_MIMETYPE' was removed in Flask 2.3. "
                "Set app.json.mimetype = <value> after app creation instead. "
                # TODO: Replace with app.json.mimetype = <value>.
                ,
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        # ── SQLAlchemy 2.0 removed keys ───────────────────────────────────────
        if key == "SQLALCHEMY_TRACK_MODIFICATIONS":
            warnings.warn(
                "Config key 'SQLALCHEMY_TRACK_MODIFICATIONS' is not supported "
                "in SQLAlchemy 2.0 / Flask-SQLAlchemy 3.x and has been removed. "
                # TODO: Remove SQLALCHEMY_TRACK_MODIFICATIONS from your config.
                #       The event system is always available; tracking is gone.
                ,
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "SQLALCHEMY_COMMIT_ON_TEARDOWN":
            warnings.warn(
                "Config key 'SQLALCHEMY_COMMIT_ON_TEARDOWN' was removed. "
                "Manage transactions explicitly in your view functions or use "
                "a context manager. "
                # TODO: Remove SQLALCHEMY_COMMIT_ON_TEARDOWN and add explicit
                #       db.session.commit() / db.session.rollback() calls.
                ,
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        # ── Hardcoded secrets — must move to environment variables ─────────────
        if key == "SECRET_KEY":
            env_value = os.environ.get("SECRET_KEY")
            if env_value:
                new_config[key] = env_value
            else:
                warnings.warn(
                    "Config key 'SECRET_KEY' should be loaded from the environment, "
                    "not hardcoded. Set the SECRET_KEY environment variable. "
                    # TODO: Remove the hardcoded SECRET_KEY value and load it with:
                    #       app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
                    #       Add SECRET_KEY to your .env.example (without a real value).
                    ,
                    UserWarning,
                    stacklevel=2,
                )
                new_config[key] = value  # keep for now, but warn
            continue

        if key in ("DATABASE_URL", "SQLALCHEMY_DATABASE_URI"):
            env_value = os.environ.get("DATABASE_URL") or os.environ.get(
                "SQLALCHEMY_DATABASE_URI"
            )
            if env_value:
                new_config["SQLALCHEMY_DATABASE_URI"] = env_value
            else:
                warnings.warn(
                    f"Config key '{key}' should be loaded from the DATABASE_URL "
                    "environment variable, not hardcoded. "
                    # TODO: Remove hardcoded database credentials from config.
                    #       Use os.environ['DATABASE_URL'] and add it to .env.example.
                    ,
                    UserWarning,
                    stacklevel=2,
                )
                new_config["SQLALCHEMY_DATABASE_URI"] = value
            continue

        # ── PROPAGATE_EXCEPTIONS: None is no longer valid in Flask 3.x ─────────
        if key == "PROPAGATE_EXCEPTIONS" and value is None:
            # Flask 3.x treats None as False; make it explicit.
            new_config[key] = False
            continue

        # ── Pass through all other keys unchanged ─────────────────────────────
        new_config[key] = value

    # Ensure SQLALCHEMY_DATABASE_URI is present
    if "SQLALCHEMY_DATABASE_URI" not in new_config:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///app.db")
        new_config["SQLALCHEMY_DATABASE_URI"] = db_url
        # TODO: Set the DATABASE_URL environment variable for your target
        #       environment (development, staging, production).

    return new_config


# ---------------------------------------------------------------------------
# 4.  /api/health and /api/ready blueprints
# ---------------------------------------------------------------------------
# These blueprints implement the liveness and readiness probe endpoints
# described in the spec.  Register them on your Flask app via
# register_health_blueprints(app) inside your create_app() factory.

health_bp = Blueprint("health", __name__)
ready_bp = Blueprint("ready", __name__)

# The service name is read from the SERVICE_NAME environment variable so that
# the same shim can be used by multiple services without code changes.
_SERVICE_NAME: str = os.environ.get("SERVICE_NAME", "python-service")


@health_bp.get("/api/health")
def liveness() -> Any:
    """
    Liveness probe — ``GET /api/health``.

    Returns ``200 OK`` with::

        {
            "status":    "ok",
            "service":   "<SERVICE_NAME>",
            "timestamp": "<ISO-8601 UTC string>"
        }

    This endpoint must remain unauthenticated so that load balancers and
    Kubernetes liveness probes can reach it without credentials.
    Matches the contract already implemented in the Java HealthController and
    the Node.js HealthController.
    """
    body = {
        "status": "ok",
        "service": _SERVICE_NAME,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return jsonify(body), 200


# ---------------------------------------------------------------------------
# Readiness check registry
# ---------------------------------------------------------------------------
# Register callables that return (bool, str) — (is_ready, reason).
# The /api/ready endpoint calls all registered checks and returns 200 only
# when every check passes.
#
# Example::
#
#   from migration_shim import register_readiness_check
#
#   def db_check():
#       try:
#           db.session.execute(text("SELECT 1"))
#           return True, "database ok"
#       except Exception as exc:
#           return False, f"database error: {exc}"
#
#   register_readiness_check("database", db_check)

_readiness_checks: Dict[str, Callable[[], tuple[bool, str]]] = {}


def register_readiness_check(name: str, fn: Callable[[], tuple[bool, str]]) -> None:
    """
    Register a named readiness check function.

    *fn* must be a zero-argument callable that returns ``(bool, str)``:
    - ``True, "reason"``  → check passed
    - ``False, "reason"`` → check failed (service not ready)

    # TODO: Register at least one meaningful readiness check per service,
    #       e.g. a database connectivity check, before deploying to production.
    """
    _readiness_checks[name] = fn


@ready_bp.get("/api/ready")
def readiness() -> Any:
    """
    Readiness probe — ``GET /api/ready``.

    Runs all registered readiness checks.

    Returns ``200 OK`` when all checks pass::

        {
            "status":    "ready",
            "service":   "<SERVICE_NAME>",
            "timestamp": "<ISO-8601 UTC string>",
            "checks":    { "<name>": "ok", ... }
        }

    Returns ``503 Service Unavailable`` when any check fails::

        {
            "status":    "not_ready",
            "service":   "<SERVICE_NAME>",
            "timestamp": "<ISO-8601 UTC string>",
            "checks":    { "<name>": "<reason>", ... }
        }

    This endpoint must remain unauthenticated.
    # TODO: Add this path to your security allowlist.
    #       For Flask-Login / JWT-based auth, exclude /api/ready from the
    #       @login_required / token_required decorators.
    #       For the payment-service SecurityConfig.java, add:
    #           .requestMatchers("/api/ready/**").permitAll()
    #       alongside the existing /api/health/** rule.
    """
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    check_results: Dict[str, str] = {}
    all_ready = True

    for name, fn in _readiness_checks.items():
        try:
            passed, reason = fn()
        except Exception as exc:  # noqa: BLE001
            passed = False
            reason = f"check raised exception: {exc}"
        check_results[name] = reason if reason else ("ok" if passed else "failed")
        if not passed:
            all_ready = False

    # If no checks are registered, report ready (liveness-only mode).
    # TODO: Register at least one readiness check (e.g. DB ping) per service.
    if not _readiness_checks:
        check_results["default"] = "no checks registered"

    status_str = "ready" if all_ready else "not_ready"
    http_status = 200 if all_ready else 503

    body = {
        "status": status_str,
        "service": _SERVICE_NAME,
        "timestamp": timestamp,
        "checks": check_results,
    }
    return jsonify(body), http_status


def register_health_blueprints(app: Flask) -> None:
    """
    Register the ``/api/health`` (liveness) and ``/api/ready`` (readiness)
    blueprints on *app*.

    Call this inside your ``create_app()`` factory **after** applying the
    migrated config::

        def create_app(config_overrides=None):
            app = Flask(__name__)
            app.config.update(migrate_config(raw_config))
            register_health_blueprints(app)
            # ... register other blueprints ...
            return app

    Both endpoints are intentionally registered **without** any authentication
    middleware so that orchestration platforms can probe them freely.
    """
    app.register_blueprint(health_bp)
    app.register_blueprint(ready_bp)


# ---------------------------------------------------------------------------
# 5.  Application factory reference implementation
# ---------------------------------------------------------------------------

def create_flask_app(
    raw_config: Optional[Dict[str, Any]] = None,
    extra_blueprints: Optional[list] = None,
) -> Flask:
    """
    Reference application factory for Flask 3.x.

    Applies the config migration shim, registers health/ready blueprints, and
    returns a fully configured ``Flask`` application instance without calling
    ``app.run()``.

    :param raw_config:       Optional dict of old-style config values to migrate.
    :param extra_blueprints: Optional list of ``(blueprint, kwargs)`` tuples to
                             register after the health blueprints.

    # TODO: Replace any module-level `app = Flask(__name__)` + `app.run()`
    #       patterns in your codebase with a call to this factory (or your own
    #       equivalent) and a separate entry-point that calls app.run() or
    #       hands the app to a WSGI server (gunicorn, waitress, etc.).
    """
    app = Flask(__name__)

    # Apply migrated config
    migrated = migrate_config(raw_config or {})
    app.config.update(migrated)

    # Register probe endpoints
    register_health_blueprints(app)

    # Register any additional blueprints supplied by the caller
    if extra_blueprints:
        for bp_entry in extra_blueprints:
            if isinstance(bp_entry, (list, tuple)) and len(bp_entry) == 2:
                bp, bp_kwargs = bp_entry
                app.register_blueprint(bp, **bp_kwargs)
            else:
                app.register_blueprint(bp_entry)

    # TODO: Wire up Flask-SQLAlchemy (or plain SQLAlchemy) here:
    #   from flask_sqlalchemy import SQLAlchemy
    #   db = SQLAlchemy()
    #   db.init_app(app)
    #
    # TODO: Wire up Flask-Migrate (Alembic) for schema migrations:
    #   from flask_migrate import Migrate
    #   migrate = Migrate(app, db)
    #
    # TODO: Remove any hardcoded credentials from the codebase and load them
    #       exclusively from environment variables (os.environ / python-dotenv).
    #       Add a .env.example file documenting all required variables without
    #       real values.
    #
    # TODO: Add a Dockerfile targeting python:3.12-slim (or 3.13-slim) and a
    #       CI/CD pipeline step that runs `pip audit` or `safety check` for
    #       dependency vulnerability scanning.

    return app


# ---------------------------------------------------------------------------
# 6.  SQLAlchemy 2.0 engine / session factory helpers
# ---------------------------------------------------------------------------

def create_engine_v2(database_url: Optional[str] = None, **kwargs: Any) -> Any:
    """
    Create a SQLAlchemy 2.0-compatible engine.

    Reads ``DATABASE_URL`` from the environment when *database_url* is not
    supplied.  Passes ``future=True`` (the 2.0 default) explicitly so that
    the engine behaves consistently regardless of the installed minor version.

    # TODO: Replace any direct ``create_engine()`` calls in your codebase with
    #       this helper (or inline the same kwargs) to ensure 2.0 semantics.
    """
    from sqlalchemy import create_engine

    url = database_url or os.environ.get("DATABASE_URL", "sqlite:///app.db")

    # future=True is the default in 2.0 but being explicit avoids surprises
    # when running under a mixed 1.4/2.0 environment during migration.
    kwargs.setdefault("future", True)

    # TODO: For production PostgreSQL, also set:
    #   pool_pre_ping=True   — detect stale connections
    #   pool_size=5          — tune to your workload
    #   max_overflow=10
    return create_engine(url, **kwargs)


def create_session_factory(engine: Any) -> Any:
    """
    Return a SQLAlchemy 2.0 ``sessionmaker`` bound to *engine*.

    Usage::

        engine = create_engine_v2()
        SessionLocal = create_session_factory(engine)

        with SessionLocal() as session:
            results = session.scalars(select(MyModel)).all()

    # TODO: Replace ``scoped_session(sessionmaker(...))`` patterns (SQLAlchemy
    #       1.x) with this helper or an equivalent ``sessionmaker`` call.
    """
    from sqlalchemy.orm import sessionmaker

    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


# ---------------------------------------------------------------------------
# 7.  Entrypoint — run a minimal demo when executed directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick smoke-test: build the app and print the registered routes.
    demo_app = create_flask_app(
        raw_config={
            "DEBUG": True,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,  # will be stripped + warned
            "JSON_SORT_KEYS": True,                   # will be stripped + warned
        }
    )

    print("Registered routes:")
    for rule in sorted(demo_app.url_map.iter_rules(), key=lambda r: r.rule):
        methods = ",".join(sorted(r.methods - {"HEAD", "OPTIONS"}))
        print(f"  {methods:10s}  {rule.rule}")

    # TODO: In production, do NOT call app.run() here.
    #       Use a WSGI server: gunicorn migration_shim:create_flask_app()
    demo_app.run(host="127.0.0.1", port=5000, debug=True)