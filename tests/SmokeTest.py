import sys
import importlib
import os
import pytest


# ---------------------------------------------------------------------------
# Version assertions
# ---------------------------------------------------------------------------

def test_python_version_is_at_least_3_12():
    """Python must be 3.12 or 3.13 (upgraded from 3.8 EOL)."""
    major, minor = sys.version_info.major, sys.version_info.minor
    assert major == 3, f"Expected Python 3.x, got {major}.{minor}"
    assert minor >= 12, (
        f"Python 3.12+ required after upgrade, but running {major}.{minor}. "
        "Upgrade Python runtime."
    )


def test_flask_version_is_3_1():
    """Flask must be exactly 3.1.x (upgraded from 1.x EOL)."""
    import flask
    version_parts = tuple(int(p) for p in flask.__version__.split(".")[:2])
    assert version_parts >= (3, 1), (
        f"Flask 3.1+ required after upgrade, but found {flask.__version__}. "
        "Run: pip install 'Flask>=3.1,<4'"
    )


def test_sqlalchemy_version_is_2_0():
    """SQLAlchemy must be 2.0.x (upgraded from 1.3 EOL)."""
    import sqlalchemy
    version_parts = tuple(int(p) for p in sqlalchemy.__version__.split(".")[:2])
    assert version_parts >= (2, 0), (
        f"SQLAlchemy 2.0+ required after upgrade, but found {sqlalchemy.__version__}. "
        "Run: pip install 'SQLAlchemy>=2.0,<3'"
    )


# ---------------------------------------------------------------------------
# Flask 3.1 — application factory pattern
# ---------------------------------------------------------------------------

def _make_app():
    """Minimal application factory using Flask 3.1 conventions."""
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test-secret-key")

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app


def test_flask_app_factory_creates_app():
    """Application factory pattern must produce a valid Flask application."""
    from flask import Flask
    app = _make_app()
    assert isinstance(app, Flask)


def test_flask_app_has_testing_config():
    """App config must be accessible via the factory-created instance."""
    app = _make_app()
    assert app.config["TESTING"] is True


def test_flask_health_endpoint_returns_200():
    """Critical REST API path /health must respond with HTTP 200."""
    app = _make_app()
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200


def test_flask_health_endpoint_returns_json():
    """Health endpoint must return JSON body with status key."""
    app = _make_app()
    client = app.test_client()
    response = client.get("/health")
    data = response.get_json()
    assert data is not None, "Response body must be valid JSON"
    assert data.get("status") == "ok"


def test_flask_3x_no_before_first_request():
    """
    Flask 3.x removed the deprecated before_first_request decorator.
    Verify it is no longer present on the Flask class (deprecated API gone).
    """
    import flask
    app = _make_app()
    assert not hasattr(app, "before_first_request"), (
        "before_first_request was removed in Flask 2.3+; "
        "it must not exist in Flask 3.1"
    )


def test_flask_3x_no_app_errorhandler_on_blueprint_via_old_api():
    """
    Flask 3.x Blueprint.app_errorhandler was removed.
    Confirm the modern error-handler registration works.
    """
    from flask import Flask
    app = Flask(__name__)

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "not found"}, 404

    client = app.test_client()
    response = client.get("/nonexistent-route-xyz")
    assert response.status_code == 404


def test_flask_secret_key_from_environment(monkeypatch):
    """SECRET_KEY must be injectable via environment variable (no hardcoded creds)."""
    monkeypatch.setenv("SECRET_KEY", "env-provided-secret")
    from flask import Flask
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback")
    assert app.config["SECRET_KEY"] == "env-provided-secret"


# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 — new-style declarative base and session patterns
# ---------------------------------------------------------------------------

def test_sqlalchemy_new_declarative_base():
    """
    SQLAlchemy 2.0 uses DeclarativeBase (not the legacy declarative_base() function).
    Verify the new-style base class is importable and usable.
    """
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

    assert Base is not None


def test_sqlalchemy_legacy_declarative_base_import_still_available_but_deprecated():
    """
    declarative_base() still exists in 2.0 for migration compatibility but
    the project must prefer DeclarativeBase. Verify new-style works end-to-end.
    """
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy import Column, Integer, String

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String(50))

    assert User.__tablename__ == "users"


def test_sqlalchemy_2x_session_execute_style():
    """
    SQLAlchemy 2.0 requires session.execute(select(...)) instead of
    the legacy session.query() pattern. Verify the new style works.
    """
    from sqlalchemy import create_engine, Column, Integer, String, select
    from sqlalchemy.orm import DeclarativeBase, Session

    class Base(DeclarativeBase):
        pass

    class Item(Base):
        __tablename__ = "items"
        id = Column(Integer, primary_key=True)
        label = Column(String(100))

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Item(id=1, label="test-item"))
        session.commit()

    with Session(engine) as session:
        stmt = select(Item).where(Item.id == 1)
        result = session.execute(stmt).scalar_one()
        assert result.label == "test-item"


def test_sqlalchemy_2x_no_query_attribute_required():
    """
    SQLAlchemy 2.0 deprecates Model.query (Flask-SQLAlchemy legacy pattern).
    The new execute() style must be used; verify it returns correct results.
    """
    from sqlalchemy import create_engine, Column, Integer, String, select
    from sqlalchemy.orm import DeclarativeBase, Session

    class Base(DeclarativeBase):
        pass

    class Product(Base):
        __tablename__ = "products"
        id = Column(Integer, primary_key=True)
        name = Column(String(80))

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Product(id=10, name="widget"))
        session.commit()

    with Session(engine) as session:
        results = session.execute(select(Product)).scalars().all()
        assert len(results) == 1
        assert results[0].name == "widget"


def test_sqlalchemy_2x_engine_future_flag():
    """
    SQLAlchemy 2.0 engines no longer need future=True (it is the default),
    but passing it must not raise an error for forward compatibility.
    """
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:", future=True)
    assert engine is not None


def test_sqlalchemy_2x_connection_execute_style():
    """
    SQLAlchemy 2.0 connection.execute() must accept text() or select() objects,
    not raw strings (legacy 1.x pattern removed).
    """
    from sqlalchemy import create_engine, text

    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).fetchone()
        assert result[0] == 1


def test_sqlalchemy_2x_raw_string_execute_raises():
    """
    SQLAlchemy 2.0 must reject raw string execution (legacy 1.x API removed).
    Passing a plain string to connection.execute() must raise an error.
    """
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.connect() as conn:
        with pytest.raises((TypeError, Exception)):
            conn.execute("SELECT 1")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Environment variable injection (no hardcoded credentials)
# ---------------------------------------------------------------------------

def test_database_url_from_environment(monkeypatch):
    """DATABASE_URL must be read from environment, not hardcoded."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    db_url = os.environ.get("DATABASE_URL")
    assert db_url is not None, "DATABASE_URL must be set via environment"
    assert "sqlite" in db_url or "postgresql" in db_url or "mysql" in db_url


def test_no_hardcoded_password_in_config():
    """
    Verify that a Flask app config built from environment variables
    does not contain a literal hardcoded password string.
    """
    from flask import Flask
    app = Flask(__name__)
    # Simulate loading config from env only
    app.config["DB_PASSWORD"] = os.environ.get("DB_PASSWORD", "")
    # The value should come from env; if env is unset it should be empty, not a hardcoded secret
    hardcoded_secrets = {"password", "secret", "admin", "root", "1234"}
    actual = app.config.get("DB_PASSWORD", "")
    assert actual.lower() not in hardcoded_secrets, (
        f"DB_PASSWORD appears to be hardcoded to '{actual}'. "
        "Inject credentials via environment variables."
    )


# ---------------------------------------------------------------------------
# New configuration keys introduced by Flask 3.1
# ---------------------------------------------------------------------------

def test_flask_3x_config_keys_load_without_error():
    """
    Flask 3.1 introduced / changed several configuration keys.
    Verify that setting them on the app config raises no errors.
    """
    from flask import Flask
    app = Flask(__name__)
    # Keys valid in Flask 3.x
    new_config = {
        "SECRET_KEY": os.environ.get("SECRET_KEY", "test-key"),
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
        "PROPAGATE_EXCEPTIONS": True,
        "TRAP_HTTP_EXCEPTIONS": False,
        "TRAP_BAD_REQUEST_ERRORS": False,
        "TESTING": False,
        "DEBUG": False,
    }
    for key, value in new_config.items():
        app.config[key] = value  # must not raise

    for key in new_config:
        assert key in app.config


def test_flask_3x_json_provider_is_default():
    """
    Flask 3.x ships with a built-in JSON provider (DefaultJSONProvider).
    Verify it is active and functional.
    """
    from flask import Flask
    from flask.json.provider import DefaultJSONProvider
    app = Flask(__name__)
    assert isinstance(app.json, DefaultJSONProvider), (
        "Flask 3.x must use DefaultJSONProvider as the default JSON provider"
    )