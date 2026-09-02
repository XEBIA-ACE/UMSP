# migration_shim.py
# Compatibility shim for Flask 1.x -> 3.1 and SQLAlchemy 1.3 -> 2.0 migration
# Generated for Python 3.8 -> 3.12/3.13 upgrade with GitHub Actions CI integration

import os
import sys
import warnings
import functools
import importlib
from typing import Any, Callable, Dict, Optional, Type

# ---------------------------------------------------------------------------
# Python version guard
# ---------------------------------------------------------------------------
if sys.version_info < (3, 10):
    warnings.warn(
        "This shim targets Python 3.12/3.13. "
        "Running on Python {}.{} may produce unexpected behaviour.".format(
            sys.version_info.major, sys.version_info.minor
        ),
        RuntimeWarning,
        stacklevel=2,
    )

# ===========================================================================
# SECTION 1: Flask 1.x -> 3.1 compatibility shim
# ===========================================================================

def _flask_available() -> bool:
    return importlib.util.find_spec("flask") is not None


if _flask_available():
    import flask
    from flask import Flask, Blueprint, request, jsonify, g, current_app

    # -----------------------------------------------------------------------
    # 1a. Application factory pattern shim
    #     Flask 3.x strongly recommends the application factory pattern.
    #     If legacy code calls `app = Flask(__name__)` at module level and
    #     then uses `app.run()` directly, wrap it here.
    # -----------------------------------------------------------------------

    def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
        """
        Application factory compatible with Flask 3.1.

        Replace any top-level `app = Flask(__name__)` usage with a call to
        this factory, or adapt this function to wrap your existing app
        initialisation logic.

        TODO: Merge your existing app initialisation code (blueprints,
              extensions, error handlers) into this factory body.
              See Flask 3.x breaking change: application context is no longer
              pushed automatically outside of a request/CLI context.
        """
        app = Flask(__name__)

        # Load default config from environment variables (replaces hardcoded values)
        app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", ""))
        app.config.setdefault("DEBUG", os.environ.get("FLASK_DEBUG", "0") == "1")

        # TODO: Replace any hardcoded DATABASE_URI with an environment variable.
        #       Flask 3.x does not change this behaviour, but the upgrade is a
        #       good opportunity to enforce it.
        app.config.setdefault(
            "SQLALCHEMY_DATABASE_URI",
            os.environ.get("DATABASE_URL", "sqlite:///app.db"),
        )

        if config:
            app.config.update(config)

        return app

    # -----------------------------------------------------------------------
    # 1b. Removed: flask.ext namespace (removed in Flask 1.0, absent in 3.x)
    #     Provide a clear error rather than a silent import failure.
    # -----------------------------------------------------------------------

    class _FlaskExtShim:
        """
        Shim for the removed `flask.ext.*` import namespace.
        Flask 3.x does not include flask.ext at all.
        """
        def __getattr__(self, name: str) -> Any:
            raise ImportError(
                "flask.ext.{name} is not available in Flask 3.x. "
                "Import the extension directly, e.g. `from flask_{name} import ...`. "
                "TODO: Update all `from flask.ext.{name}` imports in your codebase.".format(
                    name=name
                )
            )

    # Patch flask.ext if it doesn't already exist (it won't in Flask 3.x)
    if not hasattr(flask, "ext"):
        flask.ext = _FlaskExtShim()  # type: ignore[attr-defined]

    # -----------------------------------------------------------------------
    # 1c. flask.json provider changes (Flask 2.2+)
    #     `flask.json.jsonify` and `flask.json.dumps` signatures are unchanged
    #     but the underlying provider changed. Provide a safe wrapper.
    # -----------------------------------------------------------------------

    def safe_jsonify(*args: Any, **kwargs: Any):
        """
        Drop-in replacement for flask.jsonify that is safe under Flask 3.1.
        Flask 3.x uses a JSON provider; custom encoders set via
        `app.json_encoder` are no longer supported.

        TODO: If you subclassed `flask.json.JSONEncoder` and assigned it to
              `app.json_encoder`, migrate to `app.json_provider_class` using
              `flask.json.provider.DefaultJSONProvider` as the base class.
              Breaking change introduced in Flask 2.2, enforced in Flask 3.x.
        """
        return jsonify(*args, **kwargs)

    # -----------------------------------------------------------------------
    # 1d. Deprecated: `before_first_request` decorator removed in Flask 3.x
    #     Provide a compatibility wrapper that uses `with app.app_context()`.
    # -----------------------------------------------------------------------

    def before_first_request_compat(app_instance: Flask, func: Callable) -> Callable:
        """
        Replacement for the removed `@app.before_first_request` decorator.

        Flask 3.x removed `before_first_request`. Use this helper to run
        one-time initialisation inside the application factory instead.

        Usage:
            # Old (Flask 1.x):
            @app.before_first_request
            def init_db():
                db.create_all()

            # New (Flask 3.x) — call inside create_app():
            before_first_request_compat(app, init_db)

        TODO: Move all `@app.before_first_request` decorated functions into
              your application factory or a CLI command.
              See Flask 3.x breaking change: `before_first_request` removed.
        """
        with app_instance.app_context():
            func()
        return func

    # -----------------------------------------------------------------------
    # 1e. Deprecated: `app.send_static_file` path traversal behaviour changed
    #     No shim needed but flag for manual review.
    # TODO: Review any direct calls to `app.send_static_file()` or
    #       `send_from_directory()`. Flask 3.x raises 404 (not 403) for
    #       paths outside the static folder. Adjust error handling accordingly.
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # 1f. Removed: `flask._app_ctx_stack` and `flask._request_ctx_stack`
    #     These private APIs were removed in Flask 3.x.
    # TODO: Replace any usage of `flask._app_ctx_stack` or
    #       `flask._request_ctx_stack` with `flask.g` or
    #       `flask.current_app` / `flask.request` proxies.
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # 1g. `flask.escape` removed — moved to markupsafe
    # -----------------------------------------------------------------------
    try:
        from flask import escape as _flask_escape  # noqa: F401 — present in Flask 1.x
    except ImportError:
        try:
            from markupsafe import escape  # Flask 3.x: use markupsafe directly
            # Re-export under the old name for legacy import compatibility
            flask.escape = escape  # type: ignore[attr-defined]
        except ImportError:
            pass  # markupsafe not installed; will fail at runtime with a clear error

    # -----------------------------------------------------------------------
    # 1h. `flask.Markup` removed — moved to markupsafe
    # -----------------------------------------------------------------------
    try:
        from flask import Markup as _flask_Markup  # noqa: F401 — present in Flask 1.x
    except ImportError:
        try:
            from markupsafe import Markup
            flask.Markup = Markup  # type: ignore[attr-defined]
        except ImportError:
            pass

else:
    warnings.warn("Flask is not installed. Flask shims skipped.", ImportWarning, stacklevel=2)


# ===========================================================================
# SECTION 2: SQLAlchemy 1.3 -> 2.0 compatibility shim
# ===========================================================================

def _sqlalchemy_available() -> bool:
    return importlib.util.find_spec("sqlalchemy") is not None


if _sqlalchemy_available():
    import sqlalchemy
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, MappedColumn

    # -----------------------------------------------------------------------
    # 2a. Legacy declarative base shim
    #     SQLAlchemy 1.3 used `declarative_base()` from sqlalchemy.ext.declarative.
    #     SQLAlchemy 2.0 uses `DeclarativeBase` as a base class.
    # -----------------------------------------------------------------------

    try:
        # Still importable in SQLAlchemy 2.0 with a deprecation warning
        from sqlalchemy.orm import declarative_base as _sa2_declarative_base

        def declarative_base(*args: Any, **kwargs: Any):
            """
            Compatibility wrapper for `sqlalchemy.ext.declarative.declarative_base`.

            SQLAlchemy 2.0 deprecates the function form. Prefer subclassing
            `sqlalchemy.orm.DeclarativeBase` directly.

            TODO: Migrate all models from:
                Base = declarative_base()
                class MyModel(Base): ...
            to:
                class Base(DeclarativeBase): pass
                class MyModel(Base): ...
            See SQLAlchemy 2.0 migration guide: declarative_base() removal.
            """
            warnings.warn(
                "declarative_base() is deprecated in SQLAlchemy 2.0. "
                "Subclass sqlalchemy.orm.DeclarativeBase instead. "
                "TODO: Migrate your model base classes.",
                DeprecationWarning,
                stacklevel=2,
            )
            return _sa2_declarative_base(*args, **kwargs)

    except ImportError:
        # SQLAlchemy 2.0 final removed it entirely; provide a stub
        def declarative_base(*args: Any, **kwargs: Any):  # type: ignore[misc]
            raise ImportError(
                "declarative_base() has been removed in SQLAlchemy 2.0. "
                "TODO: Subclass sqlalchemy.orm.DeclarativeBase directly."
            )

    # Re-export under the old import path for legacy code
    try:
        import sqlalchemy.ext.declarative as _sa_ext_decl
        if not hasattr(_sa_ext_decl, "declarative_base"):
            _sa_ext_decl.declarative_base = declarative_base  # type: ignore[attr-defined]
    except ImportError:
        pass

    # -----------------------------------------------------------------------
    # 2b. Session usage shim
    #     SQLAlchemy 1.3: `session.execute(string_sql)`
    #     SQLAlchemy 2.0: `session.execute(text(string_sql))`
    # -----------------------------------------------------------------------

    class LegacySessionWrapper:
        """
        Wraps a SQLAlchemy 2.0 Session to accept raw string SQL in execute(),
        matching the SQLAlchemy 1.3 behaviour.

        TODO: Replace all raw string SQL passed to session.execute() with
              `sqlalchemy.text()` calls and remove this wrapper.
              SQLAlchemy 2.0 breaking change: session.execute() no longer
              accepts plain strings.
        """

        def __init__(self, session: Session) -> None:
            self._session = session

        def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
            if isinstance(statement, str):
                warnings.warn(
                    "Passing raw strings to session.execute() is not supported "
                    "in SQLAlchemy 2.0. Wrapping with text() automatically. "
                    "TODO: Replace with session.execute(text('...')).",
                    DeprecationWarning,
                    stacklevel=2,
                )
                statement = text(statement)
            return self._session.execute(statement, *args, **kwargs)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._session, name)

    def get_legacy_session(session: Session) -> LegacySessionWrapper:
        """Return a LegacySessionWrapper around a SQLAlchemy 2.0 Session."""
        return LegacySessionWrapper(session)

    # -----------------------------------------------------------------------
    # 2c. Query API shim
    #     SQLAlchemy 1.3: `session.query(Model).filter(...).all()`
    #     SQLAlchemy 2.0: `session.execute(select(Model).where(...)).scalars().all()`
    #
    # TODO: Migrate all `session.query(...)` calls to the new `select()` style.
    #       The legacy Query API is available via `sqlalchemy.orm.Query` in 2.0
    #       but is deprecated and will be removed in a future version.
    #       Enable legacy query interface by passing `query_cls` to sessionmaker
    #       only as a temporary bridge — do not rely on it long-term.
    # -----------------------------------------------------------------------

    def make_legacy_query_session_factory(engine: Any) -> Any:
        """
        Creates a sessionmaker that still supports the legacy Query API.

        TODO: This is a temporary bridge. Migrate all session.query() calls
              to select() + session.execute() and remove this factory.
        """
        try:
            from sqlalchemy.orm import Query
            warnings.warn(
                "Legacy Query API is deprecated in SQLAlchemy 2.0. "
                "TODO: Migrate to select() + session.execute().",
                DeprecationWarning,
                stacklevel=2,
            )
            return sessionmaker(bind=engine, query_cls=Query)
        except Exception:
            return sessionmaker(bind=engine)

    # -----------------------------------------------------------------------
    # 2d. `engine.execute()` removed in SQLAlchemy 2.0
    #     Provide a compatibility function.
    # -----------------------------------------------------------------------

    def engine_execute(engine: Any, statement: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Compatibility replacement for the removed `engine.execute()`.

        SQLAlchemy 2.0 breaking change: `engine.execute()` was removed.
        Use a connection context manager instead.

        TODO: Replace all `engine.execute(...)` calls with:
              with engine.connect() as conn:
                  result = conn.execute(text('...'))
        """
        warnings.warn(
            "engine.execute() has been removed in SQLAlchemy 2.0. "
            "Use `with engine.connect() as conn: conn.execute(text(...))`. "
            "TODO: Migrate all engine.execute() call sites.",
            DeprecationWarning,
            stacklevel=2,
        )
        if isinstance(statement, str):
            statement = text(statement)
        with engine.connect() as conn:
            return conn.execute(statement, *args, **kwargs)

    # -----------------------------------------------------------------------
    # 2e. `Column` type annotation changes
    #     SQLAlchemy 2.0 introduces `Mapped[...]` + `mapped_column()`.
    #     Legacy `Column` still works but triggers deprecation warnings.
    #
    # TODO: Migrate model column definitions from:
    #       id = Column(Integer, primary_key=True)
    #   to:
    #       id: Mapped[int] = mapped_column(primary_key=True)
    #   See SQLAlchemy 2.0 ORM migration guide.
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # 2f. `relationship()` `backref` -> `back_populates`
    #
    # TODO: Replace `backref=` keyword arguments in `relationship()` with
    #       explicit `back_populates=` on both sides of the relationship.
    #       `backref` still works in SQLAlchemy 2.0 but emits a deprecation
    #       warning and will be removed in a future version.
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # 2g. Autocommit mode removed
    #
    # TODO: If you used `engine = create_engine(..., execution_options={"autocommit": True})`
    #       or `connection.execution_options(autocommit=True)`, migrate to
    #       explicit transaction management:
    #           with engine.begin() as conn:
    #               conn.execute(...)
    #       SQLAlchemy 2.0 breaking change: DBAPI-level autocommit is the only
    #       supported autocommit mode; SQLAlchemy-level autocommit was removed.
    # -----------------------------------------------------------------------

else:
    warnings.warn(
        "SQLAlchemy is not installed. SQLAlchemy shims skipped.", ImportWarning, stacklevel=2
    )


# ===========================================================================
# SECTION 3: Config format migration helper
# ===========================================================================

def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a legacy Flask 1.x / SQLAlchemy 1.3 config dict into a
    format compatible with Flask 3.1 / SQLAlchemy 2.0.

    Args:
        old_config: Dictionary representing the old application configuration.

    Returns:
        A new dictionary with keys and values updated for the new stack.
    """
    new_config: Dict[str, Any] = {}

    for key, value in old_config.items():
        # --- Flask config key renames / deprecations ---

        if key == "SQLALCHEMY_TRACK_MODIFICATIONS":
            # Deprecated in Flask-SQLAlchemy 3.x; default is now False.
            # Silently drop it (setting it to False is the new default).
            warnings.warn(
                "SQLALCHEMY_TRACK_MODIFICATIONS is deprecated and has no effect "
                "in Flask-SQLAlchemy 3.x. Removing from config.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "SQLALCHEMY_DATABASE_URI" and isinstance(value, str):
            # SQLAlchemy 2.0: `postgres://` scheme renamed to `postgresql://`
            if value.startswith("postgres://"):
                warnings.warn(
                    "Database URI uses deprecated 'postgres://' scheme. "
                    "Replacing with 'postgresql://' for SQLAlchemy 2.0 compatibility.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                value = value.replace("postgres://", "postgresql://", 1)
            new_config[key] = value
            continue

        if key == "SECRET_KEY" and (not value or value in ("dev", "development", "secret", "changeme")):
            # TODO: Replace hardcoded SECRET_KEY values with a secrets manager
            #       or environment variable injection. Hardcoded credentials are
            #       a security risk flagged by SAST tools (e.g. Bandit B105/B106).
            warnings.warn(
                "SECRET_KEY appears to be a hardcoded insecure value: '{}'. "
                "TODO: Inject SECRET_KEY via the SECRET_KEY environment variable "
                "or a secrets manager. This will be flagged by SAST (Bandit B105).".format(value),
                UserWarning,
                stacklevel=2,
            )
            new_config[key] = os.environ.get("SECRET_KEY", value)
            continue

        if key == "DEBUG" and isinstance(value, str):
            # Normalise string "True"/"False" to bool for Flask 3.x
            new_config[key] = value.lower() in ("1", "true", "yes")
            continue

        if key == "TESTING" and isinstance(value, str):
            new_config[key] = value.lower() in ("1", "true", "yes")
            continue

        if key == "PROPAGATE_EXCEPTIONS":
            # TODO: Flask 3.x changed exception propagation defaults.
            #       Review whether explicit PROPAGATE_EXCEPTIONS=True is still needed.
            new_config[key] = value
            continue

        if key == "JSON_SORT_KEYS":
            # Flask 3.x: configure via app.json.sort_keys instead of config key.
            # TODO: Replace `app.config["JSON_SORT_KEYS"]` with
            #       `app.json.sort_keys = <value>` after app creation.
            warnings.warn(
                "JSON_SORT_KEYS config key is not supported in Flask 3.x. "
                "TODO: Set app.json.sort_keys = {} after app creation.".format(value),
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "JSON_AS_ASCII":
            # Flask 3.x: configure via app.json.ensure_ascii instead.
            # TODO: Replace `app.config["JSON_AS_ASCII"]` with
            #       `app.json.ensure_ascii = <value>` after app creation.
            warnings.warn(
                "JSON_AS_ASCII config key is not supported in Flask 3.x. "
                "TODO: Set app.json.ensure_ascii = {} after app creation.".format(value),
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "JSONIFY_PRETTYPRINT_REGULAR":
            # Removed in Flask 3.x.
            # TODO: Use app.json.compact = False instead.
            warnings.warn(
                "JSONIFY_PRETTYPRINT_REGULAR is removed in Flask 3.x. "
                "TODO: Set app.json.compact = False after app creation.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "JSONIFY_MIMETYPE":
            # TODO: Flask 3.x uses the JSON provider; set mimetype on the provider.
            warnings.warn(
                "JSONIFY_MIMETYPE is not supported in Flask 3.x. "
                "TODO: Customise the JSON provider if a non-default mimetype is required.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue

        if key == "TEMPLATES_AUTO_RELOAD":
            # Still supported but behaviour changed slightly in Flask 3.x.
            # TODO: Verify template auto-reload behaviour in Flask 3.x matches expectations.
            new_config[key] = value
            continue

        # --- SQLAlchemy engine option renames ---

        if key == "SQLALCHEMY_POOL_SIZE":
            new_config[key] = value
            continue

        if key == "SQLALCHEMY_ENGINE_OPTIONS" and isinstance(value, dict):
            # SQLAlchemy 2.0: `convert_unicode` option removed from engine options.
            if "convert_unicode" in value:
                warnings.warn(
                    "SQLALCHEMY_ENGINE_OPTIONS['convert_unicode'] is removed in "
                    "SQLAlchemy 2.0. Removing from engine options.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                value = {k: v for k, v in value.items() if k != "convert_unicode"}
            new_config[key] = value
            continue

        # Default: pass through unchanged
        new_config[key] = value

    return new_config


# ===========================================================================
# SECTION 4: Environment variable / secrets injection helper
# ===========================================================================

def assert_required_env_vars(*var_names: str) -> None:
    """
    Assert that all required environment variables are set.

    Call this at application startup to catch missing secrets early.

    TODO: Add all variables that previously held hardcoded credentials to
          this list. SAST tools (Bandit B105/B106/B107) will flag hardcoded
          passwords and secret keys — replace them with environment variables
          and validate here.
    """
    missing = [v for v in var_names if not os.environ.get(v)]
    if missing:
        raise EnvironmentError(
            "Required environment variables are not set: {}. "
            "TODO: Set these variables in your deployment environment or .env file. "
            "Never hardcode credentials in source code.".format(", ".join(missing))
        )


# ===========================================================================
# SECTION 5: GitHub Actions CI workflow generator
# ===========================================================================

GITHUB_ACTIONS_WORKFLOW = """\
# .github/workflows/ci.yml
# Generated by migration_shim.py
# Provides lint, SAST, and test stages for Python 3.12 + Flask 3.1 + SQLAlchemy 2.0

name: CI

on:
  push:
    branches: ["main", "master"]
  pull_request:
    branches: ["main", "master"]

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install lint dependencies
        run: |
          pip install --upgrade pip
          pip install flake8 black isort
      - name: Run flake8
        run: flake8 .
      - name: Run black (check mode)
        run: black --check .
      - name: Run isort (check mode)
        run: isort --check-only .

  sast:
    name: SAST (Bandit)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install Bandit
        run: pip install bandit[toml]
      - name: Run Bandit
        # TODO: Adjust the target path to match your source directory.
        # Bandit will flag hardcoded credentials (B105, B106, B107) and
        # other common security issues introduced during the Flask/SQLAlchemy upgrade.
        run: bandit -r . -ll --exclude ./.venv,./tests

  test:
    name: Test
    runs-on: ubuntu-latest
    env:
      # TODO: Add all required secrets as GitHub Actions secrets and reference
      #       them here. Never hardcode credentials in this file.
      SECRET_KEY: ${{ secrets.SECRET_KEY }}
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
"""


def write_github_actions_workflow(output_path: str = ".github/workflows/ci.yml") -> None:
    """
    Write the GitHub Actions CI workflow file to the repository.

    Creates the .github/workflows/ directory if it does not exist.

    TODO: Review the generated workflow and customise:
          - The Python version (currently 3.12; change to 3.13 if desired).
          - The source directory passed to Bandit (-r .).
          - Any additional test dependencies or environment variables.
          - Branch names if your default branch is not 'main' or 'master'.
    """
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(GITHUB_ACTIONS_WORKFLOW)
    print("GitHub Actions workflow written to: {}".format(output_path))


# ===========================================================================
# SECTION 6: requirements.txt pin helper
# ===========================================================================

RECOMMENDED_PINS = {
    "Flask": ">=3.1,<4.0",
    "SQLAlchemy": ">=2.0,<3.0",
    "Flask-SQLAlchemy": ">=3.1,<4.0",
    "Werkzeug": ">=3.1,<4.0",
    "markupsafe": ">=2.1,<3.0",
    "flake8": ">=7.0",
    "black": ">=24.0",
    "isort": ">=5.13",
    "bandit": ">=1.7",
    "pytest": ">=8.0",
    "pytest-cov": ">=5.0",
}


def print_recommended_pins() -> None:
    """
    Print recommended package version pins for the upgraded stack.

    TODO: Merge these pins into your requirements.txt / pyproject.toml.
          Run `pip install -r requirements.txt` and resolve any conflicts.
    """
    print("# Recommended version pins for Flask 3.1 + SQLAlchemy 2.0 + Python 3.12")
    for package, pin in RECOMMENDED_PINS.items():
        print("{package}{pin}".format(package=package, pin=pin))


# ===========================================================================
# SECTION 7: Self-test / smoke check
# ===========================================================================

def run_smoke_checks() -> None:
    """
    Run basic smoke checks to verify the shim loaded correctly and the
    installed package versions are within expected ranges.
    """
    print("=== migration_shim.py smoke checks ===")

    # Python version
    py_ver = sys.version_info
    print("Python: {}.{}.{}".format(py_ver.major, py_ver.minor, py_ver.micro))
    if py_ver < (3, 12):
        print(
            "  WARNING: Python {}.{} detected. Target is 3.12+. "
            "TODO: Upgrade Python runtime.".format(py_ver.major, py_ver.minor)
        )

    # Flask version
    if _flask_available():
        import flask as _flask
        print("Flask: {}".format(_flask.__version__))
        major = int(_flask.__version__.split(".")[0])
        if major < 3:
            print(
                "  WARNING: Flask {} detected. Target is Flask 3.1+. "
                "TODO: Run `pip install 'Flask>=3.1,<4.0'`.".format(_flask.__version__)
            )
    else:
        print("Flask: NOT INSTALLED — TODO: pip install 'Flask>=3.1,<4.0'")

    # SQLAlchemy version
    if _sqlalchemy_available():
        import sqlalchemy as _sa
        print("SQLAlchemy: {}".format(_sa.__version__))
        major = int(_sa.__version__.split(".")[0])
        if major < 2:
            print(
                "  WARNING: SQLAlchemy {} detected. Target is SQLAlchemy 2.0+. "
                "TODO: Run `pip install 'SQLAlchemy>=2.0,<3.0'`.".format(_sa.__version__)
            )
    else:
        print("SQLAlchemy: NOT INSTALLED — TODO: pip install 'SQLAlchemy>=2.0,<3.0'")

    print("=== smoke checks complete ===")


# ===========================================================================
# Entry point: when run directly, write the CI workflow and print pins
# ===========================================================================

if __name__ == "__main__":
    run_smoke_checks()
    print()
    write_github_actions_workflow()
    print()
    print_recommended_pins()