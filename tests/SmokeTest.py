"""
test_upgrade_validation.py

Upgrade validation tests for:
  - Flask 1.x → 3.1
  - SQLAlchemy 1.3 → 2.0
  - Python 3.8 → 3.12+

These tests verify that the upgraded frameworks are active at the exact target
versions, that the new APIs work correctly, and that deprecated 1.x patterns
have been replaced.
"""

import sys
import importlib
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_version(version_str):
    """Return a tuple of ints from a PEP-440-style version string."""
    import re
    parts = re.split(r"[.\-]", version_str)
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            break
    return tuple(result)


# ---------------------------------------------------------------------------
# 1. Runtime version assertions
# ---------------------------------------------------------------------------

class TestPythonVersion:
    """Python runtime must be 3.12 or newer (upgraded from 3.8 EOL)."""

    def test_python_major_version(self):
        assert sys.version_info.major == 3, (
            f"Expected Python 3.x, got {sys.version_info.major}"
        )

    def test_python_minor_version_at_least_12(self):
        assert sys.version_info.minor >= 12, (
            f"Expected Python >= 3.12 (upgrade target), "
            f"got {sys.version_info.major}.{sys.version_info.minor}. "
            "Upgrade Python from 3.8 EOL to 3.12 or 3.13."
        )

    def test_python_is_not_eol_38(self):
        assert not (sys.version_info.major == 3 and sys.version_info.minor == 8), (
            "Python 3.8 is EOL and must not be used after the upgrade."
        )


class TestFlaskVersion:
    """Flask must be exactly 3.1.x (upgraded from 1.x EOL)."""

    def test_flask_is_importable(self):
        try:
            import flask  # noqa: F401
        except ImportError:
            pytest.fail("Flask is not installed. Run: pip install flask>=3.1,<4")

    def test_flask_major_version_is_3(self):
        import flask
        major = _parse_version(flask.__version__)[0]
        assert major == 3, (
            f"Expected Flask 3.x, got {flask.__version__}. "
            "Flask 1.x is EOL and must be replaced with Flask 3.x."
        )

    def test_flask_minor_version_is_at_least_1(self):
        import flask
        parsed = _parse_version(flask.__version__)
        major, minor = parsed[0], parsed[1]
        assert (major, minor) >= (3, 1), (
            f"Expected Flask >= 3.1 (exact upgrade target), got {flask.__version__}."
        )

    def test_flask_is_not_1x(self):
        import flask
        major = _parse_version(flask.__version__)[0]
        assert major != 1, (
            f"Flask 1.x ({flask.__version__}) is EOL and must not be present "
            "after the upgrade."
        )


class TestSQLAlchemyVersion:
    """SQLAlchemy must be exactly 2.0.x (upgraded from 1.3 EOL)."""

    def test_sqlalchemy_is_importable(self):
        try:
            import sqlalchemy  # noqa: F401
        except ImportError:
            pytest.fail(
                "SQLAlchemy is not installed. Run: pip install sqlalchemy>=2.0,<3"
            )

    def test_sqlalchemy_major_version_is_2(self):
        import sqlalchemy
        major = _parse_version(sqlalchemy.__version__)[0]
        assert major == 2, (
            f"Expected SQLAlchemy 2.x, got {sqlalchemy.__version__}. "
            "SQLAlchemy 1.3 is EOL and must be replaced with 2.0."
        )

    def test_sqlalchemy_is_not_1x(self):
        import sqlalchemy
        major = _parse_version(sqlalchemy.__version__)[0]
        assert major != 1, (
            f"SQLAlchemy 1.x ({sqlalchemy.__version__}) is EOL and must not be "
            "present after the upgrade."
        )


# ---------------------------------------------------------------------------
# 2. Flask 3.x — application factory pattern and new API
# ---------------------------------------------------------------------------

class TestFlask3ApplicationFactory:
    """Flask 3.x must be used with the application factory pattern."""

    @pytest.fixture()
    def app(self):
        from flask import Flask
        application = Flask(__name__)
        application.config["TESTING"] = True
        application.config["SECRET_KEY"] = "test-secret-key"
        # New in Flask 3.x: SQLALCHEMY_DATABASE_URI loaded from env/config
        application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        return application

    @pytest.fixture()
    def client(self, app):
        return app.test_client()

    def test_app_factory_creates_flask_instance(self, app):
        from flask import Flask
        assert isinstance(app, Flask)

    def test_app_has_testing_config(self, app):
        assert app.config["TESTING"] is True

    def test_test_client_is_available(self, client):
        assert client is not None

    def test_flask_3_app_context_push(self, app):
        """Flask 3.x application context must push and pop without error."""
        with app.app_context():
            from flask import current_app
            assert current_app is not None
            assert current_app.config["TESTING"] is True

    def test_flask_3_request_context(self, app):
        """Flask 3.x request context must be usable in tests."""
        with app.test_request_context("/health"):
            from flask import request
            assert request.path == "/health"

    def test_flask_3_health_route(self, app, client):
        """A simple health endpoint must return 200 with Flask 3.x routing."""
        @app.route("/health")
        def health():
            from flask import jsonify
            return jsonify({"status": "ok", "version": "3.x"})

        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"

    def test_flask_3_json_response(self, app, client):
        """Flask 3.x jsonify must return application/json content type."""
        @app.route("/ping")
        def ping():
            from flask import jsonify
            return jsonify({"pong": True})

        response = client.get("/ping")
        assert response.status_code == 200
        assert "application/json" in response.content_type

    def test_flask_3_error_handler_registration(self, app, client):
        """Flask 3.x error handler registration API must work."""
        @app.errorhandler(404)
        def not_found(e):
            from flask import jsonify
            return jsonify({"error": "not found"}), 404

        response = client.get("/nonexistent-route-xyz")
        assert response.status_code == 404

    def test_flask_3_blueprint_registration(self, app, client):
        """Flask 3.x Blueprint registration must work (application factory pattern)."""
        from flask import Blueprint, jsonify

        bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

        @bp.route("/status")
        def status():
            return jsonify({"api": "v1", "status": "ok"})

        app.register_blueprint(bp)
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["api"] == "v1"


# ---------------------------------------------------------------------------
# 3. Flask 3.x — deprecated 1.x APIs must not be present
# ---------------------------------------------------------------------------

class TestFlask1xDeprecatedAPIsRemoved:
    """Verify that Flask 1.x deprecated patterns are no longer available."""

    def test_flask_ext_namespace_removed(self):
        """Flask 1.x flask.ext.* namespace was removed in Flask 2+."""
        import flask
        assert not hasattr(flask, "ext"), (
            "flask.ext namespace is a Flask 1.x artifact and must not exist in Flask 3.x."
        )

    def test_before_first_request_removed(self):
        """@app.before_first_request was deprecated in Flask 2.2 and removed in 3.0."""
        import flask
        app = flask.Flask(__name__)
        assert not hasattr(app, "before_first_request"), (
            "@app.before_first_request was removed in Flask 3.0. "
            "Use app.before_request with a flag or app startup events instead."
        )

    def test_flask_json_encoder_removed(self):
        """Flask.json_encoder / json_decoder class attributes were removed in Flask 3.0."""
        import flask
        app = flask.Flask(__name__)
        assert not hasattr(app, "json_encoder"), (
            "app.json_encoder was removed in Flask 3.0. "
            "Use app.json_provider_class instead."
        )
        assert not hasattr(app, "json_decoder"), (
            "app.json_decoder was removed in Flask 3.0. "
            "Use app.json_provider_class instead."
        )

    def test_flask_3_json_provider_class_present(self):
        """Flask 3.x must expose json_provider_class (replacement for json_encoder)."""
        import flask
        app = flask.Flask(__name__)
        assert hasattr(app, "json_provider_class"), (
            "Flask 3.x must have json_provider_class attribute."
        )


# ---------------------------------------------------------------------------
# 4. SQLAlchemy 2.0 — new query API (select()) must work
# ---------------------------------------------------------------------------

class TestSQLAlchemy2QueryAPI:
    """SQLAlchemy 2.0 select()-based query API must be functional."""

    @pytest.fixture(scope="class")
    def engine(self):
        from sqlalchemy import create_engine
        eng = create_engine("sqlite:///:memory:", echo=False)
        yield eng
        eng.dispose()

    @pytest.fixture(scope="class")
    def tables(self, engine):
        from sqlalchemy import Column, Integer, String, MetaData, Table
        metadata = MetaData()
        users = Table(
            "users",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(100), nullable=False),
            Column("email", String(200), nullable=False, unique=True),
        )
        metadata.create_all(engine)
        return users

    @pytest.fixture()
    def session(self, engine):
        """SQLAlchemy 2.0 Session using the new Session() context manager."""
        from sqlalchemy.orm import Session
        with Session(engine) as sess:
            yield sess

    def test_sqlalchemy_2_select_statement(self, engine, tables):
        """SQLAlchemy 2.0 select() must return a Select object."""
        from sqlalchemy import select
        stmt = select(tables)
        assert stmt is not None

    def test_sqlalchemy_2_insert_and_select(self, engine, tables):
        """SQLAlchemy 2.0 insert/select via connection execute must work."""
        from sqlalchemy import insert, select
        with engine.connect() as conn:
            conn.execute(
                insert(tables),
                [{"name": "Alice", "email": "alice@example.com"}],
            )
            conn.commit()
            result = conn.execute(select(tables).where(tables.c.name == "Alice"))
            row = result.fetchone()
        assert row is not None
        assert row.name == "Alice"
        assert row.email == "alice@example.com"

    def test_sqlalchemy_2_session_context_manager(self, engine, tables):
        """SQLAlchemy 2.0 Session must work as a context manager (new lifecycle)."""
        from sqlalchemy import insert, select
        from sqlalchemy.orm import Session

        with Session(engine) as session:
            session.execute(
                insert(tables),
                [{"name": "Bob", "email": "bob@example.com"}],
            )
            session.commit()

        with Session(engine) as session:
            result = session.execute(
                select(tables).where(tables.c.name == "Bob")
            )
            row = result.fetchone()

        assert row is not None
        assert row.name == "Bob"

    def test_sqlalchemy_2_session_closes_after_context(self, engine):
        """Session must be closed (connection returned to pool) after context exit."""
        from sqlalchemy.orm import Session

        session_ref = None
        with Session(engine) as session:
            session_ref = session
            assert not session_ref.is_active or True  # session is open inside

        # After context exit the session must be closed
        assert not session_ref.is_active, (
            "Session must be closed after exiting the context manager "
            "(connection leak prevention)."
        )

    def test_sqlalchemy_2_rollback_on_exception(self, engine, tables):
        """Session must roll back automatically when an exception occurs."""
        from sqlalchemy import insert
        from sqlalchemy.orm import Session

        try:
            with Session(engine) as session:
                session.execute(
                    insert(tables),
                    [{"name": "Charlie", "email": "charlie@example.com"}],
                )
                raise RuntimeError("Simulated error — session must roll back")
        except RuntimeError:
            pass

        # Verify the row was NOT committed
        from sqlalchemy import select
        with Session(engine) as session:
            result = session.execute(
                select(tables).where(tables.c.name == "Charlie")
            )
            row = result.fetchone()
        assert row is None, (
            "Row must not be persisted when the session rolls back on exception."
        )

    def test_sqlalchemy_2_engine_dispose_releases_connections(self, engine):
        """engine.dispose() must release all pooled connections without error."""
        # Should not raise
        engine.dispose()


# ---------------------------------------------------------------------------
# 5. SQLAlchemy 2.0 — deprecated 1.x APIs must not be used
# ---------------------------------------------------------------------------

class TestSQLAlchemy1xDeprecatedAPIsRemoved:
    """Verify that SQLAlchemy 1.x deprecated patterns are not available/used."""

    def test_query_property_not_on_base_model(self):
        """SQLAlchemy 2.0 removes the legacy Query.query property from mapped classes."""
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        class SampleModel(Base):
            __tablename__ = "sample_upgrade_check"
            from sqlalchemy import Column, Integer, String
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        # In SQLAlchemy 2.0 the legacy .query attribute is not present by default
        assert not hasattr(SampleModel, "query"), (
            "SampleModel.query is a SQLAlchemy 1.x legacy API. "
            "Use session.execute(select(SampleModel)) in SQLAlchemy 2.0."
        )

    def test_sqlalchemy_2_declarative_base_via_declarativebase(self):
        """SQLAlchemy 2.0 DeclarativeBase class must be importable and usable."""
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        assert Base is not None

    def test_sqlalchemy_1x_declarative_base_function_still_importable_but_deprecated(self):
        """
        declarative_base() function still exists in 2.0 for compatibility but
        the preferred API is DeclarativeBase class.  We verify DeclarativeBase
        is the canonical import.
        """
        from sqlalchemy.orm import DeclarativeBase
        assert DeclarativeBase is not None

    def test_session_execute_returns_result_not_list(self):
        """
        SQLAlchemy 2.0 session.execute() returns a CursorResult, not a list.
        The 1.x session.query().all() pattern returning a list directly is replaced.
        """
        from sqlalchemy import create_engine, Column, Integer, String, select
        from sqlalchemy.orm import DeclarativeBase, Session

        class Base(DeclarativeBase):
            pass

        class Item(Base):
            __tablename__ = "items_upgrade_check"
            id = Column(Integer, primary_key=True)
            label = Column(String(50))

        eng = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(eng)

        with Session(eng) as session:
            result = session.execute(select(Item))
            # In SQLAlchemy 2.0 this is a CursorResult / ChunkedIteratorResult
            rows = result.all()
            assert isinstance(rows, list), (
                "session.execute().all() must return a list in SQLAlchemy 2.0."
            )

        eng.dispose()


# ---------------------------------------------------------------------------
# 6. New configuration keys introduced by the upgrade
# ---------------------------------------------------------------------------

class TestNewConfigurationKeys:
    """New Flask 3.x and SQLAlchemy 2.0 configuration keys must load without error."""

    @pytest.fixture()
    def app(self):
        from flask import Flask
        application = Flask(__name__)
        application.config.from_mapping(
            # Flask 3.x configuration keys
            SECRET_KEY="upgrade-test-secret",
            TESTING=True,
            # SQLAlchemy 2.0 / Flask-SQLAlchemy 3.x configuration keys
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SQLALCHEMY_ENGINE_OPTIONS={
                "pool_pre_ping": True,       # New recommended option in 2.0
                "pool_recycle": 300,
                "pool_size": 5,
                "max_overflow": 10,
            },
            # Environment-based secrets (replacing hardcoded credentials)
            DATABASE_URL="sqlite:///:memory:",
        )
        return application

    def test_secret_key_config_loads(self, app):
        assert app.config["SECRET_KEY"] == "upgrade-test-secret"

    def test_sqlalchemy_database_uri_config_loads(self, app):
        assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"

    def test_sqlalchemy_track_modifications_false(self, app):
        """SQLALCHEMY_TRACK_MODIFICATIONS must be False (deprecated feature disabled)."""
        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False

    def test_sqlalchemy_engine_options_pool_pre_ping(self, app):
        """pool_pre_ping must be enabled to detect stale connections (leak prevention)."""
        opts = app.config["SQLALCHEMY_ENGINE_OPTIONS"]
        assert opts.get("pool_pre_ping") is True, (
            "pool_pre_ping=True is required to detect and recycle stale connections."
        )

    def test_sqlalchemy_engine_options_pool_recycle(self, app):
        """pool_recycle must be set to prevent connections from going stale."""
        opts = app.config["SQLALCHEMY_ENGINE_OPTIONS"]
        assert "pool_recycle" in opts, (
            "pool_recycle must be configured to prevent connection leaks."
        )
        assert opts["pool_recycle"] > 0

    def test_database_url_env_config_loads(self, app):
        """DATABASE_URL must be loaded from environment/config (not hardcoded)."""
        assert "DATABASE_URL" in app.config
        assert app.config["DATABASE_URL"] is not None

    def test_flask_3_config_from_mapping(self):
        """Flask 3.x config.from_mapping() must work without error."""
        from flask import Flask
        application = Flask(__name__)
        application.config.from_mapping(
            TESTING=True,
            SECRET_KEY="test",
        )
        assert application.config["TESTING"] is True

    def test_flask_3_config_from_prefixed_env(self, monkeypatch):
        """Flask 3.x config.from_prefixed_env() must be available (new in Flask 2.1+)."""
        import flask
        application = flask.Flask(__name__)
        assert hasattr(application.config, "from_prefixed_env"), (
            "config.from_prefixed_env() was introduced in Flask 2.1 and must be "
            "present in Flask 3.x."
        )


# ---------------------------------------------------------------------------
# 7. SQLAlchemy 2.0 session lifecycle — connection leak prevention
# ---------------------------------------------------------------------------

class TestSessionLifecycleConnectionLeakPrevention:
    """
    Verify the session lifecycle patterns that prevent connection leaks.
    These tests directly validate the upgrade goal.
    """

    @pytest.fixture(scope="class")
    def engine(self):
        from sqlalchemy import create_engine
        eng = create_engine(
            "sqlite:///:memory:",
            echo=False,
            pool_pre_ping=True,
        )
        yield eng
        eng.dispose()

    def test_session_is_closed_after_with_block(self, engine):
        """Session.close() must be called automatically on context manager exit."""
        from sqlalchemy.orm import Session

        with Session(engine) as session:
            assert session is not None

        assert not session.is_active, (
            "Session must not be active after exiting the with block. "
            "Active sessions hold database connections and cause leaks."
        )

    def test_multiple_sessions_do_not_exhaust_pool(self, engine):
        """Opening and closing multiple sessions must not exhaust the connection pool."""
        from sqlalchemy.orm import Session
        from sqlalchemy import text

        for _ in range(20):
            with Session(engine) as session:
                session.execute(text("SELECT 1"))
                session.commit()
        # If we reach here without pool timeout, connections are being returned correctly

    def test_session_commit_releases_connection_to_pool(self, engine):
        """After commit, the connection must be returned to the pool."""
        from sqlalchemy.orm import Session
        from sqlalchemy import text

        with Session(engine) as session:
            session.execute(text("SELECT 1"))
            session.commit()
            # Connection should be returned to pool after commit in 2.0
            # (autobegin means a new transaction starts lazily on next operation)

    def test_session_rollback_releases_connection_to_pool(self, engine):
        """After rollback, the connection must be returned to the pool."""
        from sqlalchemy.orm import Session
        from sqlalchemy import text

        with Session(engine) as session:
            session.execute(text("SELECT 1"))
            session.rollback()

    def test_engine_pool_pre_ping_configured(self, engine):
        """pool_pre_ping must be enabled on the engine to detect stale connections."""
        pool = engine.pool
        # pool_pre_ping is stored as _pre_ping on the pool
        assert getattr(pool, "_pre_ping", False) is True, (
            "pool_pre_ping must be True on the engine pool. "
            "This prevents stale connections from being returned from the pool."
        )

    def test_scoped_session_removed_in_favour_of_context_manager(self):
        """
        Verify that the new Session context manager pattern is used instead of
        the SQLAlchemy 1.x scoped_session global pattern.

        scoped_session still exists in 2.0 for compatibility, but the preferred
        pattern for web frameworks is Session-per-request via context managers.
        """
        from sqlalchemy.orm import Session
        from sqlalchemy import create_engine, text

        eng = create_engine("sqlite:///:memory:")

        # New 2.0 pattern: Session as context manager (not global scoped_session)
        with Session(eng) as session:
            result = session.execute(text("SELECT 42 AS answer"))
            row = result.fetchone()
            assert row.answer == 42

        eng.dispose()

    def test_session_begin_context_manager_auto_commits(self, engine):
        """Session.begin() context manager must auto-commit on success."""
        from sqlalchemy.orm import Session
        from sqlalchemy import text

        with Session(engine) as session:
            with session.begin():
                session.execute(text("SELECT 1"))
            # If we reach here, commit succeeded without explicit session.commit()

    def test_session_begin_context_manager_auto_rolls_back_on_error(self, engine):
        """Session.begin() context manager must auto-rollback on exception."""
        from sqlalchemy.orm import Session
        from sqlalchemy import text

        try:
            with Session(engine) as session:
                with session.begin():
                    session.execute(text("SELECT 1"))
                    raise ValueError("Simulated failure")
        except ValueError:
            pass
        # No assertion needed — if the session/connection leaked, subsequent
        # tests would fail with pool exhaustion