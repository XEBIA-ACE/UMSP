"""Endpoint and framework-surface tests for the Flask 1.x -> 3.x upgrade (JTT-3256)."""

from __future__ import annotations

import importlib
import importlib.metadata
import sys
import warnings
from pathlib import Path

import flask
import pytest
import werkzeug
from werkzeug.exceptions import HTTPException

from umsp import create_app

REPO_ROOT = Path(__file__).resolve().parents[1]


def _major(dist: str) -> int:
    return int(importlib.metadata.version(dist).split(".")[0])


class TestFrameworkVersions:
    def test_flask_is_3x(self):
        assert _major("flask") == 3, importlib.metadata.version("flask")

    def test_werkzeug_is_3x(self):
        assert _major("werkzeug") == 3, importlib.metadata.version("werkzeug")

    def test_requirements_pin_flask_3(self):
        text = (REPO_ROOT / "requirements.txt").read_text()
        assert "Flask==3." in text
        assert "Flask==1." not in text

    def test_flask_1x_removed_apis_are_gone(self):
        # Removed in Flask 2.x/3.x; code relying on them must have been migrated.
        assert not hasattr(flask, "escape")
        assert not hasattr(flask, "Markup")
        assert not hasattr(flask.json, "JSONEncoder")
        assert not hasattr(flask.Flask, "before_first_request")
        assert not hasattr(flask.Flask, "json_encoder")
        assert not hasattr(werkzeug, "__version__")

    def test_import_app_without_deprecation_warnings(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            for name in ("umsp", "umsp.api", "umsp.views", "umsp.errors"):
                sys.modules.pop(name, None)
                importlib.import_module(name)
            create_app({"TESTING": True})


class TestAppFactory:
    def test_create_app_returns_flask_instance(self, app):
        assert isinstance(app, flask.Flask)
        assert app.testing is True

    def test_config_override(self):
        app = create_app({"APP_NAME": "Custom"})
        assert app.config["APP_NAME"] == "Custom"

    def test_all_routes_registered(self, app):
        rules = {r.rule for r in app.url_map.iter_rules()}
        assert {"/", "/api/health", "/api/items", "/api/items/<int:item_id>"} <= rules


class TestTemplateRendering:
    def test_index_renders_template(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.mimetype == "text/html"
        body = resp.get_data(as_text=True)
        assert "<h1>UMSP</h1>" in body
        assert 'href="/api/health"' in body

    def test_template_autoescapes(self):
        app = create_app({"APP_NAME": "<b>x</b>"})
        body = app.test_client().get("/").get_data(as_text=True)
        assert "&lt;b&gt;x&lt;/b&gt;" in body
        assert "<b>x</b>" not in body


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["app"] == "UMSP"
        assert data["flask"].startswith("3.")

    def test_health_rejects_post(self, client):
        resp = client.post("/api/health")
        assert resp.status_code == 405
        assert resp.get_json()["error"] == "Method Not Allowed"


class TestItemsEndpoints:
    def test_list_empty(self, client):
        assert client.get("/api/items").get_json() == {"items": []}

    def test_create_and_get(self, client):
        resp = client.post("/api/items", json={"name": "widget"})
        assert resp.status_code == 201
        assert resp.headers["Location"] == "/api/items/1"
        assert resp.get_json() == {"id": 1, "name": "widget"}

        resp = client.get("/api/items/1")
        assert resp.status_code == 200
        assert resp.get_json() == {"id": 1, "name": "widget"}

        assert client.get("/api/items").get_json() == {"items": [{"id": 1, "name": "widget"}]}

    def test_create_without_body_is_400(self, client):
        resp = client.post("/api/items")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "Bad Request"

    def test_create_with_non_json_content_type_is_400(self, client):
        # Flask 3.x: request.get_json() raises 415 unless silent=True; the
        # handler uses silent=True so callers still get a 400 as under 1.x.
        resp = client.post("/api/items", data="name=x", content_type="text/plain")
        assert resp.status_code == 400

    def test_create_missing_name_is_400(self, client):
        assert client.post("/api/items", json={}).status_code == 400

    def test_get_missing_is_404_json(self, client):
        resp = client.get("/api/items/99")
        assert resp.status_code == 404
        assert resp.get_json() == {
            "error": "Not Found",
            "message": "item 99 not found",
            "status": 404,
        }

    def test_delete(self, client):
        client.post("/api/items", json={"name": "a"})
        assert client.delete("/api/items/1").status_code == 204
        assert client.delete("/api/items/1").status_code == 404

    def test_non_int_id_is_404(self, client):
        assert client.get("/api/items/abc").status_code == 404


class TestRequestResponseSurface:
    def test_request_get_json_strict_raises_415(self, app):
        with app.test_request_context("/x", method="POST", data="{}", content_type="text/plain"):
            with pytest.raises(HTTPException) as exc_info:
                flask.request.get_json()
            assert exc_info.value.code == 415

    def test_request_get_json_silent_returns_none(self, app):
        with app.test_request_context("/x", method="POST", data="{}", content_type="text/plain"):
            assert flask.request.get_json(silent=True) is None

    def test_json_provider_sorts_keys(self, app):
        with app.app_context():
            assert flask.json.dumps({"b": 1, "a": 2}) == '{"a": 2, "b": 1}'

    def test_unknown_route_returns_json_404(self, client):
        resp = client.get("/nope")
        assert resp.status_code == 404
        assert resp.get_json()["status"] == 404
