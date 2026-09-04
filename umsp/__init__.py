"""UMSP application package.

Flask 3.x application-factory entry point. ``create_app`` replaces the
module-level ``app = Flask(__name__)`` singleton used with Flask 1.x.
"""

from __future__ import annotations

import importlib.metadata
from typing import Any, Mapping

from flask import Flask

from umsp.config import Config
from umsp.errors import register_error_handlers

__version__ = "0.2.0"


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.from_mapping(test_config)

    from umsp.api import bp as api_bp
    from umsp.views import bp as views_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    register_error_handlers(app)
    return app


def runtime_info() -> dict[str, str]:
    return {
        "umsp": __version__,
        "flask": importlib.metadata.version("flask"),
        "werkzeug": importlib.metadata.version("werkzeug"),
    }
