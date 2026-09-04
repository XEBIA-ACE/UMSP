from __future__ import annotations

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException) -> tuple[Response, int]:
        code = exc.code or 500
        return jsonify(error=exc.name, message=exc.description, status=code), code
