from __future__ import annotations

import os


class Config:
    SECRET_KEY = os.environ.get("UMSP_SECRET_KEY", "dev-only-change-me")
    # Flask 1.x used JSON_SORT_KEYS / JSONIFY_PRETTYPRINT_REGULAR config keys;
    # in Flask 3.x these are attributes on app.json (see create_app / errors).
    APP_NAME = "UMSP"
