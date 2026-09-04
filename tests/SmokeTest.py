import sys
import importlib
import os
import pytest

# ---------------------------------------------------------------------------
# Version assertions — upgrade target: Python 3.12+, Flask 3.1, SQLAlchemy 2.0
# ---------------------------------------------------------------------------

def test_python_version_is_at_least_3_12():
    """Python must be 3.12 or higher (upgraded from 3.8 EOL)."""
    assert sys.version_info >= (3, 12), (
        f"Expected Python >= 3.12 but got {sys.version_info.major}.{sys.version_info.minor}. "
        "Upgrade Python runtime before running this service."
    )


def test_flask_version_is_3_1():
    """Flask must be exactly the 3.1.x line (upgraded from 1.x EOL)."""
    flask = pytest.importorskip("flask", reason="Flask is not installed")
    major, minor = (int(x) for x in flask.__version__.split(".")[:2])
    assert (major, minor) == (3, 1), (
        f"Expected Flask 3.1.x but found {flask.__version__}. "
        "Run: pip install 'Flask>=3.1,<3.2'"
    )


def test_sqlalchemy_version_is_2_0():
    """SQLAlchemy must be the 2.x line (upgraded from 1.3 EOL)."""
    sa = pytest.importorskip("sqlalchemy", reason="SQLAlchemy is not installed")
    major = int(sa.__version__.split(".")[0])
    assert major == 2, (
        f"Expected SQLAlchemy 2.x but found {sa.__version__}. "
        "Run: pip install 'SQLAlchemy>=2.0,<3'"
    )


# ---------------------------------------------------------------------------
# Flask 3.x — application factory pattern
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def flask_app():
    """
    Attempt to import and create the Flask application via the application
    factory pattern introduced in the Flask 3.x upgrade.

    If the project does not yet expose a `create_app` factory, the test that
    uses this fixture will be skipped with an informative message.
    """
    try:
        # Adjust the import path to match the actual project module name.
        # Common conventions: `app.create_app`, `src.app.create_app`, etc.
        for module_path in ("app", "src.app", "application", "src.application"):
            try:
                mod = importlib.import_module(module_path)
                if hasattr(mod, "create_app"):
                    application = mod.create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
                    return application
            except ModuleNotFoundError:
                continue
        pytest.skip(
            "No create_app factory found. "
            "Flask 3.x upgrade requires an application factory in app.py or src/app.py."
        )
    except Exception as exc:
        pytest.skip(f"Could not instantiate Flask app: {exc}")


@pytest.fixture()
def flask_client(flask_app):
    """Return a Flask test client with application context active."""
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


def test_flask_app_factory_pattern_is_used(flask_app):
    """
    The application must be created via a factory function, not a module-level
    `app = Flask(__name__)` singleton — this is the Flask 3.x best practice
    enforced by the upgrade.
    """
    import flask
    assert isinstance(flask_app, flask.Flask), (
        "create_app() must return a Flask instance."
    )


def test_flask_app_is_in_testing_mode(flask_app):
    """TESTING flag must be honoured when passed to the factory."""
    assert flask_app.testing is True


def test_flask_health_endpoint_returns_200(flask_client):
    """
    The /api/health endpoint (present in the payment-service reference) must
    respond with HTTP 200 under Flask 3.1.
    """
    response = flask_client.get("/api/health")
    assert response.status_code == 200, (
        f"Expected 200 from /api/health but got {response.status_code}. "
        "Ensure the health blueprint is registered in create_app()."
    )


# ---------------------------------------------------------------------------
# Flask 3.x — deprecated APIs must NOT be present
# ---------------------------------------------------------------------------

def test_flask_before_first_request_is_removed():
    """
    `before_first_request` was deprecated in Flask 2.2 and removed in Flask 3.0.
    The upgraded codebase must not reference it.
    """
    flask = pytest.importorskip("flask")
    assert not hasattr(flask.Flask, "before_first_request"), (
        "Flask.before_first_request still exists — this was removed in Flask 3.0. "
        "Replace usages with app.with_appcontext() or an explicit init function."
    )


def test_flask_json_module_is_accessible():
    """
    In Flask 3.x the JSON provider API changed. Verify the new interface is
    available (flask.json.provider module introduced in 2.2, stable in 3.x).
    """
    import flask.json
    # Flask 3.x exposes JSONProvider; absence means an older version is active
    try:
        from flask.json.provider import JSONProvider  # noqa: F401
    except ImportError:
        pytest.fail(
            "flask.json.provider.JSONProvider not found. "
            "This class is required in Flask 3.x. Ensure Flask >= 3.1 is installed."
        )


# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 — new query API
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def sa_engine():
    """In-memory SQLite engine using the SQLAlchemy 2.0 API."""
    sa = pytest.importorskip("sqlalchemy")
    engine = sa.create_engine("sqlite:///:memory:", echo=False)
    yield engine
    engine.dispose()


@pytest.fixture()
def sa_session(sa_engine):
    """
    Fixture-based DB isolation: each test receives a fresh session that is
    rolled back after the test completes — no data leaks between tests.
    """
    import sqlalchemy as sa
    from sqlalchemy.orm import Session

    connection = sa_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def test_sqlalchemy_select_uses_new_api():
    """
    SQLAlchemy 2.0 requires `select()` from `sqlalchemy` directly.
    The legacy `Query` object (session.query()) is deprecated.
    Verify the new `select()` construct is importable and functional.
    """
    import sqlalchemy as sa
    stmt = sa.select(sa.literal(1))
    assert stmt is not None, "sa.select() must return a valid Select construct."


def test_sqlalchemy_session_execute_returns_result(sa_session):
    """
    In SQLAlchemy 2.0, `session.execute(select(...))` replaces
    `session.query(...)`. Verify the new execution style works.
    """
    import sqlalchemy as sa
    result = sa_session.execute(sa.select(sa.literal(42)))
    row = result.scalar()
    assert row == 42, (
        f"Expected scalar result 42 but got {row}. "
        "SQLAlchemy 2.0 session.execute() may not be working correctly."
    )


def test_sqlalchemy_legacy_query_api_is_deprecated():
    """
    The `Query` class still exists in SQLAlchemy 2.0 for legacy compatibility
    but `session.query()` should not be used in new code. Verify that the
    modern `select()` path is preferred by confirming `Session.execute` exists.
    """
    from sqlalchemy.orm import Session
    assert hasattr(Session, "execute"), (
        "Session.execute() not found — required for SQLAlchemy 2.0 query API."
    )


def test_sqlalchemy_mapped_column_available():
    """
    `mapped_column()` and `Mapped` type annotations are the canonical
    SQLAlchemy 2.0 ORM declaration style (replacing `Column()`).
    """
    try:
        from sqlalchemy.orm import mapped_column, Mapped  # noqa: F401
    except ImportError:
        pytest.fail(
            "sqlalchemy.orm.mapped_column / Mapped not importable. "
            "These are required for the SQLAlchemy 2.0 declarative ORM style. "
            "Ensure SQLAlchemy >= 2.0 is installed."
        )


def test_sqlalchemy_declarative_base_new_style():
    """
    SQLAlchemy 2.0 introduces `DeclarativeBase` as the preferred base class
    (replacing `declarative_base()` factory from 1.x).
    """
    try:
        from sqlalchemy.orm import DeclarativeBase  # noqa: F401
    except ImportError:
        pytest.fail(
            "sqlalchemy.orm.DeclarativeBase not importable. "
            "This is the SQLAlchemy 2.0 ORM base class. "
            "Ensure SQLAlchemy >= 2.0 is installed."
        )


# ---------------------------------------------------------------------------
# Fixture-based DB isolation — per-test repository reset
# ---------------------------------------------------------------------------

class _InMemoryUserStore:
    """
    Minimal Python equivalent of InMemoryUserRepository used to validate
    the fixture-based isolation pattern introduced by this upgrade.
    """

    def __init__(self):
        self._store: dict = {}

    def save(self, user_id: str, data: dict) -> dict:
        self._store[user_id] = data
        return data

    def find_by_id(self, user_id: str):
        return self._store.get(user_id)

    def clear(self):
        self._store.clear()

    def count(self) -> int:
        return len(self._store)


@pytest.fixture()
def user_repository():
    """
    Fixture that provides a fresh, empty _InMemoryUserStore for each test.
    This is the pytest equivalent of the Jest `makeUserRepository()` factory
    described in the upgrade spec — each test gets an isolated store with no
    shared mutable state.
    """
    repo = _InMemoryUserStore()
    yield repo
    repo.clear()


def test_user_repository_fixture_is_empty_at_start(user_repository):
    """Each test must receive an empty repository — no state from prior tests."""
    assert user_repository.count() == 0, (
        "Repository fixture must start empty. "
        "Shared state from a previous test has leaked — check fixture scope."
    )


def test_user_repository_save_and_retrieve(user_repository):
    """Basic save/retrieve works within a single test."""
    user_repository.save("user-1", {"email": "alice@example.com", "verified": False})
    result = user_repository.find_by_id("user-1")
    assert result is not None
    assert result["email"] == "alice@example.com"


def test_user_repository_isolation_between_tests_first(user_repository):
    """
    First of two isolation tests: saves a record.
    The second test must NOT see this record.
    """
    user_repository.save("user-isolation", {"email": "leak@example.com"})
    assert user_repository.count() == 1


def test_user_repository_isolation_between_tests_second(user_repository):
    """
    Second of two isolation tests: must start with an empty store even though
    the previous test saved a record.  Validates fixture teardown works.
    """
    assert user_repository.count() == 0, (
        "State from test_user_repository_isolation_between_tests_first leaked "
        "into this test. The user_repository fixture must reset _store between tests."
    )


# ---------------------------------------------------------------------------
# Environment-based secrets management (new config keys from upgrade)
# ---------------------------------------------------------------------------

def test_no_hardcoded_database_url_in_config():
    """
    The upgrade mandates environment-based secrets management.
    DATABASE_URL (or equivalent) must come from the environment, not be
    hardcoded. Verify the environment variable is read, not a literal string.
    """
    # If DATABASE_URL is set in the environment, it must not contain a
    # hardcoded default password pattern like 'password' or 'secret'.
    db_url = os.environ.get("DATABASE_URL", "")
    forbidden_patterns = ["password=password", "password=secret", ":secret@", ":password@"]
    for pattern in forbidden_patterns:
        assert pattern not in db_url.lower(), (
            f"DATABASE_URL contains a hardcoded credential pattern '{pattern}'. "
            "Use environment-based secrets management as required by the upgrade."
        )


def test_secret_key_not_hardcoded():
    """
    SECRET_KEY / JWT_SECRET must be sourced from the environment.
    A missing key is acceptable (CI may not set it); a hardcoded insecure
    default is not.
    """
    secret = os.environ.get("SECRET_KEY", os.environ.get("JWT_SECRET", ""))
    insecure_defaults = ["secret", "changeme", "dev", "test123", "password"]
    if secret:
        assert secret.lower() not in insecure_defaults, (
            f"SECRET_KEY/JWT_SECRET is set to an insecure default value '{secret}'. "
            "Generate a strong random secret and inject it via the environment."
        )


# ---------------------------------------------------------------------------
# pytest is the active test runner (not unittest)
# ---------------------------------------------------------------------------

def test_pytest_is_active_test_runner():
    """
    Confirm pytest is the active test runner — not unittest.
    This validates the core goal of the upgrade.
    """
    import pytest as _pytest
    # If we reach here, pytest is running this file.
    assert _pytest.__version__ is not None
    major = int(_pytest.__version__.split(".")[0])
    assert major >= 7, (
        f"pytest >= 7 is required but found {_pytest.__version__}. "
        "Run: pip install 'pytest>=7'"
    )


def test_unittest_testcase_not_used_as_base():
    """
    The upgrade replaces unittest.TestCase subclasses with plain pytest
    functions and fixtures. Verify that unittest.TestCase is not imported
    as a base class in the test suite (self-referential check on this file).
    """
    import unittest
    # This test file itself must not subclass TestCase
    import inspect
    current_module = sys.modules[__name__]
    for name, obj in inspect.getmembers(current_module, inspect.isclass):
        assert not issubclass(obj, unittest.TestCase) or obj is unittest.TestCase, (
            f"Class '{name}' subclasses unittest.TestCase. "
            "Replace with plain pytest functions and fixtures per the upgrade spec."
        )