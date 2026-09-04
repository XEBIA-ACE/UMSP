from __future__ import annotations

from flask import Blueprint, current_app, render_template

bp = Blueprint("views", __name__)


@bp.get("/")
def index() -> str:
    return render_template("index.html", app_name=current_app.config["APP_NAME"])
