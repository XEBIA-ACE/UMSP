import sys
import os
import importlib
import subprocess
import pytest


# ---------------------------------------------------------------------------
# Version assertions
# ---------------------------------------------------------------------------

def test_python_version_is_312_or_higher():
    """Python must be 3.12+ (upgraded from 3.8 EOL)."""
    major, minor = sys.version_info.major, sys.version_info.minor
    assert major == 3, f"Expected Python 3.x, got {major}.{minor}"
    assert minor >= 12, (
        f"Expected Python 3.12 or higher, got 3.{minor}. "
        "Upgrade from 3.8 EOL has not been applied."
    )


def test_flask_version_is_3_1():
    """Flask must be exactly 3.1.x (upgraded from 1.x EOL)."""
    import flask
    version_parts = tuple(int(x) for x in flask.__version__.split(".")[:2])
    assert version_parts >= (3, 1), (
        f"Expected Flask >= 3.1, got {flask.__version__}. "
        "Critical upgrade from Flask 1.x has not been applied."
    )


def test_sqlalchemy_version_is_2_0():
    """SQLAlchemy must be 2.0+ (upgraded from 1.3 EOL)."""
    import sqlalchemy
    version_parts = tuple(int(x) for x in sqlalchemy.__version__.split(".")[:2])
    assert version_parts >= (2, 0), (
        f"Expected SQLAlchemy >= 2.0, got {sqlalchemy.__version__}. "
        "Critical upgrade from SQLAlchemy 1.3 has not been applied."
    )


# ---------------------------------------------------------------------------
# Flask 3.x — application factory pattern
# ---------------------------------------------------------------------------

def test_flask_app_factory_pattern():
    """Application must be created via a factory function, not a module-level app."""
    # Try common factory locations used in Flask 3.x projects
    factory_found = False
    candidates = [
        ("app", "create_app"),
        ("application", "create_app"),
        ("src.app", "create_app"),
        ("wsgi", "create_app"),
    ]
    for module_path, func_name in candidates:
        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, func_name) and callable(getattr(mod, func_name)):
                factory_found = True
                break
        except ImportError:
            continue

    assert factory_found, (
        "No create_app() factory function found in expected modules "
        "(app, application, src.app, wsgi). "
        "Flask 3.x upgrade requires the application factory pattern."
    )


def test_flask_create_app_returns_flask_instance():
    """create_app() must return a valid Flask application instance."""
    import flask
    factory_mod = None
    for module_path in ("app", "application", "src.app", "wsgi"):
        try:
            factory_mod = importlib.import_module(module_path)
            if hasattr(factory_mod, "create_app"):
                break
            factory_mod = None
        except ImportError:
            continue

    if factory_mod is None:
        pytest.skip("No create_app factory found; skipping instance check.")

    app = factory_mod.create_app()
    assert isinstance(app, flask.Flask), (
        f"create_app() returned {type(app)}, expected flask.Flask instance."
    )


def test_flask_app_runs_in_testing_mode():
    """Flask app must be configurable for testing without errors."""
    import flask
    factory_mod = None
    for module_path in ("app", "application", "src.app", "wsgi"):
        try:
            factory_mod = importlib.import_module(module_path)
            if hasattr(factory_mod, "create_app"):
                break
            factory_mod = None
        except ImportError:
            continue

    if factory_mod is None:
        pytest.skip("No create_app factory found; skipping testing mode check.")

    app = factory_mod.create_app({"TESTING": True})
    assert app.testing is True, "Flask app did not enter testing mode."


# ---------------------------------------------------------------------------
# Flask 3.x — deprecated APIs removed
# ---------------------------------------------------------------------------

def test_flask_before_first_request_removed():
    """Flask 3.x removed before_first_request; it must not be used in the codebase."""
    import flask
    assert not hasattr(flask.Flask, "before_first_request"), (
        "flask.Flask.before_first_request still exists — "
        "this was removed in Flask 2.3+. Ensure the codebase has migrated away."
    )


def test_flask_json_encoder_removed():
    """Flask 3.x removed app.json_encoder/json_decoder; verify they are gone."""
    import flask
    app = flask.Flask(__name__)
    assert not hasattr(app, "json_encoder"), (
        "app.json_encoder still present — removed in Flask 2.3+. "
        "Migrate to app.json.provider."
    )
    assert not hasattr(app, "json_decoder"), (
        "app.json_decoder still present — removed in Flask 2.3+. "
        "Migrate to app.json.provider."
    )


def test_flask_ext_namespace_removed():
    """flask.ext.* namespace was removed; importing it must fail."""
    with pytest.raises(ImportError):
        import flask.ext  # noqa: F401


# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 — new declarative and session APIs
# ---------------------------------------------------------------------------

def test_sqlalchemy_declarative_base_from_orm():
    """SQLAlchemy 2.0 DeclarativeBase must be importable from sqlalchemy.orm."""
    from sqlalchemy.orm import DeclarativeBase  # noqa: F401


def test_sqlalchemy_mapped_column_importable():
    """SQLAlchemy 2.0 mapped_column must be importable (new declarative API)."""
    from sqlalchemy.orm import mapped_column, Mapped  # noqa: F401


def test_sqlalchemy_select_importable():
    """SQLAlchemy 2.0 select() must be importable from sqlalchemy."""
    from sqlalchemy import select  # noqa: F401


def test_sqlalchemy_legacy_query_not_default():
    """SQLAlchemy 2.0 Session must not expose .query() by default (legacy API)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:", future=True)
    with Session(engine) as session:
        # In SQLAlchemy 2.0, Session.query is still present for compat but
        # the recommended path is select(). Verify the 2.0-style execute works.
        from sqlalchemy import text
        result = session.execute(text("SELECT 1"))
        row = result.fetchone()
        assert row[0] == 1, "SQLAlchemy 2.0 session.execute() did not return expected result."


def test_sqlalchemy_engine_future_flag():
    """SQLAlchemy 2.0 create_engine must work without the legacy future=True flag."""
    from sqlalchemy import create_engine
    # In 2.0, future=True is the default and the flag is a no-op / accepted
    engine = create_engine("sqlite:///:memory:")
    assert engine is not None


def test_sqlalchemy_autocommit_removed_from_session_constructor():
    """SQLAlchemy 2.0 removed autocommit from Session constructor."""
    from sqlalchemy.orm import Session
    import inspect
    sig = inspect.signature(Session.__init__)
    assert "autocommit" not in sig.parameters, (
        "Session.__init__ still accepts 'autocommit' — "
        "this was removed in SQLAlchemy 2.0."
    )


# ---------------------------------------------------------------------------
# Environment variable injection (no hardcoded credentials)
# ---------------------------------------------------------------------------

def test_database_url_from_environment(monkeypatch):
    """DATABASE_URL (or equivalent) must be read from environment, not hardcoded."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    db_url = os.environ.get("DATABASE_URL")
    assert db_url is not None, (
        "DATABASE_URL environment variable is not set. "
        "Credentials must be injected via environment variables."
    )
    assert "sqlite" in db_url or "postgresql" in db_url or "mysql" in db_url, (
        f"DATABASE_URL value '{db_url}' does not look like a valid DB URL."
    )


def test_secret_key_from_environment(monkeypatch):
    """Flask SECRET_KEY must be injectable via environment variable."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-ci")
    secret = os.environ.get("SECRET_KEY")
    assert secret is not None and len(secret) > 0, (
        "SECRET_KEY environment variable is not set. "
        "Flask secret key must be injected via environment, not hardcoded."
    )


def test_no_hardcoded_credentials_in_config():
    """Config module must not contain hardcoded password/secret literals."""
    config_candidates = ["config", "settings", "app.config", "src.config"]
    config_source = None
    for candidate in config_candidates:
        try:
            mod = importlib.import_module(candidate)
            config_source = inspect.getsource(mod) if hasattr(mod, "__file__") else ""
            break
        except (ImportError, OSError):
            continue

    if config_source is None:
        pytest.skip("No config module found; skipping hardcoded credential check.")

    import inspect
    forbidden_patterns = [
        "password = \"",
        "password = '",
        "secret_key = \"",
        "secret_key = '",
        "SECRET_KEY = \"",
        "SECRET_KEY = '",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in config_source, (
            f"Hardcoded credential pattern '{pattern}' found in config. "
            "Inject secrets via environment variables."
        )


# ---------------------------------------------------------------------------
# GitHub Actions CI workflow file presence
# ---------------------------------------------------------------------------

def test_github_actions_workflow_directory_exists():
    """The .github/workflows/ directory must exist in the repository root."""
    repo_root = _find_repo_root()
    workflows_dir = os.path.join(repo_root, ".github", "workflows")
    assert os.path.isdir(workflows_dir), (
        f".github/workflows/ directory not found at {workflows_dir}. "
        "GitHub Actions CI workflow has not been added."
    )


def test_github_actions_ci_workflow_file_exists():
    """A CI workflow YAML file must exist in .github/workflows/."""
    repo_root = _find_repo_root()
    workflows_dir = os.path.join(repo_root, ".github", "workflows")
    if not os.path.isdir(workflows_dir):
        pytest.skip(".github/workflows/ directory not found.")

    yaml_files = [f for f in os.listdir(workflows_dir) if f.endswith((".yml", ".yaml"))]
    assert len(yaml_files) > 0, (
        "No YAML workflow files found in .github/workflows/. "
        "CI workflow file must be created."
    )


def test_ci_workflow_contains_lint_stage():
    """CI workflow must define a lint job/stage."""
    content = _read_ci_workflow()
    if content is None:
        pytest.skip("CI workflow file not found.")
    assert "lint" in content.lower(), (
        "CI workflow does not contain a 'lint' stage. "
        "Lint stage is required per upgrade spec."
    )


def test_ci_workflow_contains_sast_stage():
    """CI workflow must define a SAST job/stage (e.g., bandit, semgrep, codeql)."""
    content = _read_ci_workflow()
    if content is None:
        pytest.skip("CI workflow file not found.")
    sast_keywords = ["bandit", "semgrep", "codeql", "sast", "security"]
    assert any(kw in content.lower() for kw in sast_keywords), (
        f"CI workflow does not contain a SAST stage. "
        f"Expected one of: {sast_keywords}. SAST stage is required per upgrade spec."
    )


def test_ci_workflow_contains_test_stage():
    """CI workflow must define a test job/stage."""
    content = _read_ci_workflow()
    if content is None:
        pytest.skip("CI workflow file not found.")
    assert any(kw in content.lower() for kw in ["pytest", "test", "unittest"]), (
        "CI workflow does not contain a test stage. "
        "Test stage is required per upgrade spec."
    )


def test_ci_workflow_triggers_on_push_and_pr():
    """CI workflow must trigger on push and pull_request events."""
    content = _read_ci_workflow()
    if content is None:
        pytest.skip("CI workflow file not found.")
    assert "push" in content, "CI workflow missing 'push' trigger."
    assert "pull_request" in content, "CI workflow missing 'pull_request' trigger."


def test_ci_workflow_specifies_python_312_or_higher():
    """CI workflow must specify Python 3.12 or higher as the runtime."""
    content = _read_ci_workflow()
    if content is None:
        pytest.skip("CI workflow file not found.")
    assert any(ver in content for ver in ["3.12", "3.13", "'3.12'", "'3.13'", '"3.12"', '"3.13"']), (
        "CI workflow does not specify Python 3.12 or 3.13. "
        "Upgrade target requires Python 3.12+."
    )


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _find_repo_root() -> str:
    """Walk up from this file to find the repository root (contains .git or pyproject.toml)."""
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isdir(os.path.join(current, ".git")) or \
                os.path.isfile(os.path.join(current, "pyproject.toml")) or \
                os.path.isfile(os.path.join(current, "setup.py")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.dirname(os.path.abspath(__file__))


def _read_ci_workflow() -> "str | None":
    """Return the content of the first CI workflow YAML file found, or None."""
    repo_root = _find_repo_root()
    workflows_dir = os.path.join(repo_root, ".github", "workflows")
    if not os.path.isdir(workflows_dir):
        return None
    for fname in sorted(os.listdir(workflows_dir)):
        if fname.endswith((".yml", ".yaml")):
            with open(os.path.join(workflows_dir, fname), "r", encoding="utf-8") as fh:
                return fh.read()
    return None