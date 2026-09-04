# migration_shim.py
# Compatibility shim for Flask 1.x → 3.1, SQLAlchemy 1.3 → 2.0 upgrade
# and /health + /ready endpoint additions.
#
# Usage:
#   python migration_shim.py
#
# This script:
#   1. Provides deprecated Flask API replacements (Flask 1.x → 3.x)
#   2. Provides SQLAlchemy 1.3 → 2.0 query API shims
#   3. Provides a config migration function (old format → new format)
#   4. Registers /api/health and /api/ready blueprints on an existing Flask app
#   5. Marks every location requiring manual intervention with a TODO comment

from __future__ import annotations

import datetime
import os
import warnings
from typing import Any, Callable, Dict, Optional

# ---------------------------------------------------------------------------
# Dependency availability guards
# ---------------------------------------------------------------------------

try:
    import flask
    from flask import Flask, Blueprint, jsonify, request, g
    import flask.globals  # noqa: F401
    _FLASK_AVAILABLE = True
    _FLASK_VERSION = tuple(int(x) for x in flask.__version__.split(".")[:2])
except ImportError:  # pragma: no cover
    _FLASK_AVAILABLE = False
    _FLASK_VERSION = (0, 0)

try:
    import sqlalchemy
    from sqlalchemy import text, select
    import sqlalchemy.orm
    _SA_AVAILABLE = True
    _SA_VERSION = tuple(int(x) for x in sqlalchemy.__version__.split(".")[:2])
except ImportError:  # pragma: no cover
    _SA_AVAILABLE = False
    _SA_VERSION = (0, 0)


# ===========================================================================
# SECTION 1 — Flask 1.x → 3.x deprecated API replacements
# ===========================================================================

class FlaskCompatShim:
    """
    Wraps a Flask 3.x application and re-exposes Flask 1.x APIs that were
    removed or changed in Flask 2.x / 3.x.

    Breaking changes addressed:
      - flask.json.jsonify / flask.json.dumps signature changes
      - before_first_request removed in Flask 2.3 (Flask 3.x: fully removed)
      - flask.escape moved to markupsafe.escape
      - flask.Markup moved to markupsafe.Markup
      - flask._app_ctx_stack / flask._request_ctx_stack removed
      - send_file / send_from_directory: attachment_filename → download_name
      - PROPAGATE_EXCEPTIONS default changed
      - JSON_SORT_KEYS / JSONIFY_PRETTYPRINT_REGULAR config keys removed
    """

    def __init__(self, app: "Flask") -> None:
        if not _FLASK_AVAILABLE:
            raise RuntimeError("Flask is not installed.")
        self.app = app
        self._before_first_request_funcs: list[Callable] = []
        self._first_request_done = False
        self._patch_before_first_request()

    # ------------------------------------------------------------------
    # before_first_request shim
    # Flask 2.3 deprecated before_first_request; Flask 3.x removed it.
    # Replacement: use a with app.app_context() block at startup, or an
    # explicit flag checked in a before_request hook (implemented below).
    # ------------------------------------------------------------------

    def _patch_before_first_request(self) -> None:
        """
        Registers a before_request hook that fires registered callables
        exactly once, emulating the removed before_first_request decorator.
        """
        shim = self

        @self.app.before_request
        def _run_before_first_request_funcs() -> None:
            if not shim._first_request_done:
                shim._first_request_done = True
                for fn in shim._before_first_request_funcs:
                    fn()

    def before_first_request(self, fn: Callable) -> Callable:
        """
        Drop-in replacement for the removed @app.before_first_request decorator.

        Usage (old Flask 1.x code):
            @app.before_first_request
            def startup():
                ...

        Usage with this shim:
            shim = FlaskCompatShim(app)

            @shim.before_first_request
            def startup():
                ...
        """
        warnings.warn(
            "before_first_request was removed in Flask 3.x. "
            "This shim emulates it via a before_request hook. "
            "Migrate to app startup code or an explicit flag.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._before_first_request_funcs.append(fn)
        return fn

    # ------------------------------------------------------------------
    # flask.escape / flask.Markup shim
    # Moved to markupsafe in Flask 2.x; import alias provided here.
    # ------------------------------------------------------------------

    @staticmethod
    def get_escape() -> Callable:
        """
        Returns markupsafe.escape, replacing the removed flask.escape.

        Old code:  from flask import escape
        New code:  from markupsafe import escape
        """
        try:
            from markupsafe import escape  # type: ignore[import]
            return escape
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "markupsafe is required. Install it with: pip install markupsafe"
            ) from exc

    @staticmethod
    def get_markup() -> type:
        """
        Returns markupsafe.Markup, replacing the removed flask.Markup.

        Old code:  from flask import Markup
        New code:  from markupsafe import Markup
        """
        try:
            from markupsafe import Markup  # type: ignore[import]
            return Markup
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "markupsafe is required. Install it with: pip install markupsafe"
            ) from exc

    # ------------------------------------------------------------------
    # send_file / send_from_directory: attachment_filename → download_name
    # ------------------------------------------------------------------

    @staticmethod
    def send_file_compat(path_or_file: Any, **kwargs: Any) -> Any:
        """
        Wraps flask.send_file, translating the removed `attachment_filename`
        kwarg to `download_name` (Flask 2.0+).

        Old code:  send_file(path, attachment_filename="report.pdf")
        New code:  send_file(path, download_name="report.pdf")
        """
        from flask import send_file  # type: ignore[import]

        if "attachment_filename" in kwargs:
            warnings.warn(
                "send_file(attachment_filename=...) was removed in Flask 2.0. "
                "Use download_name= instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            kwargs["download_name"] = kwargs.pop("attachment_filename")

        # TODO: If you also passed `cache_timeout`, rename it to `max_age`
        # (removed in Flask 2.0). See Flask 2.0 migration guide.
        if "cache_timeout" in kwargs:
            warnings.warn(
                "send_file(cache_timeout=...) was removed in Flask 2.0. "
                "Use max_age= instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            kwargs["max_age"] = kwargs.pop("cache_timeout")

        return send_file(path_or_file, **kwargs)

    # ------------------------------------------------------------------
    # JSON config key migration
    # JSON_SORT_KEYS and JSONIFY_PRETTYPRINT_REGULAR were removed in
    # Flask 2.3 / 3.x. They must be set on the app's json_provider.
    # ------------------------------------------------------------------

    @staticmethod
    def apply_json_config(app: "Flask", sort_keys: bool = False, pretty: bool = False) -> None:
        """
        Applies JSON formatting options that were previously set via
        JSON_SORT_KEYS and JSONIFY_PRETTYPRINT_REGULAR config keys.

        Old code:
            app.config["JSON_SORT_KEYS"] = False
            app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

        New code (Flask 3.x):
            FlaskCompatShim.apply_json_config(app, sort_keys=False, pretty=True)

        TODO: If you relied on JSON_AS_ASCII (also removed), set
              app.json.ensure_ascii = False directly.
        """
        warnings.warn(
            "JSON_SORT_KEYS and JSONIFY_PRETTYPRINT_REGULAR config keys were "
            "removed in Flask 2.3+. Use app.json.sort_keys and app.json.mimetype "
            "or a custom DefaultJSONProvider instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if hasattr(app, "json"):
            app.json.sort_keys = sort_keys  # type: ignore[attr-defined]
        else:
            # TODO: Flask version predates json provider API — manual migration required.
            pass


# ===========================================================================
# SECTION 2 — SQLAlchemy 1.3 → 2.0 query API shims
# ===========================================================================

class SAQueryShim:
    """
    Provides SQLAlchemy 1.3-style query helpers backed by the SQLAlchemy 2.0
    select() / Session.execute() API.

    Breaking changes addressed:
      - Session.query() is legacy in 2.0 (still present but emits warnings)
      - Query.get() removed → Session.get()
      - Query.first() / .all() → execute(select(...)).scalars()
      - engine.execute() removed → use Session or Connection.execute()
      - Column type imports moved: sqlalchemy.types → sqlalchemy directly
      - relationship() cascade default changed
      - declarative_base() moved to sqlalchemy.orm.declarative_base()
    """

    def __init__(self, session: Any) -> None:
        if not _SA_AVAILABLE:
            raise RuntimeError("SQLAlchemy is not installed.")
        self.session = session

    def get(self, model: type, pk: Any) -> Any:
        """
        Replaces the removed Query.get(pk).

        Old code:  session.query(Model).get(pk)
        New code:  session.get(Model, pk)
        """
        warnings.warn(
            "Query.get() is removed in SQLAlchemy 2.0. Use Session.get(Model, pk).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.session.get(model, pk)

    def all(self, model: type) -> list:
        """
        Replaces session.query(Model).all().

        Old code:  session.query(Model).all()
        New code:  session.execute(select(Model)).scalars().all()
        """
        warnings.warn(
            "session.query() is legacy in SQLAlchemy 2.0. "
            "Use session.execute(select(Model)).scalars().all().",
            DeprecationWarning,
            stacklevel=2,
        )
        stmt = select(model)
        return self.session.execute(stmt).scalars().all()

    def filter_by(self, model: type, **kwargs: Any) -> list:
        """
        Replaces session.query(Model).filter_by(**kwargs).all().

        Old code:  session.query(Model).filter_by(email=email).all()
        New code:  session.execute(select(Model).filter_by(**kwargs)).scalars().all()
        """
        warnings.warn(
            "session.query().filter_by() is legacy in SQLAlchemy 2.0. "
            "Use session.execute(select(Model).filter_by(...)).scalars().all().",
            DeprecationWarning,
            stacklevel=2,
        )
        stmt = select(model).filter_by(**kwargs)
        return self.session.execute(stmt).scalars().all()

    def first(self, model: type, **kwargs: Any) -> Any:
        """
        Replaces session.query(Model).filter_by(**kwargs).first().

        Old code:  session.query(Model).filter_by(email=email).first()
        New code:  session.execute(select(Model).filter_by(**kwargs)).scalars().first()
        """
        warnings.warn(
            "session.query().filter_by().first() is legacy in SQLAlchemy 2.0. "
            "Use session.execute(select(Model).filter_by(...)).scalars().first().",
            DeprecationWarning,
            stacklevel=2,
        )
        stmt = select(model).filter_by(**kwargs)
        return self.session.execute(stmt).scalars().first()

    def count(self, model: type) -> int:
        """
        Replaces session.query(Model).count().

        Old code:  session.query(Model).count()
        New code:  session.scalar(select(func.count()).select_from(Model))
        """
        from sqlalchemy import func  # type: ignore[import]

        warnings.warn(
            "session.query().count() is legacy in SQLAlchemy 2.0. "
            "Use session.scalar(select(func.count()).select_from(Model)).",
            DeprecationWarning,
            stacklevel=2,
        )
        stmt = select(sqlalchemy.func.count()).select_from(model)
        return self.session.scalar(stmt)


def get_declarative_base() -> Any:
    """
    Returns sqlalchemy.orm.DeclarativeBase (2.0) or the legacy declarative_base().

    Old code:  from sqlalchemy.ext.declarative import declarative_base; Base = declarative_base()
    New code:  from sqlalchemy.orm import DeclarativeBase; class Base(DeclarativeBase): pass

    This helper bridges both styles.

    TODO: Migrate all model base classes to inherit from sqlalchemy.orm.DeclarativeBase
    directly, as declarative_base() is removed in SQLAlchemy 2.0 (it still exists in
    the 2.0 release as a legacy alias but will be removed in a future version).
    """
    if _SA_VERSION >= (2, 0):
        try:
            from sqlalchemy.orm import DeclarativeBase  # type: ignore[import]

            class _Base(DeclarativeBase):  # type: ignore[misc]
                pass

            return _Base
        except ImportError:
            pass
    # Fallback for SQLAlchemy 1.x
    from sqlalchemy.ext.declarative import declarative_base  # type: ignore[import]
    warnings.warn(
        "sqlalchemy.ext.declarative.declarative_base() is legacy. "
        "Migrate to sqlalchemy.orm.DeclarativeBase.",
        DeprecationWarning,
        stacklevel=2,
    )
    return declarative_base()


def create_engine_compat(url: str, **kwargs: Any) -> Any:
    """
    Wraps sqlalchemy.create_engine, removing kwargs that were valid in 1.3
    but removed in 2.0.

    Removed kwargs handled:
      - convert_unicode (removed in 2.0)
      - implicit_returning (removed in 2.0; now always True)

    TODO: If you used execution_options on the engine directly, migrate to
    Connection.execution_options() per the SQLAlchemy 2.0 migration guide.
    """
    if not _SA_AVAILABLE:
        raise RuntimeError("SQLAlchemy is not installed.")

    removed_kwargs = ["convert_unicode", "implicit_returning"]
    for key in removed_kwargs:
        if key in kwargs:
            warnings.warn(
                f"create_engine() kwarg '{key}' was removed in SQLAlchemy 2.0 and "
                f"has been ignored by this shim.",
                DeprecationWarning,
                stacklevel=2,
            )
            kwargs.pop(key)

    # TODO: If you relied on engine.execute(), that was removed in SQLAlchemy 2.0.
    # Use a Session or an explicit Connection via engine.connect() instead.

    return sqlalchemy.create_engine(url, **kwargs)


# ===========================================================================
# SECTION 3 — Config format migration
# ===========================================================================

def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms an old Flask 1.x / SQLAlchemy 1.3 config dict into the format
    expected by Flask 3.x / SQLAlchemy 2.0.

    Handles the following breaking config changes:

    Flask:
      - JSON_SORT_KEYS          → removed (set on app.json.sort_keys)
      - JSONIFY_PRETTYPRINT_REGULAR → removed (set on app.json.mimetype)
      - JSON_AS_ASCII           → removed (set on app.json.ensure_ascii)
      - PROPAGATE_EXCEPTIONS    → still valid; default changed to True in testing
      - SERVER_NAME             → still valid; warn if set (affects URL generation)

    SQLAlchemy (via Flask-SQLAlchemy):
      - SQLALCHEMY_TRACK_MODIFICATIONS → removed in Flask-SQLAlchemy 3.x
      - SQLALCHEMY_COMMIT_ON_TEARDOWN  → removed; use explicit commits
      - SQLALCHEMY_POOL_SIZE, SQLALCHEMY_MAX_OVERFLOW, SQLALCHEMY_POOL_TIMEOUT
        → moved to SQLALCHEMY_ENGINE_OPTIONS dict in Flask-SQLAlchemy 3.x

    Health / readiness probe config (new keys introduced by this upgrade):
      - HEALTH_SERVICE_NAME     → new key for /api/health response
      - READINESS_CHECKS        → new key listing readiness check callables
    """
    new_config: Dict[str, Any] = {}
    engine_options: Dict[str, Any] = {}

    for key, value in old_config.items():

        # ── Flask JSON config keys removed in Flask 2.3 / 3.x ──────────────
        if key == "JSON_SORT_KEYS":
            warnings.warn(
                "Config key JSON_SORT_KEYS was removed in Flask 2.3. "
                "Set app.json.sort_keys after app creation.",
                DeprecationWarning,
                stacklevel=2,
            )
            # Store as a hint for post-creation setup; not a real Flask config key.
            new_config["_COMPAT_JSON_SORT_KEYS"] = value
            continue

        if key == "JSONIFY_PRETTYPRINT_REGULAR":
            warnings.warn(
                "Config key JSONIFY_PRETTYPRINT_REGULAR was removed in Flask 2.3. "
                "Set app.json.mimetype or use a custom DefaultJSONProvider.",
                DeprecationWarning,
                stacklevel=2,
            )
            new_config["_COMPAT_JSONIFY_PRETTYPRINT_REGULAR"] = value
            continue

        if key == "JSON_AS_ASCII":
            warnings.warn(
                "Config key JSON_AS_ASCII was removed in Flask 2.3. "
                "Set app.json.ensure_ascii after app creation.",
                DeprecationWarning,
                stacklevel=2,
            )
            new_config["_COMPAT_JSON_AS_ASCII"] = value
            continue

        # ── Flask-SQLAlchemy keys removed in Flask-SQLAlchemy 3.x ───────────
        if key == "SQLALCHEMY_TRACK_MODIFICATIONS":
            warnings.warn(
                "Config key SQLALCHEMY_TRACK_MODIFICATIONS was removed in "
                "Flask-SQLAlchemy 3.0. Remove it from your config.",
                DeprecationWarning,
                stacklevel=2,
            )
            # Drop silently — no equivalent in Flask-SQLAlchemy 3.x.
            continue

        if key == "SQLALCHEMY_COMMIT_ON_TEARDOWN":
            warnings.warn(
                "Config key SQLALCHEMY_COMMIT_ON_TEARDOWN was removed. "
                "Use explicit db.session.commit() calls.",
                DeprecationWarning,
                stacklevel=2,
            )
            # TODO: Audit all request handlers to ensure explicit commits are present.
            continue

        # ── SQLAlchemy engine options moved to SQLALCHEMY_ENGINE_OPTIONS ─────
        if key == "SQLALCHEMY_POOL_SIZE":
            warnings.warn(
                "SQLALCHEMY_POOL_SIZE is deprecated. "
                "Use SQLALCHEMY_ENGINE_OPTIONS = {'pool_size': ...}.",
                DeprecationWarning,
                stacklevel=2,
            )
            engine_options["pool_size"] = value
            continue

        if key == "SQLALCHEMY_MAX_OVERFLOW":
            warnings.warn(
                "SQLALCHEMY_MAX_OVERFLOW is deprecated. "
                "Use SQLALCHEMY_ENGINE_OPTIONS = {'max_overflow': ...}.",
                DeprecationWarning,
                stacklevel=2,
            )
            engine_options["max_overflow"] = value
            continue

        if key == "SQLALCHEMY_POOL_TIMEOUT":
            warnings.warn(
                "SQLALCHEMY_POOL_TIMEOUT is deprecated. "
                "Use SQLALCHEMY_ENGINE_OPTIONS = {'pool_timeout': ...}.",
                DeprecationWarning,
                stacklevel=2,
            )
            engine_options["pool_timeout"] = value
            continue

        if key == "SQLALCHEMY_POOL_RECYCLE":
            warnings.warn(
                "SQLALCHEMY_POOL_RECYCLE is deprecated. "
                "Use SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': ...}.",
                DeprecationWarning,
                stacklevel=2,
            )
            engine_options["pool_recycle"] = value
            continue

        # ── SERVER_NAME warning ──────────────────────────────────────────────
        if key == "SERVER_NAME" and value:
            warnings.warn(
                "SERVER_NAME is set. In Flask 2.x+ this affects subdomain matching "
                "and URL generation. Verify it is still correct for your deployment.",
                UserWarning,
                stacklevel=2,
            )
            new_config[key] = value
            continue

        # ── Pass through all other keys unchanged ────────────────────────────
        new_config[key] = value

    # Merge collected engine options
    if engine_options:
        existing = new_config.get("SQLALCHEMY_ENGINE_OPTIONS", {})
        existing.update(engine_options)
        new_config["SQLALCHEMY_ENGINE_OPTIONS"] = existing

    # ── Inject new health/readiness config keys if absent ───────────────────
    new_config.setdefault("HEALTH_SERVICE_NAME", os.environ.get("SERVICE_NAME", "service"))
    new_config.setdefault("READINESS_CHECKS", [])

    # TODO: Populate READINESS_CHECKS with callables that verify your database
    # connection and any other downstream dependencies required before the service
    # is considered ready to accept traffic (see /api/ready endpoint below).

    return new_config


def apply_compat_json_settings(app: "Flask", migrated_config: Dict[str, Any]) -> None:
    """
    Applies the _COMPAT_* keys produced by migrate_config() to the Flask app's
    json provider, which is the correct location in Flask 3.x.

    Call this immediately after app creation and config loading.
    """
    if not _FLASK_AVAILABLE:
        return

    if "_COMPAT_JSON_SORT_KEYS" in migrated_config:
        app.json.sort_keys = migrated_config["_COMPAT_JSON_SORT_KEYS"]  # type: ignore[attr-defined]

    if "_COMPAT_JSON_AS_ASCII" in migrated_config:
        app.json.ensure_ascii = migrated_config["_COMPAT_JSON_AS_ASCII"]  # type: ignore[attr-defined]

    # TODO: JSONIFY_PRETTYPRINT_REGULAR has no direct equivalent in Flask 3.x's
    # DefaultJSONProvider. To enable pretty-printing, subclass DefaultJSONProvider
    # and override dumps() to pass indent=2. See Flask 3.x docs.


# ===========================================================================
# SECTION 4 — /api/health and /api/ready Blueprint
# ===========================================================================

def create_health_blueprint(
    service_name: str = "service",
    readiness_checks: Optional[list[Callable[[], bool]]] = None,
) -> "Blueprint":
    """
    Creates and returns a Flask Blueprint that registers:

      GET /api/health  — liveness probe (always 200 if the process is alive)
      GET /api/ready   — readiness probe (200 if all readiness_checks pass, 503 otherwise)

    This matches the endpoint contract defined in spec.md:
      - /api/health response: { status, service, timestamp }
      - /api/ready  response: { status, service, timestamp, checks: { <name>: bool } }

    Parameters
    ----------
    service_name:
        Value for the "service" field in the response body.
        Defaults to the SERVICE_NAME environment variable or "service".
    readiness_checks:
        List of zero-argument callables that return True (ready) or False (not ready).
        Each callable should be named (its __name__ is used as the check key).

    TODO: Add actual readiness check callables for:
          - Database connectivity (e.g. db.session.execute(text("SELECT 1")))
          - Any required downstream HTTP dependencies
          - Cache / Redis connectivity if applicable
    """
    if not _FLASK_AVAILABLE:
        raise RuntimeError("Flask is not installed.")

    if readiness_checks is None:
        readiness_checks = []

    health_bp = Blueprint("health", __name__)

    @health_bp.get("/api/health")
    def liveness() -> Any:
        """
        Liveness probe — returns 200 as long as the Python process is running.
        No dependency checks are performed here by design.

        Response shape (matches spec.md):
          { "status": "ok", "service": "<name>", "timestamp": "<ISO-8601>" }
        """
        body = {
            "status": "ok",
            "service": service_name,
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return jsonify(body), 200

    @health_bp.get("/api/ready")
    def readiness() -> Any:
        """
        Readiness probe — runs all registered readiness_checks.
        Returns 200 if all checks pass, 503 if any check fails.

        Response shape (matches spec.md):
          {
            "status": "ready" | "not_ready",
            "service": "<name>",
            "timestamp": "<ISO-8601>",
            "checks": { "<check_name>": true | false, ... }
          }

        TODO: Wire in real dependency checks via the readiness_checks parameter.
        """
        check_results: Dict[str, bool] = {}
        all_ready = True

        for check_fn in readiness_checks:
            check_name = getattr(check_fn, "__name__", str(check_fn))
            try:
                result = bool(check_fn())
            except Exception:
                result = False
            check_results[check_name] = result
            if not result:
                all_ready = False

        status_str = "ready" if all_ready else "not_ready"
        http_status = 200 if all_ready else 503

        body = {
            "status": status_str,
            "service": service_name,
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "checks": check_results,
        }
        return jsonify(body), http_status

    return health_bp


def register_health_endpoints(
    app: "Flask",
    service_name: Optional[str] = None,
    readiness_checks: Optional[list[Callable[[], bool]]] = None,
) -> None:
    """
    Convenience function: creates the health blueprint and registers it on app.

    Parameters
    ----------
    app:
        The Flask application instance.
    service_name:
        Overrides the service name in health responses.
        Falls back to app.config.get("HEALTH_SERVICE_NAME") or SERVICE_NAME env var.
    readiness_checks:
        List of zero-argument callables returning bool.
        Falls back to app.config.get("READINESS_CHECKS", []).

    Example usage in an application factory:

        from migration_shim import register_health_endpoints

        def create_app(config=None):
            app = Flask(__name__)
            # ... load config, init extensions ...
            register_health_endpoints(app)
            return app

    TODO: Pass actual readiness check callables once database and other
    dependencies are initialised. Example:

        def check_db():
            from myapp.extensions import db
            db.session.execute(text("SELECT 1"))
            return True

        register_health_endpoints(app, readiness_checks=[check_db])
    """
    if not _FLASK_AVAILABLE:
        raise RuntimeError("Flask is not installed.")

    resolved_name: str = (
        service_name
        or app.config.get("HEALTH_SERVICE_NAME")
        or os.environ.get("SERVICE_NAME", "service")
    )

    resolved_checks: list[Callable[[], bool]] = (
        readiness_checks
        if readiness_checks is not None
        else app.config.get("READINESS_CHECKS", [])
    )

    bp = create_health_blueprint(
        service_name=resolved_name,
        readiness_checks=resolved_checks,
    )
    app.register_blueprint(bp)


# ===========================================================================
# SECTION 5 — SQLAlchemy readiness check helper
# ===========================================================================

def make_sqlalchemy_readiness_check(db_session_factory: Callable) -> Callable[[], bool]:
    """
    Returns a readiness check callable that verifies the database is reachable
    by executing a lightweight SELECT 1 query.

    Parameters
    ----------
    db_session_factory:
        A zero-argument callable that returns a SQLAlchemy Session, or a
        Flask-SQLAlchemy db object (pass db.session).

    Usage:

        from migration_shim import make_sqlalchemy_readiness_check, register_health_endpoints
        from myapp.extensions import db

        def create_app():
            app = Flask(__name__)
            db.init_app(app)
            check_db = make_sqlalchemy_readiness_check(lambda: db.session)
            register_health_endpoints(app, readiness_checks=[check_db])
            return app

    TODO: If your app uses async SQLAlchemy (AsyncSession), this synchronous
    check will not work. Implement an async readiness check and use an async
    Flask view instead.
    """
    if not _SA_AVAILABLE:
        raise RuntimeError("SQLAlchemy is not installed.")

    def check_database() -> bool:
        try:
            session = db_session_factory()
            session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    check_database.__name__ = "database"
    return check_database


# ===========================================================================
# SECTION 6 — Standalone demo / smoke test
# ===========================================================================

def _build_demo_app() -> "Flask":
    """
    Builds a minimal Flask 3.x application with /api/health and /api/ready
    endpoints registered, demonstrating the shim in action.

    This is NOT production code — it is a smoke-test entry point.
    """
    if not _FLASK_AVAILABLE:
        raise RuntimeError("Flask is not installed.")

    app = Flask(__name__)

    # ── Migrate an example old-style config ─────────────────────────────────
    old_config: Dict[str, Any] = {
        "DEBUG": False,
        "SECRET_KEY": os.environ.get("SECRET_KEY", "change-me"),
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL", "sqlite:///:memory:"),
        # Old keys that must be migrated:
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JSON_SORT_KEYS": False,
        "JSONIFY_PRETTYPRINT_REGULAR": False,
        "SQLALCHEMY_POOL_SIZE": 5,
        "SQLALCHEMY_MAX_OVERFLOW": 10,
    }

    new_config = migrate_config(old_config)
    app.config.update(new_config)
    apply_compat_json_settings(app, new_config)

    # ── Apply before_first_request shim ─────────────────────────────────────
    shim = FlaskCompatShim(app)

    @shim.before_first_request
    def _on_first_request() -> None:
        app.logger.info("First request received — running startup tasks.")
        # TODO: Place any one-time startup logic here (e.g. warm caches).

    # ── Register health + readiness endpoints ────────────────────────────────
    # TODO: Replace the lambda below with a real database readiness check once
    # SQLAlchemy is initialised. See make_sqlalchemy_readiness_check().
    def _always_ready() -> bool:
        return True

    _always_ready.__name__ = "stub_always_ready"

    register_health_endpoints(
        app,
        service_name="payment-service",
        readiness_checks=[_always_ready],
    )

    return app


if __name__ == "__main__":
    demo_app = _build_demo_app()
    port = int(os.environ.get("PORT", 5000))
    # TODO: Do not use app.run() in production. Use a WSGI server such as
    # gunicorn or waitress: `gunicorn "migration_shim:_build_demo_app()"`
    demo_app.run(host="0.0.0.0", port=port, debug=False)