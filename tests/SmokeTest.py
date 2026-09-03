import sys
import importlib
import pytest


# ---------------------------------------------------------------------------
# Version constants derived from the upgrade context
# ---------------------------------------------------------------------------
TARGET_PYTHON_MAJOR = 3
TARGET_PYTHON_MINOR = 12  # minimum acceptable target (3.12 or 3.13)
TARGET_FLASK_MAJOR = 3
TARGET_FLASK_MINOR = 1
TARGET_SQLALCHEMY_MAJOR = 2
TARGET_SQLALCHEMY_MINOR = 0


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _parse_version(version_string: str) -> tuple:
    """Return a tuple of ints from a PEP-440-style version string."""
    parts = []
    for segment in version_string.split(".")[:3]:
        numeric = ""
        for ch in segment:
            if ch.isdigit():
                numeric += ch
            else:
                break
        if numeric:
            parts.append(int(numeric))
    return tuple(parts)


# ---------------------------------------------------------------------------
# Python runtime version
# ---------------------------------------------------------------------------

class TestPythonVersion:
    """Verify the active Python interpreter meets the upgrade target."""

    def test_python_major_version(self):
        assert sys.version_info.major == TARGET_PYTHON_MAJOR, (
            f"Expected Python {TARGET_PYTHON_MAJOR}.x, "
            f"got {sys.version_info.major}.{sys.version_info.minor}"
        )

    def test_python_minimum_minor_version(self):
        assert sys.version_info.minor >= TARGET_PYTHON_MINOR, (
            f"Expected Python >= {TARGET_PYTHON_MAJOR}.{TARGET_PYTHON_MINOR}, "
            f"got {sys.version_info.major}.{sys.version_info.minor}"
        )

    def test_python_not_eol_38(self):
        """Confirm we are no longer running the EOL 3.8 interpreter."""
        assert not (sys.version_info.major == 3 and sys.version_info.minor == 8), (
            "Python 3.8 is EOL and must not be used after the upgrade."
        )


# ---------------------------------------------------------------------------
# Flask version and API surface
# ---------------------------------------------------------------------------

class TestFlaskVersion:
    """Verify Flask 3.x is installed and the new API surface is available."""

    @pytest.fixture(scope="class")
    def flask_module(self):
        flask = pytest.importorskip("flask", reason="Flask is not installed")
        return flask

    def test_flask_major_version(self, flask_module):
        version_tuple = _parse_version(flask_module.__version__)
        assert version_tuple[0] >= TARGET_FLASK_MAJOR, (
            f"Expected Flask >= {TARGET_FLASK_MAJOR}.0, "
            f"got {flask_module.__version__}"
        )

    def test_flask_minor_version(self, flask_module):
        version_tuple = _parse_version(flask_module.__version__)
        if version_tuple[0] == TARGET_FLASK_MAJOR:
            assert version_tuple[1] >= TARGET_FLASK_MINOR, (
                f"Expected Flask >= {TARGET_FLASK_MAJOR}.{TARGET_FLASK_MINOR}, "
                f"got {flask_module.__version__}"
            )

    def test_flask_not_version_1x(self, flask_module):
        version_tuple = _parse_version(flask_module.__version__)
        assert version_tuple[0] != 1, (
            f"Flask 1.x is EOL and must not be used after the upgrade. "
            f"Found {flask_module.__version__}"
        )

    def test_flask_application_factory_pattern_supported(self, flask_module):
        """Flask 3.x supports the application factory pattern via create_app convention."""
        app = flask_module.Flask(__name__)
        assert app is not None
        assert hasattr(app, "config")

    def test_flask_app_context_works(self, flask_module):
        app = flask_module.Flask(__name__)
        with app.app_context():
            assert flask_module.current_app._get_current_object() is app

    def test_flask_blueprints_available(self, flask_module):
        bp = flask_module.Blueprint("test_bp", __name__)
        assert bp is not None

    def test_flask_json_provider_api_available(self, flask_module):
        """Flask 3.x replaced flask.json helpers with a JSON provider API."""
        app = flask_module.Flask(__name__)
        # Flask 3.x exposes json_provider_class on the app
        assert hasattr(app, "json_provider_class") or hasattr(app, "json"), (
            "Flask 3.x JSON provider API not found on the application object."
        )

    def test_flask_deprecated_before_request_funcs_replaced(self, flask_module):
        """Verify before_request decorator (replacement for deprecated patterns) works."""
        app = flask_module.Flask(__name__)

        @app.before_request
        def _setup():
            pass

        assert "_setup" in [f.__name__ for f in app.before_request_funcs.get(None, [])]

    def test_flask_no_deprecated_send_file_max_age_default(self, flask_module):
        """
        In Flask 2+/3+, SEND_FILE_MAX_AGE_DEFAULT was removed as a top-level
        config key in favour of the default value on send_file().
        Verify the app starts without that legacy key causing errors.
        """
        app = flask_module.Flask(__name__)
        # Setting the old key should not raise but also should not be required
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = None
        with app.app_context():
            pass  # no exception expected

    def test_flask_rest_route_registration(self, flask_module):
        """Critical REST API path: route registration and test client work."""
        app = flask_module.Flask(__name__)

        @app.route("/health", methods=["GET"])
        def health():
            return flask_module.jsonify({"status": "ok"})

        client = app.test_client()
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data == {"status": "ok"}

    def test_flask_error_handler_registration(self, flask_module):
        app = flask_module.Flask(__name__)

        @app.errorhandler(404)
        def not_found(e):
            return flask_module.jsonify({"error": "not found"}), 404

        client = app.test_client()
        response = client.get("/nonexistent-route-xyz")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# SQLAlchemy version and new 2.0 API
# ---------------------------------------------------------------------------

class TestSQLAlchemyVersion:
    """Verify SQLAlchemy 2.x is installed and the 2.0 query API is available."""

    @pytest.fixture(scope="class")
    def sa(self):
        sqlalchemy = pytest.importorskip(
            "sqlalchemy", reason="SQLAlchemy is not installed"
        )
        return sqlalchemy

    def test_sqlalchemy_major_version(self, sa):
        version_tuple = _parse_version(sa.__version__)
        assert version_tuple[0] >= TARGET_SQLALCHEMY_MAJOR, (
            f"Expected SQLAlchemy >= {TARGET_SQLALCHEMY_MAJOR}.0, "
            f"got {sa.__version__}"
        )

    def test_sqlalchemy_not_version_1x(self, sa):
        version_tuple = _parse_version(sa.__version__)
        assert version_tuple[0] != 1, (
            f"SQLAlchemy 1.x is EOL and must not be used after the upgrade. "
            f"Found {sa.__version__}"
        )

    def test_sqlalchemy_2_0_select_api_available(self, sa):
        """SQLAlchemy 2.0 uses select() as the primary query construct."""
        assert hasattr(sa, "select"), "sa.select not found — 2.0 API unavailable"
        stmt = sa.select(sa.text("1"))
        assert stmt is not None

    def test_sqlalchemy_2_0_session_execute_api(self, sa):
        """
        SQLAlchemy 2.0 removed Query.all() in favour of session.execute(select(...)).
        Verify the new pattern works end-to-end with an in-memory database.
        """
        from sqlalchemy import create_engine, Column, Integer, String, select
        from sqlalchemy.orm import DeclarativeBase, Session

        engine = create_engine("sqlite:///:memory:", future=True)

        class Base(DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "user"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        Base.metadata.create_all(engine)

        with Session(engine) as session:
            session.add(User(id=1, name="alice"))
            session.commit()

        with Session(engine) as session:
            result = session.execute(select(User).where(User.name == "alice"))
            users = result.scalars().all()

        assert len(users) == 1
        assert users[0].name == "alice"

    def test_sqlalchemy_declarative_base_new_style(self, sa):
        """SQLAlchemy 2.0 introduces DeclarativeBase as the preferred base class."""
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        assert Base is not None

    def test_sqlalchemy_legacy_query_property_not_required(self, sa):
        """
        In SQLAlchemy 2.0 the legacy Query interface is optional/removed.
        Verify that Session does NOT require the legacy query property for
        basic operations (i.e., the new API is self-sufficient).
        """
        from sqlalchemy import create_engine, Column, Integer, String, select
        from sqlalchemy.orm import DeclarativeBase, Session

        engine = create_engine("sqlite:///:memory:", future=True)

        class Base(DeclarativeBase):
            pass

        class Item(Base):
            __tablename__ = "item"
            id = Column(Integer, primary_key=True)
            label = Column(String(50))

        Base.metadata.create_all(engine)

        with Session(engine) as session:
            session.add(Item(id=1, label="widget"))
            session.commit()

            # 2.0-style query — must not raise
            stmt = select(Item).where(Item.label == "widget")
            result = session.execute(stmt).scalars().all()
            assert len(result) == 1

    def test_sqlalchemy_mapped_column_available(self, sa):
        """mapped_column() is a new 2.0 construct for typed ORM mappings."""
        try:
            from sqlalchemy.orm import mapped_column, Mapped
        except ImportError:
            pytest.fail(
                "sqlalchemy.orm.mapped_column / Mapped not available — "
                "SQLAlchemy 2.0 API is missing."
            )

    def test_sqlalchemy_engine_future_flag_default(self, sa):
        """
        In SQLAlchemy 2.0 the future=True flag is the default behaviour.
        Creating an engine without future=True must still work.
        """
        from sqlalchemy import create_engine
        engine = create_engine("sqlite:///:memory:")
        assert engine is not None


# ---------------------------------------------------------------------------
# Environment-based secrets management (no hardcoded credentials)
# ---------------------------------------------------------------------------

class TestEnvironmentSecretsManagement:
    """
    Verify that the application configuration pattern supports environment-based
    secrets (introduced as part of the modernization).
    """

    def test_os_environ_accessible(self):
        import os
        assert os.environ is not None

    def test_flask_config_from_env_var(self):
        flask = pytest.importorskip("flask")
        import os

        os.environ.setdefault("SECRET_KEY", "test-secret-key-for-validation")
        app = flask.Flask(__name__)
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

        assert app.config["SECRET_KEY"] == os.environ["SECRET_KEY"]
        assert app.config["SECRET_KEY"] != ""

    def test_database_url_from_environment(self):
        """DATABASE_URL should be read from the environment, not hardcoded."""
        import os
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        db_url = os.environ.get("DATABASE_URL")
        assert db_url is not None
        assert len(db_url) > 0


# ---------------------------------------------------------------------------
# New configuration keys introduced by Flask 3.x
# ---------------------------------------------------------------------------

class TestFlask3ConfigKeys:
    """Verify new/changed configuration keys in Flask 3.x load without errors."""

    @pytest.fixture(scope="class")
    def app(self):
        flask = pytest.importorskip("flask")
        application = flask.Flask(__name__)
        return application

    def test_max_content_length_config(self, app):
        app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
        assert app.config["MAX_CONTENT_LENGTH"] == 16 * 1024 * 1024

    def test_json_sort_keys_config(self, app):
        """JSON_SORT_KEYS is still supported in Flask 3.x."""
        app.config["JSON_SORT_KEYS"] = False
        assert app.config["JSON_SORT_KEYS"] is False

    def test_propagate_exceptions_config(self, app):
        app.config["PROPAGATE_EXCEPTIONS"] = True
        assert app.config["PROPAGATE_EXCEPTIONS"] is True

    def test_testing_config_key(self, app):
        app.config["TESTING"] = True
        assert app.config["TESTING"] is True

    def test_secret_key_config(self, app):
        app.config["SECRET_KEY"] = "upgrade-validation-secret"
        assert app.config["SECRET_KEY"] == "upgrade-validation-secret"


# ---------------------------------------------------------------------------
# Monolith / REST API integration smoke test
# ---------------------------------------------------------------------------

class TestRESTAPIIntegration:
    """End-to-end validation of the REST API architecture pattern post-upgrade."""

    @pytest.fixture(scope="class")
    def app(self):
        flask = pytest.importorskip("flask")

        application = flask.Flask(__name__)
        application.config["TESTING"] = True
        application.config["SECRET_KEY"] = "integration-test-secret"

        @application.route("/api/v1/status", methods=["GET"])
        def status():
            return flask.jsonify({"version": flask.__version__, "status": "running"})

        @application.route("/api/v1/items", methods=["GET"])
        def list_items():
            return flask.jsonify({"items": []})

        @application.route("/api/v1/items", methods=["POST"])
        def create_item():
            payload = flask.request.get_json(silent=True) or {}
            return flask.jsonify({"created": payload}), 201

        return application

    @pytest.fixture(scope="class")
    def client(self, app):
        return app.test_client()

    def test_status_endpoint_returns_200(self, client):
        response = client.get("/api/v1/status")
        assert response.status_code == 200

    def test_status_endpoint_returns_flask_version(self, client):
        import flask
        response = client.get("/api/v1/status")
        data = response.get_json()
        assert "version" in data
        version_tuple = _parse_version(data["version"])
        assert version_tuple[0] >= TARGET_FLASK_MAJOR

    def test_list_items_endpoint(self, client):
        response = client.get("/api/v1/items")
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data

    def test_create_item_endpoint(self, client):
        response = client.post(
            "/api/v1/items",
            json={"name": "test-item"},
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["created"]["name"] == "test-item"

    def test_unsupported_method_returns_405(self, client):
        response = client.delete("/api/v1/status")
        assert response.status_code == 405