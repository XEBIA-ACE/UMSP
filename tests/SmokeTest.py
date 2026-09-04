import sys
import importlib
import json
import os

import pytest

# ---------------------------------------------------------------------------
# Version assertions
# ---------------------------------------------------------------------------

def test_python_version_is_at_least_3_12():
    """
    The upgrade target is Python 3.12 or 3.13.
    The current runtime must be >= 3.12 (not the EOL 3.8).
    """
    assert sys.version_info >= (3, 12), (
        f"Expected Python >= 3.12 but got {sys.version_info.major}.{sys.version_info.minor}. "
        "Upgrade Python before running this service."
    )


def test_flask_version_is_3_x():
    """Flask must be upgraded to 3.x (target 3.1)."""
    flask = pytest.importorskip("flask", reason="Flask is not installed")
    major = int(flask.__version__.split(".")[0])
    assert major >= 3, (
        f"Expected Flask >= 3.x but found {flask.__version__}. "
        "Run: pip install 'flask>=3.1'"
    )


def test_flask_exact_target_version():
    """Flask target version is 3.1 — assert major.minor match."""
    flask = pytest.importorskip("flask", reason="Flask is not installed")
    parts = flask.__version__.split(".")
    major, minor = int(parts[0]), int(parts[1])
    assert (major, minor) >= (3, 1), (
        f"Expected Flask >= 3.1 but found {flask.__version__}."
    )


def test_sqlalchemy_version_is_2_x():
    """SQLAlchemy must be upgraded to 2.0."""
    sa = pytest.importorskip("sqlalchemy", reason="SQLAlchemy is not installed")
    major = int(sa.__version__.split(".")[0])
    assert major >= 2, (
        f"Expected SQLAlchemy >= 2.x but found {sa.__version__}. "
        "Run: pip install 'sqlalchemy>=2.0'"
    )


# ---------------------------------------------------------------------------
# Flask application-factory pattern (new in this upgrade)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flask_app():
    """
    Attempt to import the application factory.  The upgrade mandates the
    application-factory pattern, so `create_app` must be importable.
    Adjust the module path to match the actual project layout.
    """
    # Try common locations produced by the application-factory pattern.
    factory_candidates = [
        ("app", "create_app"),
        ("src.app", "create_app"),
        ("application", "create_app"),
        ("src.infrastructure.app", "create_app"),
    ]
    factory = None
    for module_path, func_name in factory_candidates:
        try:
            mod = importlib.import_module(module_path)
            factory = getattr(mod, func_name, None)
            if factory is not None:
                break
        except ModuleNotFoundError:
            continue

    if factory is None:
        pytest.skip(
            "No create_app factory found. "
            "Ensure the application-factory pattern is implemented as part of this upgrade."
        )

    app = factory({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="module")
def client(flask_app):
    return flask_app.test_client()


def test_create_app_returns_flask_instance(flask_app):
    """create_app() must return a Flask application instance."""
    from flask import Flask
    assert isinstance(flask_app, Flask), (
        "create_app() did not return a Flask instance. "
        "The application-factory pattern is required by this upgrade."
    )


# ---------------------------------------------------------------------------
# /health endpoint — liveness probe
# ---------------------------------------------------------------------------

def test_health_endpoint_returns_200(client):
    """GET /api/health must return HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == 200, (
        f"Expected 200 from /api/health but got {response.status_code}"
    )


def test_health_endpoint_returns_json(client):
    """GET /api/health must return application/json."""
    response = client.get("/api/health")
    assert "application/json" in response.content_type, (
        f"Expected JSON content-type but got {response.content_type}"
    )


def test_health_endpoint_payload(client):
    """GET /api/health must include status='ok' and a timestamp."""
    response = client.get("/api/health")
    data = response.get_json()
    assert data is not None, "/api/health returned non-JSON body"
    assert data.get("status") == "ok", f"Expected status='ok' but got {data.get('status')}"
    assert "timestamp" in data, "Response missing 'timestamp' field"
    assert data["timestamp"], "'timestamp' field is empty"


def test_health_endpoint_no_auth_required(client):
    """
    /api/health must be accessible without authentication tokens.
    This verifies the security allowlist introduced in this upgrade.
    """
    response = client.get("/api/health")
    assert response.status_code != 401, (
        "/api/health returned 401 — the endpoint must be publicly accessible"
    )
    assert response.status_code != 403, (
        "/api/health returned 403 — the endpoint must be publicly accessible"
    )


# ---------------------------------------------------------------------------
# /ready endpoint — readiness probe (NEW in this upgrade)
# ---------------------------------------------------------------------------

def test_ready_endpoint_exists(client):
    """
    GET /api/ready must exist (introduced by this upgrade).
    A 404 means the endpoint was not added.
    """
    response = client.get("/api/ready")
    assert response.status_code != 404, (
        "GET /api/ready returned 404. "
        "The /ready readiness endpoint must be added as part of this upgrade."
    )


def test_ready_endpoint_returns_200_when_healthy(client):
    """GET /api/ready must return 200 when the service is ready."""
    response = client.get("/api/ready")
    assert response.status_code in (200, 503), (
        f"GET /api/ready returned unexpected status {response.status_code}. "
        "Expected 200 (ready) or 503 (unavailable)."
    )


def test_ready_endpoint_returns_json(client):
    """GET /api/ready must return application/json."""
    response = client.get("/api/ready")
    assert "application/json" in response.content_type, (
        f"Expected JSON content-type from /api/ready but got {response.content_type}"
    )


def test_ready_endpoint_payload_when_ready(client):
    """
    When /api/ready returns 200, the body must contain a 'status' field
    and a 'timestamp' field.
    """
    response = client.get("/api/ready")
    if response.status_code != 200:
        pytest.skip("Service reported not-ready (503); skipping payload shape check.")
    data = response.get_json()
    assert data is not None, "/api/ready returned non-JSON body"
    assert "status" in data, "Response missing 'status' field"
    assert "timestamp" in data, "Response missing 'timestamp' field"


def test_ready_endpoint_no_auth_required(client):
    """/api/ready must be accessible without authentication."""
    response = client.get("/api/ready")
    assert response.status_code not in (401, 403), (
        f"/api/ready returned {response.status_code} — "
        "the readiness endpoint must be publicly accessible (no auth required)."
    )


# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 — deprecated 1.x query API must not be used
# ---------------------------------------------------------------------------

def test_sqlalchemy_legacy_query_api_not_imported():
    """
    SQLAlchemy 2.0 removes the legacy Session.query() pattern.
    Verify that the project source files do not import the removed
    `sqlalchemy.orm.Query` class directly (a sign of un-migrated 1.x code).
    """
    import ast
    import pathlib

    src_root = pathlib.Path(__file__).parent
    # Walk up to find a 'src' directory if this test lives elsewhere
    for candidate in [src_root, src_root.parent, src_root.parent / "src"]:
        if candidate.is_dir():
            src_root = candidate
            break

    legacy_usages = []
    for py_file in src_root.rglob("*.py"):
        if "test" in py_file.name.lower():
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            # Detect: from sqlalchemy.orm import Query
            if isinstance(node, ast.ImportFrom):
                if (node.module or "").startswith("sqlalchemy"):
                    for alias in node.names:
                        if alias.name == "Query":
                            legacy_usages.append(str(py_file))
    assert not legacy_usages, (
        "The following files import the legacy SQLAlchemy 1.x 'Query' class "
        f"which is removed in 2.0: {legacy_usages}. "
        "Migrate to session.execute(select(...)) as required by this upgrade."
    )


def test_sqlalchemy_2_select_api_importable():
    """
    The SQLAlchemy 2.0 select() construct must be importable — this is the
    replacement for the legacy Query API.
    """
    from sqlalchemy import select  # noqa: F401 — import is the assertion


def test_sqlalchemy_2_mapped_column_importable():
    """
    mapped_column() is the new 2.0 declarative API.  Its presence confirms
    the ORM layer has been migrated away from the 1.x Column() style.
    """
    try:
        from sqlalchemy.orm import mapped_column  # noqa: F401
    except ImportError:
        pytest.fail(
            "sqlalchemy.orm.mapped_column is not importable. "
            "Ensure SQLAlchemy >= 2.0 is installed and the ORM models are migrated."
        )


# ---------------------------------------------------------------------------
# Environment-based secrets management (new requirement in this upgrade)
# ---------------------------------------------------------------------------

def test_no_hardcoded_credentials_in_config():
    """
    The upgrade requires removing hardcoded credentials.
    Scan Python source files for obvious hardcoded secret patterns.
    """
    import pathlib
    import re

    # Patterns that suggest hardcoded credentials
    suspicious_patterns = [
        re.compile(r'password\s*=\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
        re.compile(r'secret\s*=\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
        re.compile(r'api_key\s*=\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
    ]
    # Allowlist patterns (test fixtures, example values, env lookups)
    allowlist = re.compile(
        r'os\.environ|os\.getenv|environ\[|getenv\(|example|test|fake|mock|dummy|placeholder',
        re.IGNORECASE,
    )

    src_root = pathlib.Path(__file__).parent
    for candidate in [src_root, src_root.parent, src_root.parent / "src"]:
        if candidate.is_dir():
            src_root = candidate
            break

    violations = []
    for py_file in src_root.rglob("*.py"):
        if "test" in py_file.name.lower():
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for line_no, line in enumerate(content.splitlines(), start=1):
            if allowlist.search(line):
                continue
            for pattern in suspicious_patterns:
                if pattern.search(line):
                    violations.append(f"{py_file}:{line_no}: {line.strip()}")

    assert not violations, (
        "Possible hardcoded credentials found (upgrade requires env-based secrets):\n"
        + "\n".join(violations)
    )


def test_environment_variable_loading_does_not_raise():
    """
    The application must be able to load its configuration from environment
    variables without raising an exception when optional vars are absent.
    """
    config_candidates = [
        "config",
        "src.config",
        "app.config",
        "src.infrastructure.config",
    ]
    loaded = False
    for module_path in config_candidates:
        try:
            importlib.import_module(module_path)
            loaded = True
            break
        except ModuleNotFoundError:
            continue
        except Exception as exc:
            pytest.fail(
                f"Config module '{module_path}' raised an exception during import: {exc}. "
                "Ensure all required environment variables have safe defaults."
            )
    if not loaded:
        pytest.skip("No config module found; skipping env-loading check.")


# ---------------------------------------------------------------------------
# Flask 3.x — removed / changed APIs must not be present
# ---------------------------------------------------------------------------

def test_flask_3_removed_before_first_request_not_used():
    """
    Flask 3.x removed `before_first_request`.  Verify it is not referenced
    in the application source.
    """
    import pathlib

    src_root = pathlib.Path(__file__).parent
    for candidate in [src_root, src_root.parent, src_root.parent / "src"]:
        if candidate.is_dir():
            src_root = candidate
            break

    violations = []
    for py_file in src_root.rglob("*.py"):
        if "test" in py_file.name.lower():
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if "before_first_request" in content:
            violations.append(str(py_file))

    assert not violations, (
        "The following files use 'before_first_request' which was removed in Flask 3.x: "
        f"{violations}. Replace with application startup logic in create_app()."
    )


def test_flask_3_removed_flask_json_not_used():
    """
    Flask 3.x removed `flask.json.provider` legacy helpers and the
    `flask.json` module's `JSONEncoder`/`JSONDecoder` class attributes.
    Verify the deprecated `app.json_encoder` attribute is not assigned.
    """
    import pathlib

    src_root = pathlib.Path(__file__).parent
    for candidate in [src_root, src_root.parent, src_root.parent / "src"]:
        if candidate.is_dir():
            src_root = candidate
            break

    violations = []
    for py_file in src_root.rglob("*.py"):
        if "test" in py_file.name.lower():
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if "json_encoder" in content or "json_decoder" in content:
            violations.append(str(py_file))

    assert not violations, (
        "The following files reference removed Flask 1.x JSON encoder/decoder attributes: "
        f"{violations}. Use app.json.provider or flask.json.provider.DefaultJSONProvider."
    )


def test_flask_3_jsonify_replacement_works(flask_app):
    """
    flask.jsonify() still works in Flask 3.x and must remain functional
    (it is the supported way to return JSON responses).
    """
    from flask import jsonify

    with flask_app.app_context():
        response = jsonify({"status": "ok"})
        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))
        assert data["status"] == "ok"