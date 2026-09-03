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
import warnings
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Python version guard
# ---------------------------------------------------------------------------

if sys.version_info < (3, 12):
    warnings.warn(
        "This application targets Python 3.12+. "
        f"You are running Python {sys.version}. "
        "Please upgrade your runtime to Python 3.12 or 3.13.",
        DeprecationWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# Flask compatibility shim: Flask 1.x -> 3.1
# ---------------------------------------------------------------------------

try:
    import flask as _flask
    from flask import Flask

    _flask_version = tuple(int(x) for x in _flask.__version__.split(".")[:2])

    # ------------------------------------------------------------------
    # Deprecated: flask.json.jsonify / flask.json.dumps direct usage
    # Flask 3.x removed flask.json.JSONEncoder / flask.json.JSONDecoder
    # ------------------------------------------------------------------
    try:
        # TODO: If your code subclasses flask.json.JSONEncoder or
        # flask.json.JSONDecoder (removed in Flask 3.x), you must migrate
        # to using app.json_provider_class with flask.json.provider.DefaultJSONProvider.
        # See: https://flask.palletsprojects.com/en/3.0.x/api/#flask.json.provider
        from flask.json import JSONEncoder as _LegacyJSONEncoder  # noqa: F401

        warnings.warn(
            "flask.json.JSONEncoder is removed in Flask 3.x. "
            "Migrate to flask.json.provider.DefaultJSONProvider.",
            DeprecationWarning,
            stacklevel=2,
        )
    except ImportError:
        # Flask 3.x — JSONEncoder is already gone, which is expected
        pass

    # ------------------------------------------------------------------
    # Deprecated: before_first_request (removed in Flask 3.x)
    # ------------------------------------------------------------------
    # TODO: Replace all uses of @app.before_first_request with explicit
    # initialization calls inside the application factory (create_app).
    # Flask 3.x removed before_first_request entirely.
    # Ref: https://flask.palletsprojects.com/en/3.0.x/api/

    def _patched_before_first_request(app_instance: Flask):
        """
        Shim: @app.before_first_request was removed in Flask 3.x.
        This helper raises a clear error pointing to the correct migration path.
        """
        def decorator(f):
            raise RuntimeError(
                "before_first_request has been removed in Flask 3.x. "
                "Move initialization logic into your application factory "
                "(create_app) or use a with app.app_context(): block at startup."
            )
        return decorator

    if not hasattr(Flask, "before_first_request"):
        # Already removed — attach a helpful stub so existing code fails loudly
        Flask.before_first_request = _patched_before_first_request  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Deprecated: flask.signals (Blinker now required in Flask 3.x)
    # ------------------------------------------------------------------
    # TODO: Ensure blinker is listed in requirements.txt / pyproject.toml.
    # Flask 3.x requires blinker for signals; it was optional in Flask 1.x.

    # ------------------------------------------------------------------
    # Application factory pattern enforcement
    # ------------------------------------------------------------------
    # TODO: Migrate from a module-level `app = Flask(__name__)` pattern to
    # an application factory:
    #
    #   def create_app(config: dict | None = None) -> Flask:
    #       app = Flask(__name__)
    #       app.config.from_object(...)
    #       # register blueprints, extensions, etc.
    #       return app
    #
    # This is required for proper testing and extension initialization in Flask 3.x.

    def create_app_factory_template(config: Optional[Dict[str, Any]] = None) -> Flask:
        """
        Template application factory following Flask 3.x best practices.
        Replace the body of this function with your actual initialization logic.
        """
        app = Flask(__name__)

        # Load default config
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY", None),
            # TODO: Remove any hardcoded SECRET_KEY values and load from environment.
            # Hardcoded credentials are a security risk flagged in the upgrade targets.
        )

        if config is not None:
            app.config.from_mapping(config)

        # TODO: Register your blueprints here, e.g.:
        # from .routes import main_bp
        # app.register_blueprint(main_bp)

        return app

    # ------------------------------------------------------------------
    # Deprecated: flask.ext.* namespace (removed long ago, but guard anyway)
    # ------------------------------------------------------------------
    class _FlaskExtShim:
        """Raises ImportError with migration guidance for flask.ext.* imports."""
        def __getattr__(self, name: str):
            raise ImportError(
                f"flask.ext.{name} is not supported. "
                "Import Flask extensions directly, e.g. `import flask_{name}`."
            )

    sys.modules.setdefault("flask.ext", _FlaskExtShim())  # type: ignore[arg-type]

    logger.info("Flask shims applied (detected Flask %s).", _flask.__version__)

except ImportError:
    warnings.warn(
        "Flask is not installed. Flask shims were not applied.",
        ImportWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# SQLAlchemy compatibility shim: 1.3 -> 2.0
# ---------------------------------------------------------------------------

try:
    import sqlalchemy as sa

    _sa_version = tuple(int(x) for x in sa.__version__.split(".")[:2])

    # ------------------------------------------------------------------
    # Deprecated: Session.execute(string) — use text() wrapper in 2.0
    # ------------------------------------------------------------------
    try:
        from sqlalchemy.orm import Session as _Session
        from sqlalchemy import text as _sa_text

        _original_execute = _Session.execute

        def _shim_execute(self, statement, *args, **kwargs):
            if isinstance(statement, str):
                warnings.warn(
                    "Passing a raw string to Session.execute() is removed in "
                    "SQLAlchemy 2.0. Wrap your SQL with sqlalchemy.text(). "
                    "Example: session.execute(text('SELECT 1'))",
                    DeprecationWarning,
                    stacklevel=2,
                )
                statement = _sa_text(statement)
            return _original_execute(self, statement, *args, **kwargs)

        _Session.execute = _shim_execute  # type: ignore[method-assign]
    except Exception as exc:
        logger.debug("Could not patch Session.execute: %s", exc)

    # ------------------------------------------------------------------
    # Deprecated: Query API (session.query()) -> Select API (select())
    # ------------------------------------------------------------------
    # TODO: Migrate all session.query(Model).filter(...).all() calls to the
    # SQLAlchemy 2.0 select() API:
    #
    #   OLD (1.x):
    #       results = session.query(User).filter(User.active == True).all()
    #
    #   NEW (2.0):
    #       from sqlalchemy import select
    #       stmt = select(User).where(User.active == True)
    #       results = session.execute(stmt).scalars().all()
    #
    # The legacy Query API is available in 2.0 under legacy mode but will be
    # removed in a future version.

    # ------------------------------------------------------------------
    # Deprecated: declarative_base() moved in SQLAlchemy 2.0
    # ------------------------------------------------------------------
    try:
        from sqlalchemy.orm import declarative_base  # noqa: F401 — 2.0 location
    except ImportError:
        # SQLAlchemy 1.x — provide shim pointing to new location
        try:
            from sqlalchemy.ext.declarative import declarative_base as _old_base

            # Re-export under the new canonical path
            import sqlalchemy.orm as _sa_orm
            _sa_orm.declarative_base = _old_base  # type: ignore[attr-defined]

            warnings.warn(
                "sqlalchemy.ext.declarative.declarative_base has moved to "
                "sqlalchemy.orm.declarative_base in SQLAlchemy 2.0. "
                "Update your imports.",
                DeprecationWarning,
                stacklevel=2,
            )
        except ImportError:
            pass

    # ------------------------------------------------------------------
    # Deprecated: engine.execute() removed in SQLAlchemy 2.0
    # ------------------------------------------------------------------
    try:
        from sqlalchemy.engine import Engine as _Engine

        if hasattr(_Engine, "execute"):
            _original_engine_execute = _Engine.execute

            def _shim_engine_execute(self, statement, *args, **kwargs):
                warnings.warn(
                    "Engine.execute() is removed in SQLAlchemy 2.0. "
                    "Use a connection context instead:\n"
                    "  with engine.connect() as conn:\n"
                    "      result = conn.execute(text(...))",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return _original_engine_execute(self, statement, *args, **kwargs)

            _Engine.execute = _shim_engine_execute  # type: ignore[method-assign]
    except Exception as exc:
        logger.debug("Could not patch Engine.execute: %s", exc)

    # ------------------------------------------------------------------
    # Deprecated: autocommit / autoflush session flags behavior change
    # ------------------------------------------------------------------
    # TODO: SQLAlchemy 2.0 changes transaction handling. If you rely on
    # autocommit=True on Session or Connection, migrate to explicit
    # session.commit() / connection.commit() calls.
    # Ref: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html

    # ------------------------------------------------------------------
    # Deprecated: relationship() with string back_populates targets
    # ------------------------------------------------------------------
    # TODO: Verify all relationship() declarations use back_populates=
    # instead of backref= where possible. backref= still works in 2.0
    # but back_populates= is the recommended explicit form.

    # ------------------------------------------------------------------
    # Provide a 2.0-style mapped_column / Mapped type hint shim notice
    # ------------------------------------------------------------------
    # TODO: Consider migrating Column() declarations to the new 2.0
    # Mapped[] + mapped_column() style for full type-safety:
    #
    #   OLD (1.x / 2.0 compatible):
    #       class User(Base):
    #           id = Column(Integer, primary_key=True)
    #           name = Column(String)
    #
    #   NEW (2.0 preferred):
    #       from sqlalchemy.orm import Mapped, mapped_column
    #       class User(Base):
    #           id: Mapped[int] = mapped_column(primary_key=True)
    #           name: Mapped[str]

    logger.info("SQLAlchemy shims applied (detected SQLAlchemy %s).", sa.__version__)

except ImportError:
    warnings.warn(
        "SQLAlchemy is not installed. SQLAlchemy shims were not applied.",
        ImportWarning,
        stacklevel=2,
    )

# ---------------------------------------------------------------------------
# Config format migration helper
# ---------------------------------------------------------------------------

def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform an old Flask 1.x / SQLAlchemy 1.3 config dict into a
    Flask 3.x / SQLAlchemy 2.0 compatible config dict.

    Parameters
    ----------
    old_config:
        Dictionary representing the old application configuration.

    Returns
    -------
    Dict[str, Any]
        Migrated configuration dictionary.
    """
    new_config: Dict[str, Any] = {}

    for key, value in old_config.items():
        # ------------------------------------------------------------------
        # Flask config key renames / removals
        # ------------------------------------------------------------------

        if key == "SQLALCHEMY_TRACK_MODIFICATIONS":
            # Removed in Flask-SQLAlchemy 3.x; was deprecated since 2.x.
            # Default is now False; key should be omitted entirely.
            warnings.warn(
                "SQLALCHEMY_TRACK_MODIFICATIONS has been removed in "
                "Flask-SQLAlchemy 3.x. Remove this key from your config.",
                DeprecationWarning,
                stacklevel=2,
            )
            # Do not carry forward
            continue

        if key == "SQLALCHEMY_DATABASE_URI":
            # Validate that the URI does not contain hardcoded credentials.
            if isinstance(value, str) and (
                ("password" in value.lower() or "passwd" in value.lower())
                and "@" in value
                and not value.startswith("${")
                and not value.startswith("%(")
            ):
                # TODO: Replace hardcoded database credentials in
                # SQLALCHEMY_DATABASE_URI with an environment variable:
                #   SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
                warnings.warn(
                    "SQLALCHEMY_DATABASE_URI appears to contain hardcoded "
                    "credentials. Replace with os.environ['DATABASE_URL'] "
                    "or equivalent secrets management.",
                    UserWarning,
                    stacklevel=2,
                )
            new_config[key] = value
            continue

        if key == "SECRET_KEY":
            if isinstance(value, str) and value not in ("", None):
                # TODO: Remove hardcoded SECRET_KEY. Load from environment:
                #   SECRET_KEY = os.environ["SECRET_KEY"]
                warnings.warn(
                    "SECRET_KEY appears to be hardcoded. "
                    "Load it from an environment variable instead: "
                    "os.environ['SECRET_KEY']",
                    UserWarning,
                    stacklevel=2,
                )
            new_config[key] = value
            continue

        if key == "PROPAGATE_EXCEPTIONS":
            # Flask 3.x: PROPAGATE_EXCEPTIONS is still supported but
            # behavior around error handling changed. Verify your error
            # handlers are registered correctly.
            # TODO: Review error handler registration for Flask 3.x compatibility.
            new_config[key] = value
            continue

        if key == "JSON_SORT_KEYS":
            # Removed in Flask 3.x — configure via app.json.sort_keys instead.
            warnings.warn(
                "JSON_SORT_KEYS config key is removed in Flask 3.x. "
                "Set app.json.sort_keys = True/False after app creation.",
                DeprecationWarning,
                stacklevel=2,
            )
            # TODO: Set app.json.sort_keys in your application factory instead.
            continue

        if key == "JSON_AS_ASCII":
            # Removed in Flask 3.x — configure via app.json.ensure_ascii instead.
            warnings.warn(
                "JSON_AS_ASCII config key is removed in Flask 3.x. "
                "Set app.json.ensure_ascii = True/False after app creation.",
                DeprecationWarning,
                stacklevel=2,
            )
            # TODO: Set app.json.ensure_ascii in your application factory instead.
            continue

        if key == "JSONIFY_PRETTYPRINT_REGULAR":
            # Removed in Flask 3.x.
            warnings.warn(
                "JSONIFY_PRETTYPRINT_REGULAR is removed in Flask 3.x. "
                "Remove this key from your config.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "JSONIFY_MIMETYPE":
            # Removed in Flask 3.x — configure via app.json.mimetype instead.
            warnings.warn(
                "JSONIFY_MIMETYPE is removed in Flask 3.x. "
                "Set app.json.mimetype after app creation.",
                DeprecationWarning,
                stacklevel=2,
            )
            # TODO: Set app.json.mimetype in your application factory instead.
            continue

        if key == "TEMPLATES_AUTO_RELOAD":
            # Removed in Flask 3.x — now controlled by app.jinja_env.auto_reload.
            warnings.warn(
                "TEMPLATES_AUTO_RELOAD is removed in Flask 3.x. "
                "Set app.jinja_env.auto_reload directly.",
                DeprecationWarning,
                stacklevel=2,
            )
            # TODO: Set app.jinja_env.auto_reload in your application factory.
            continue

        # ------------------------------------------------------------------
        # SQLAlchemy engine option migrations
        # ------------------------------------------------------------------

        if key == "SQLALCHEMY_ENGINE_OPTIONS":
            engine_opts = dict(value) if value else {}

            if "use_batch_mode" in engine_opts:
                # TODO: use_batch_mode was a psycopg2 dialect option; verify
                # your psycopg2/psycopg3 driver configuration for SQLAlchemy 2.0.
                warnings.warn(
                    "SQLALCHEMY_ENGINE_OPTIONS['use_batch_mode'] may need "
                    "review for SQLAlchemy 2.0 + psycopg3 compatibility.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            if "convert_unicode" in engine_opts:
                # Removed in SQLAlchemy 2.0.
                warnings.warn(
                    "Engine option 'convert_unicode' is removed in "
                    "SQLAlchemy 2.0. Remove it from SQLALCHEMY_ENGINE_OPTIONS.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                del engine_opts["convert_unicode"]

            new_config[key] = engine_opts
            continue

        # Default: carry forward unchanged
        new_config[key] = value

    # ------------------------------------------------------------------
    # Inject required new defaults if missing
    # ------------------------------------------------------------------

    if "SECRET_KEY" not in new_config:
        # TODO: Ensure SECRET_KEY is set via environment variable in production.
        new_config["SECRET_KEY"] = os.environ.get("SECRET_KEY", None)
        if new_config["SECRET_KEY"] is None:
            warnings.warn(
                "SECRET_KEY is not set. Set the SECRET_KEY environment variable.",
                UserWarning,
                stacklevel=2,
            )

    return new_config


def migrate_config_file(input_path: str, output_path: str) -> None:
    """
    Read a Python config file, apply migrate_config() transformations,
    and write a migration report alongside the output path.

    NOTE: This performs a best-effort static analysis. Complex dynamic
    config files may require manual review.

    Parameters
    ----------
    input_path:
        Path to the existing config Python file.
    output_path:
        Path where the migrated config file will be written.
    """
    import ast
    import textwrap

    with open(input_path, "r", encoding="utf-8") as fh:
        source = fh.read()

    # Collect top-level assignments that look like config keys
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Could not parse {input_path}: {exc}") from exc

    removed_keys = {
        "SQLALCHEMY_TRACK_MODIFICATIONS",
        "JSON_SORT_KEYS",
        "JSON_AS_ASCII",
        "JSONIFY_PRETTYPRINT_REGULAR",
        "JSONIFY_MIMETYPE",
        "TEMPLATES_AUTO_RELOAD",
    }

    todo_keys = {
        "SECRET_KEY": (
            "# TODO: Load SECRET_KEY from environment variable:\n"
            "# SECRET_KEY = os.environ['SECRET_KEY']\n"
        ),
        "SQLALCHEMY_DATABASE_URI": (
            "# TODO: Load DATABASE_URL from environment variable:\n"
            "# SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']\n"
        ),
    }

    output_lines = [
        "# AUTO-GENERATED by migration_shim.py",
        "# Review all TODO comments before deploying.",
        "import os",
        "",
    ]

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    key = target.id
                    if key in removed_keys:
                        output_lines.append(
                            f"# REMOVED: {key} is no longer supported in the "
                            f"target framework version. See migration_shim.py."
                        )
                        continue
                    if key in todo_keys:
                        output_lines.append(todo_keys[key])

    # Append the original source with a header comment for manual review
    output_lines.append("")
    output_lines.append("# --- Original config below (review and update manually) ---")
    output_lines.append("")
    output_lines.append(source)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(output_lines))

    logger.info("Migrated config written to %s", output_path)
    print(f"[migration_shim] Migrated config written to: {output_path}")
    print("[migration_shim] Review all TODO comments in the output file.")


# ---------------------------------------------------------------------------
# Secrets / environment variable migration helpers
# ---------------------------------------------------------------------------

def assert_required_env_vars() -> None:
    """
    Assert that all required environment variables are present.
    Call this at application startup (inside create_app or __main__).

    TODO: Extend this list with any additional secrets your application requires.
    """
    required = [
        "SECRET_KEY",
        "DATABASE_URL",
        # TODO: Add additional required environment variable names here.
    ]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set these in your environment or a .env file (never commit secrets)."
        )


# ---------------------------------------------------------------------------
# CI/CD pipeline note
# ---------------------------------------------------------------------------
# TODO: Create .github/workflows/ci.yml with the following stages:
#
#   1. Lint:
#      - Use flake8 or ruff for Python linting.
#      - Use black --check for formatting.
#
#   2. Test:
#      - Run pytest with coverage reporting.
#      - Ensure tests pass on Python 3.12 and 3.13.
#
#   3. Security scan:
#      - Use pip-audit or safety to scan dependencies for known CVEs.
#      - Use bandit for static security analysis of Python source code.
#
#   Trigger on: push to main, pull_request targeting main.
#
#   Example workflow snippet (add to .github/workflows/ci.yml):
#
#   name: CI
#   on:
#     push:
#       branches: [main]
#     pull_request:
#       branches: [main]
#   jobs:
#     lint:
#       runs-on: ubuntu-latest
#       steps:
#         - uses: actions/checkout@v4
#         - uses: actions/setup-python@v5
#           with:
#             python-version: "3.12"
#         - run: pip install ruff black
#         - run: ruff check .
#         - run: black --check .
#     test:
#       runs-on: ubuntu-latest
#       steps:
#         - uses: actions/checkout@v4
#         - uses: actions/setup-python@v5
#           with:
#             python-version: "3.12"
#         - run: pip install -r requirements.txt
#         - run: pytest --tb=short --cov
#     security:
#       runs-on: ubuntu-latest
#       steps:
#         - uses: actions/checkout@v4
#         - uses: actions/setup-python@v5
#           with:
#             python-version: "3.12"
#         - run: pip install pip-audit bandit
#         - run: pip-audit
#         - run: bandit -r . -ll

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Migration shim helper for Flask 1.x->3.1 / SQLAlchemy 1.3->2.0 upgrade."
    )
    parser.add_argument(
        "--migrate-config",
        metavar="INPUT_CONFIG",
        help="Path to the existing Python config file to migrate.",
    )
    parser.add_argument(
        "--output",
        metavar="OUTPUT_CONFIG",
        default="config_migrated.py",
        help="Path for the migrated config output file (default: config_migrated.py).",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check that required environment variables are set.",
    )

    args = parser.parse_args()

    if args.migrate_config:
        migrate_config_file(args.migrate_config, args.output)

    if args.check_env:
        try:
            assert_required_env_vars()
            print("[migration_shim] All required environment variables are set.")
        except EnvironmentError as e:
            print(f"[migration_shim] ERROR: {e}")
            sys.exit(1)

    if not args.migrate_config and not args.check_env:
        parser.print_help()