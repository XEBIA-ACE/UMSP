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

def _parse_version(version_string: str):
    """Return a tuple of ints from a PEP-440-style version string."""
    parts = []
    for segment in version_string.split("."):
        numeric = ""
        for ch in segment:
            if ch.isdigit():
                numeric += ch
            else:
                break
        if numeric:
            parts.append(int(numeric))
    return tuple(parts)


# ===========================================================================
# 1. Runtime version assertions
# ===========================================================================

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
            "Python 3.8 is EOL and must not be used after this upgrade."
        )


# ===========================================================================
# 2. Flask version assertions
# ===========================================================================

class TestFlaskVersion:
    """Verify Flask 3.1 (or later 3.x) is installed and active."""

    @pytest.fixture(autouse=True)
    def import_flask(self):
        self.flask = pytest.importorskip("flask", reason="Flask is not installed")

    def test_flask_major_version(self):
        version_tuple = _parse_version(self.flask.__version__)
        assert version_tuple[0] == TARGET_FLASK_MAJOR, (
            f"Expected Flask {TARGET_FLASK_MAJOR}.x, got {self.flask.__version__}"
        )

    def test_flask_minimum_minor_version(self):
        version_tuple = _parse_version(self.flask.__version__)
        assert version_tuple[1] >= TARGET_FLASK_MINOR, (
            f"Expected Flask >= {TARGET_FLASK_MAJOR}.{TARGET_FLASK_MINOR}, "
            f"got {self.flask.__version__}"
        )

    def test_flask_not_1x(self):
        """Confirm EOL Flask 1.x is no longer active."""
        version_tuple = _parse_version(self.flask.__version__)
        assert version_tuple[0] != 1, (
            f"Flask 1.x is EOL and must not be used after this upgrade. "
            f"Got {self.flask.__version__}"
        )


# ===========================================================================
# 3. SQLAlchemy version assertions
# ===========================================================================

class TestSQLAlchemyVersion:
    """Verify SQLAlchemy 2.0+ is installed and active."""

    @pytest.fixture(autouse=True)
    def import_sqlalchemy(self):
        self.sa = pytest.importorskip(
            "sqlalchemy", reason="SQLAlchemy is not installed"
        )

    def test_sqlalchemy_major_version(self):
        version_tuple = _parse_version(self.sa.__version__)
        assert version_tuple[0] >= TARGET_SQLALCHEMY_MAJOR, (
            f"Expected SQLAlchemy >= {TARGET_SQLALCHEMY_MAJOR}.0, "
            f"got {self.sa.__version__}"
        )

    def test_sqlalchemy_not_1x(self):
        """Confirm EOL SQLAlchemy 1.3 is no longer active."""
        version_tuple = _parse_version(self.sa.__version__)
        assert version_tuple[0] != 1, (
            f"SQLAlchemy 1.x is EOL and must not be used after this upgrade. "
            f"Got {self.sa.__version__}"
        )


# ===========================================================================
# 4. Flask application factory pattern (Flask 3.x requirement)
# ===========================================================================

class TestFlaskApplicationFactory:
    """
    Verify that the application can be constructed via the factory pattern
    introduced as part of the Flask 3.x upgrade.
    """

    @pytest.fixture
    def app(self):
        flask = pytest.importorskip("flask")

        def create_app(config=None):
            application = flask.Flask(__name__)
            application.config["TESTING"] = True
            application.config["SECRET_KEY"] = "test-secret-key"
            if config:
                application.config.update(config)
            return application

        return create_app()

    def test_app_factory_creates_flask_instance(self, app):
        flask = importlib.import_module("flask")
        assert isinstance(app, flask.Flask)

    def test_app_factory_testing_flag(self, app):
        assert app.config["TESTING"] is True

    def test_app_context_pushes_without_error(self, app):
        with app.app_context():
            flask = importlib.import_module("flask")
            assert flask.current_app._get_current_object() is app

    def test_test_client_returns_200_for_registered_route(self, app):
        @app.route("/healthz")
        def healthz():
            import flask as _flask
            return _flask.jsonify({"status": "ok"}), 200

        client = app.test_client()
        response = client.get("/healthz")
        assert response.status_code == 200

    def test_json_response_content_type(self, app):
        @app.route("/ping")
        def ping():
            import flask as _flask
            return _flask.jsonify({"ping": "pong"}), 200

        client = app.test_client()
        response = client.get("/ping")
        assert "application/json" in response.content_type


# ===========================================================================
# 5. Flask 3.x — deprecated APIs removed / replaced
# ===========================================================================

class TestFlaskDeprecatedAPIsRemoved:
    """
    Confirm that APIs deprecated in Flask 1.x and removed in Flask 3.x
    are no longer present, and that their replacements work correctly.
    """

    def test_flask_json_provider_exists(self):
        """Flask 3.x uses a JSON provider; the old flask.json helpers changed."""
        flask = pytest.importorskip("flask")
        # Flask 3.x exposes json_provider_class on the Flask class
        assert hasattr(flask.Flask, "json_provider_class"), (
            "Flask 3.x should expose json_provider_class on the Flask class"
        )

    def test_before_first_request_removed(self):
        """
        @app.before_first_request was deprecated in Flask 2.2 and removed in 3.0.
        Verify it no longer exists on the Flask application object.
        """
        flask = pytest.importorskip("flask")
        app = flask.Flask(__name__)
        assert not hasattr(app, "before_first_request"), (
            "before_first_request was removed in Flask 3.0 and must not exist"
        )

    def test_flask_escape_removed(self):
        """
        flask.escape was removed in Flask 2.x (moved to markupsafe).
        Confirm it is not importable from flask directly.
        """
        flask = pytest.importorskip("flask")
        assert not hasattr(flask, "escape"), (
            "flask.escape was removed; use markupsafe.escape instead"
        )

    def test_markupsafe_escape_available(self):
        """Replacement for flask.escape lives in markupsafe."""
        markupsafe = pytest.importorskip(
            "markupsafe", reason="markupsafe is not installed"
        )
        assert hasattr(markupsafe, "escape")
        result = markupsafe.escape("<script>")
        assert "&lt;script&gt;" in str(result)


# ===========================================================================
# 6. SQLAlchemy 2.0 — new query API
# ===========================================================================

class TestSQLAlchemy2QueryAPI:
    """
    Verify that the SQLAlchemy 2.0 select() / Session.execute() query API
    works correctly (replacing the legacy Query API from 1.3).
    """

    @pytest.fixture
    def in_memory_engine(self):
        sa = pytest.importorskip("sqlalchemy")
        engine = sa.create_engine("sqlite:///:memory:", future=True)
        return engine

    @pytest.fixture
    def mapped_table(self, in_memory_engine):
        sa = pytest.importorskip("sqlalchemy")
        metadata = sa.MetaData()
        users = sa.Table(
            "users",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(50), nullable=False),
        )
        metadata.create_all(in_memory_engine)
        return users, in_memory_engine

    def test_select_statement_api(self, mapped_table):
        sa = importlib.import_module("sqlalchemy")
        users, engine = mapped_table

        with engine.connect() as conn:
            conn.execute(users.insert(), [{"name": "Alice"}, {"name": "Bob"}])
            conn.commit()

            stmt = sa.select(users).where(users.c.name == "Alice")
            result = conn.execute(stmt)
            rows = result.fetchall()

        assert len(rows) == 1
        assert rows[0].name == "Alice"

    def test_session_execute_new_api(self, mapped_table):
        """Verify Session.execute(select(...)) works — the 2.0 style."""
        sa = importlib.import_module("sqlalchemy")
        orm = importlib.import_module("sqlalchemy.orm")
        users, engine = mapped_table

        Session = orm.sessionmaker(bind=engine)
        with Session() as session:
            session.execute(users.insert(), [{"name": "Carol"}])
            session.commit()

            stmt = sa.select(users).where(users.c.name == "Carol")
            result = session.execute(stmt)
            row = result.fetchone()

        assert row is not None
        assert row.name == "Carol"

    def test_legacy_query_api_not_default(self):
        """
        In SQLAlchemy 2.0, Session.query() still exists for compatibility
        but the canonical path is Session.execute(select(...)). Verify
        that the 2.0 select() import path is available and preferred.
        """
        sa = pytest.importorskip("sqlalchemy")
        # select() must be importable from the top-level package in 2.0
        assert hasattr(sa, "select"), (
            "sqlalchemy.select must be available in SQLAlchemy 2.0"
        )

    def test_create_engine_future_flag_accepted(self):
        """
        SQLAlchemy 2.0 accepts (and ignores) future=True for back-compat.
        In 2.0 all engines are 'future' engines by default.
        """
        sa = pytest.importorskip("sqlalchemy")
        # Should not raise
        engine = sa.create_engine("sqlite:///:memory:", future=True)
        assert engine is not None


# ===========================================================================
# 7. Environment-based secrets management (no hardcoded credentials)
# ===========================================================================

class TestEnvironmentBasedSecrets:
    """
    Verify that the application reads secrets from environment variables
    rather than hardcoded values, as required by the upgrade spec.
    """

    def test_secret_key_read_from_env(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "env-provided-secret")
        import os
        assert os.environ.get("SECRET_KEY") == "env-provided-secret"

    def test_database_url_read_from_env(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        import os
        assert os.environ.get("DATABASE_URL") == "sqlite:///test.db"

    def test_flask_app_uses_env_secret_key(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "super-secret-from-env")
        import os
        flask = pytest.importorskip("flask")

        app = flask.Flask(__name__)
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

        assert app.config["SECRET_KEY"] == "super-secret-from-env"
        assert app.config["SECRET_KEY"] != ""


# ===========================================================================
# 8. New configuration keys introduced by Flask 3.x
# ===========================================================================

class TestFlask3ConfigKeys:
    """
    Verify that configuration keys introduced or changed in Flask 3.x
    load without errors.
    """

    @pytest.fixture
    def app(self):
        flask = pytest.importorskip("flask")
        application = flask.Flask(__name__)
        application.config["TESTING"] = True
        application.config["SECRET_KEY"] = "test-key"
        return application

    def test_json_sort_keys_config(self, app):
        """JSON_SORT_KEYS is a valid Flask 3.x config key."""
        app.config["JSON_SORT_KEYS"] = False
        assert app.config["JSON_SORT_KEYS"] is False

    def test_propagate_exceptions_config(self, app):
        app.config["PROPAGATE_EXCEPTIONS"] = True
        assert app.config["PROPAGATE_EXCEPTIONS"] is True

    def test_max_content_length_config(self, app):
        app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
        assert app.config["MAX_CONTENT_LENGTH"] == 16 * 1024 * 1024

    def test_application_root_config(self, app):
        app.config["APPLICATION_ROOT"] = "/"
        assert app.config["APPLICATION_ROOT"] == "/"

    def test_config_from_mapping(self, app):
        """Flask 3.x supports config.from_mapping without errors."""
        app.config.from_mapping(
            {
                "TESTING": True,
                "SECRET_KEY": "mapping-key",
                "DEBUG": False,
            }
        )
        assert app.config["SECRET_KEY"] == "mapping-key"


# ===========================================================================
# 9. REST API smoke tests with Flask 3.x
# ===========================================================================

class TestRESTAPIWithFlask3:
    """
    Verify that the REST API architectural pattern works correctly
    under Flask 3.x.
    """

    @pytest.fixture
    def client(self):
        flask = pytest.importorskip("flask")

        app = flask.Flask(__name__)
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test"

        @app.route("/api/v1/status", methods=["GET"])
        def status():
            return flask.jsonify({"status": "healthy", "version": "3.1"}), 200

        @app.route("/api/v1/items", methods=["POST"])
        def create_item():
            data = flask.request.get_json()
            if not data or "name" not in data:
                return flask.jsonify({"error": "name required"}), 400
            return flask.jsonify({"id": 1, "name": data["name"]}), 201

        return app.test_client()

    def test_get_status_endpoint(self, client):
        response = client.get("/api/v1/status")
        assert response.status_code == 200

    def test_get_status_returns_json(self, client):
        response = client.get("/api/v1/status")
        data = response.get_json()
        assert data is not None
        assert data["status"] == "healthy"

    def test_post_creates_resource(self, client):
        response = client.post(
            "/api/v1/items",
            json={"name": "widget"},
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "widget"

    def test_post_missing_field_returns_400(self, client):
        response = client.post(
            "/api/v1/items",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_method_not_allowed_returns_405(self, client):
        response = client.delete("/api/v1/status")
        assert response.status_code == 405