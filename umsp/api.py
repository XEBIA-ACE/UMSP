"""JSON API endpoints.

Notable Flask 3.x differences from 1.x exercised here:
- ``request.get_json()`` raises ``415 Unsupported Media Type`` when the
  Content-Type is not JSON (1.x returned ``None``); use ``silent=True`` or
  ``force=True`` where lenient parsing is desired.
- ``abort``/``jsonify`` are imported from ``flask``; ``flask.json.JSONEncoder``
  is gone, custom serialisation goes through ``app.json``.
"""

from __future__ import annotations

from flask import Blueprint, Response, abort, current_app, jsonify, request, url_for

from umsp import runtime_info

bp = Blueprint("api", __name__)

_ITEMS: dict[int, dict[str, object]] = {}


def reset_items() -> None:
    _ITEMS.clear()


@bp.get("/health")
def health() -> Response:
    return jsonify(status="ok", app=current_app.config["APP_NAME"], **runtime_info())


@bp.get("/items")
def list_items() -> Response:
    return jsonify(items=list(_ITEMS.values()))


@bp.get("/items/<int:item_id>")
def get_item(item_id: int) -> Response:
    item = _ITEMS.get(item_id)
    if item is None:
        abort(404, description=f"item {item_id} not found")
    return jsonify(item)


@bp.post("/items")
def create_item() -> tuple[Response, int, dict[str, str]]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload.get("name"):
        abort(400, description="JSON body with a 'name' field is required")
    item_id = max(_ITEMS, default=0) + 1
    item = {"id": item_id, "name": payload["name"]}
    _ITEMS[item_id] = item
    location = url_for("api.get_item", item_id=item_id)
    return jsonify(item), 201, {"Location": location}


@bp.delete("/items/<int:item_id>")
def delete_item(item_id: int) -> tuple[str, int]:
    if _ITEMS.pop(item_id, None) is None:
        abort(404, description=f"item {item_id} not found")
    return "", 204
