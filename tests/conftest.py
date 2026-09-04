import pytest

from umsp import create_app
from umsp.api import reset_items


@pytest.fixture()
def app():
    app = create_app({"TESTING": True})
    reset_items()
    yield app
    reset_items()


@pytest.fixture()
def client(app):
    return app.test_client()
