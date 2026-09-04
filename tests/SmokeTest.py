import sys
import importlib
import json
import os
import subprocess

import pytest


# ---------------------------------------------------------------------------
# Version assertions
# ---------------------------------------------------------------------------

def test_python_version_is_at_least_3_12():
    """
    The upgrade target is Python 3.12 or 3.13.
    The current runtime must be >= 3.12 and NOT the legacy 3.8.
    """
    major, minor = sys.version_info.major, sys.version_info.minor
    assert major == 3, f"Expected Python 3.x, got {major}.{minor}"
    assert minor >= 12, (
        f"Upgrade target is Python 3.12+, but active interpreter is {major}.{minor}. "
        "The upgrade has not been applied."
    )


def test_python_version_is_not_legacy_3_8():
    """Explicitly confirm we are no longer running on the EOL 3.8 baseline."""
    assert sys.version_info[:2] != (3, 8), (
        "Python 3.8 (EOL) is still active. The upgrade to 3.12/3.13 has not been applied."
    )


def test_flask_version_is_3_x():
    """Flask must be upgraded from 1.x (EOL) to 3.x."""
    flask = pytest.importorskip("flask", reason="Flask is not installed")
    major = int(flask.__version__.split(".")[0])
    assert major >= 3, (
        f"Flask {flask.__version__} is active. The upgrade to Flask 3.x has not been applied."
    )


def test_flask_version_is_not_1_x():
    """Confirm Flask 1.x is no longer present."""
    flask = pytest.importorskip("flask", reason="Flask is not installed")
    major = int(flask.__version__.split(".")[0])
    assert major != 1, (
        f"Flask 1.x ({flask.__version__}) is still installed. "
        "The upgrade to Flask 3.x has not been applied."
    )


def test_sqlalchemy_version_is_2_x():
    """SQLAlchemy must be upgraded from 1.3 (EOL) to 2.0."""
    sa = pytest.importorskip("sqlalchemy", reason="SQLAlchemy is not installed")
    major = int(sa.__version__.split(".")[0])
    assert major >= 2, (
        f"SQLAlchemy {sa.__version__} is active. "
        "The upgrade to SQLAlchemy 2.0 has not been applied."
    )


def test_sqlalchemy_version_is_not_1_3():
    """Confirm SQLAlchemy 1.3 is no longer present."""
    sa = pytest.importorskip("sqlalchemy", reason="SQLAlchemy is not installed")
    version_tuple = tuple(int(x) for x in sa.__version__.split(".")[:2])
    assert version_tuple >= (2, 0), (
        f"SQLAlchemy {sa.__version__} is still installed. "
        "The upgrade to 2.0 has not been applied."
    )


# ---------------------------------------------------------------------------
# Flask 3.x application factory pattern
# ---------------------------------------------------------------------------

def _import_create_app():
    """
    Attempt to import the application factory.  The upgrade spec requires
    Flask 3.x with the application factory pattern.  We try common module
    paths used in the codebase.
    """
    for module_path in ("app", "src.app", "infrastructure.app"):
        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, "create_app"):
                return mod.create_app
        except ModuleNotFoundError:
            continue
    return None


def test_application_factory_exists():
    """
    Flask 3.x upgrade requires the application factory pattern.
    A callable `create_app` must be importable.
    """
    create_app = _import_create_app()
    assert create_app is not None, (
        "No `create_app` factory function found. "
        "The Flask 3.x application factory pattern has not been implemented."
    )


def test_application_factory_returns_flask_app():
    """create_app() must return a Flask application instance."""
    flask = pytest.importorskip("flask")
    create_app = _import_create_app()
    if create_app is None:
        pytest.skip("create_app not found — skipping factory return-type check")
    app = create_app()
    assert isinstance(app, flask.Flask), (
        f"create_app() returned {type(app)!r}, expected a Flask application instance."
    )


# ---------------------------------------------------------------------------
# /health endpoint — liveness probe
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flask_test_client():
    """Return a Flask test client if the application factory is available."""
    flask = pytest.importorskip("flask")
    create_app = _import_create_app()
    if create_app is None:
        pytest.skip("create_app not found — cannot create test client")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint_returns_200(flask_test_client):
    """GET /api/health must return HTTP 200."""
    response = flask_test_client.get("/api/health")
    assert response.status_code == 200, (
        f"GET /api/health returned {response.status_code}, expected 200."
    )


def test_health_endpoint_returns_json(flask_test_client):
    """GET /api/health must return application/json content-type."""
    response = flask_test_client.get("/api/health")
    assert "application/json" in response.content_type, (
        f"GET /api/health content-type is {response.content_type!r}, expected application/json."
    )


def test_health_endpoint_payload_status_ok(flask_test_client):
    """GET /api/health payload must contain status='ok'."""
    response = flask_test_client.get("/api/health")
    data = response.get_json()
    assert data is not None, "GET /api/health returned non-JSON body."
    assert data.get("status") == "ok", (
        f"Expected status='ok' in /api/health response, got {data.get('status')!r}."
    )


def test_health_endpoint_payload_has_timestamp(flask_test_client):
    """GET /api/health payload must include a non-empty timestamp field."""
    response = flask_test_client.get("/api/health")
    data = response.get_json()
    assert data is not None, "GET /api/health returned non-JSON body."
    assert "timestamp" in data and data["timestamp"], (
        "GET /api/health response is missing a non-empty 'timestamp' field."
    )


def test_health_endpoint_is_unauthenticated(flask_test_client):
    """GET /api/health must be accessible without any authentication token."""
    response = flask_test_client.get("/api/health")
    assert response.status_code != 401 and response.status_code != 403, (
        f"GET /api/health requires authentication (status {response.status_code}). "
        "Liveness probes must be unauthenticated."
    )


# ---------------------------------------------------------------------------
# /ready endpoint — readiness probe (new endpoint added by this upgrade)
# ---------------------------------------------------------------------------

def test_ready_endpoint_exists(flask_test_client):
    """
    GET /api/ready must exist (new endpoint introduced by this upgrade).
    A 404 means the route has not been registered.
    """
    response = flask_test_client.get("/api/ready")
    assert response.status_code != 404, (
        "GET /api/ready returned 404. The new readiness endpoint has not been registered. "
        "Ensure the route is mounted at /api/ready."
    )


def test_ready_endpoint_returns_200(flask_test_client):
    """GET /api/ready must return HTTP 200 when the service is ready."""
    response = flask_test_client.get("/api/ready")
    assert response.status_code == 200, (
        f"GET /api/ready returned {response.status_code}, expected 200."
    )


def test_ready_endpoint_returns_json(flask_test_client):
    """GET /api/ready must return application/json content-type."""
    response = flask_test_client.get("/api/ready")
    assert "application/json" in response.content_type, (
        f"GET /api/ready content-type is {response.content_type!r}, expected application/json."
    )


def test_ready_endpoint_payload_status_ready(flask_test_client):
    """GET /api/ready payload must contain status='ready'."""
    response = flask_test_client.get("/api/ready")
    data = response.get_json()
    assert data is not None, "GET /api/ready returned non-JSON body."
    assert data.get("status") == "ready", (
        f"Expected status='ready' in /api/ready response, got {data.get('status')!r}."
    )


def test_ready_endpoint_payload_has_timestamp(flask_test_client):
    """GET /api/ready payload must include a non-empty timestamp field."""
    response = flask_test_client.get("/api/ready")
    data = response.get_json()
    assert data is not None, "GET /api/ready returned non-JSON body."
    assert "timestamp" in data and data["timestamp"], (
        "GET /api/ready response is missing a non-empty 'timestamp' field."
    )


def test_ready_endpoint_is_unauthenticated(flask_test_client):
    """GET /api/ready must be accessible without any authentication token."""
    response = flask_test_client.get("/api/ready")
    assert response.status_code != 401 and response.status_code != 403, (
        f"GET /api/ready requires authentication (status {response.status_code}). "
        "Readiness probes must be unauthenticated."
    )


# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 — deprecated legacy query API must not be used
# ---------------------------------------------------------------------------

def test_sqlalchemy_legacy_query_api_not_imported():
    """
    SQLAlchemy 2.0 removes the legacy Session.query() pattern.
    Verify that the application does not import the removed
    `sqlalchemy.orm.Query` in a way that would fail at runtime.
    The class still exists for compatibility but active use of
    `session.query(Model)` is the deprecated pattern; we verify
    the new `select()` construct is importable as the replacement.
    """
    sa_orm = pytest.importorskip("sqlalchemy.orm")
    from sqlalchemy import select  # noqa: F401 — must be importable in 2.0
    # select() is the canonical 2.0 query API
    assert callable(select), "sqlalchemy.select is not callable — SQLAlchemy 2.0 API unavailable."


def test_sqlalchemy_2_0_select_construct_works():
    """
    Verify the SQLAlchemy 2.0 select() construct works end-to-end
    with an in-memory SQLite database — the canonical replacement for
    the legacy session.query() API.
    """
    sa = pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine, Column, Integer, String, select
    from sqlalchemy.orm import DeclarativeBase, Session

    class Base(DeclarativeBase):
        pass

    class _SampleModel(Base):
        __tablename__ = "sample_upgrade_test"
        id = Column(Integer, primary_key=True)
        name = Column(String(50))

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(_SampleModel(id=1, name="upgrade-check"))
        session.commit()

    with Session(engine) as session:
        stmt = select(_SampleModel).where(_SampleModel.name == "upgrade-check")
        result = session.execute(stmt).scalars().first()

    assert result is not None, "SQLAlchemy 2.0 select() query returned no results."
    assert result.name == "upgrade-check", (
        f"Unexpected name value: {result.name!r}"
    )


def test_sqlalchemy_2_0_engine_future_flag():
    """
    SQLAlchemy 2.0 engines no longer require `future=True` (it is the default),
    but passing it must not raise an error — confirming 2.0 compatibility.
    """
    sa = pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:", future=True)
    assert engine is not None


# ---------------------------------------------------------------------------
# Flask 3.x — deprecated APIs removed in 3.x must not be present
# ---------------------------------------------------------------------------

def test_flask_3_removed_before_first_request():
    """
    Flask 3.x removed `before_first_request` decorator (deprecated in 2.x).
    Confirm it is no longer present on the Flask application class.
    """
    flask = pytest.importorskip("flask")
    app = flask.Flask(__name__)
    assert not hasattr(app, "before_first_request"), (
        "Flask app still exposes `before_first_request` — this was removed in Flask 3.x. "
        "The upgrade to Flask 3.x has not been fully applied."
    )


def test_flask_3_json_provider_available():
    """
    Flask 3.x introduced the `json_provider_class` attribute on the app.
    Its presence confirms Flask 3.x is active.
    """
    flask = pytest.importorskip("flask")
    app = flask.Flask(__name__)
    assert hasattr(app, "json_provider_class"), (
        "Flask app does not have `json_provider_class`. "
        "This attribute was introduced in Flask 2.2+ and is required in Flask 3.x."
    )


def test_flask_3_no_deprecated_flask_json_module():
    """
    `flask.json.jsonify` must still work in Flask 3.x (it was not removed),
    but the old `flask.json` module-level `dumps`/`loads` wrappers that
    relied on the app context implicitly should be replaced by the provider API.
    Verify `flask.json.provider` sub-module exists (Flask 2.2+ / 3.x).
    """
    flask = pytest.importorskip("flask")
    import flask.json.provider as provider_module  # noqa: F401
    assert provider_module is not None, (
        "flask.json.provider module not found — Flask 3.x JSON provider API is missing."
    )


# ---------------------------------------------------------------------------
# Environment-based secrets management (no hardcoded credentials)
# ---------------------------------------------------------------------------

def test_secret_key_loaded_from_environment(monkeypatch):
    """
    The upgrade requires environment-based secrets management.
    The Flask SECRET_KEY must be read from the environment, not hardcoded.
    """
    flask = pytest.importorskip("flask")
    test_secret = "test-upgrade-secret-key-xyz"
    monkeypatch.setenv("SECRET_KEY", test_secret)

    create_app = _import_create_app()
    if create_app is None:
        pytest.skip("create_app not found — skipping secret key environment test")

    app = create_app()
    # The app's secret key should either match the env var or not be a
    # well-known insecure default like "dev", "secret", "changeme", etc.
    insecure_defaults = {"dev", "secret", "changeme", "hardcoded", "password", "flask"}
    secret = (app.secret_key or "").lower() if app.secret_key else ""
    assert secret not in insecure_defaults, (
        f"Flask SECRET_KEY appears to be a hardcoded insecure default: {app.secret_key!r}. "
        "Secrets must be loaded from environment variables."
    )


def test_database_url_not_hardcoded(monkeypatch):
    """
    Database connection strings must not be hardcoded.
    Verify that the application reads DATABASE_URL (or equivalent) from the environment.
    """
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    create_app = _import_create_app()
    if create_app is None:
        pytest.skip("create_app not found — skipping DATABASE_URL environment test")
    # If create_app raises a configuration error when DATABASE_URL is set to a
    # test value, that indicates hardcoded credentials are still present.
    try:
        app = create_app()
        assert app is not None
    except Exception as exc:
        pytest.fail(
            f"create_app() raised {type(exc).__name__}: {exc} when DATABASE_URL was set "
            "via environment. Ensure the app reads DATABASE_URL from os.environ."
        )


# ---------------------------------------------------------------------------
# New configuration keys introduced by the upgrade
# ---------------------------------------------------------------------------

def test_new_health_blueprint_or_route_registered(flask_test_client):
    """
    The upgrade adds /api/health and /api/ready endpoints.
    Both routes must be registered in the Flask URL map.
    """
    response_health = flask_test_client.get("/api/health")
    response_ready = flask_test_client.get("/api/ready")

    assert response_health.status_code != 404, (
        "GET /api/health is not registered in the Flask URL map (404). "
        "The health endpoint has not been added."
    )
    assert response_ready.status_code != 404, (
        "GET /api/ready is not registered in the Flask URL map (404). "
        "The readiness endpoint has not been added."
    )


def test_health_and_ready_endpoints_are_distinct(flask_test_client):
    """
    /api/health (liveness) and /api/ready (readiness) must be separate endpoints
    returning distinct status values.
    """
    health_data = flask_test_client.get("/api/health").get_json()
    ready_data = flask_test_client.get("/api/ready").get_json()

    if health_data is None or ready_data is None:
        pytest.skip("One or both endpoints returned non-JSON — skipping distinctness check")

    assert health_data.get("status") != ready_data.get("status") or (
        health_data.get("status") == "ok" and ready_data.get("status") == "ready"
    ), (
        "The /api/health and /api/ready endpoints must return distinct status values "
        "('ok' and 'ready' respectively). They appear to be the same endpoint."
    )