# UMSP
ACE scaffold: UMSP

## Stack
- Python 3.10+
- Flask 3.1 / Werkzeug 3.1 (upgraded from Flask 1.x — JTT-3256)

## Run
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
flask --app umsp run          # or: python -m umsp
```

## Test / lint
```bash
pytest -W error::DeprecationWarning
flake8 .
```

## Flask 1.x -> 3.x migration notes
| Flask 1.x | Flask 3.x | Where |
|-----------|-----------|-------|
| Module-level `app = Flask(__name__)` | `create_app()` application factory | `umsp/__init__.py` |
| `@app.route(..., methods=["GET"])` | `@bp.get` / `@bp.post` / `@bp.delete` shortcuts | `umsp/api.py` |
| `request.get_json()` returns `None` on non-JSON | raises `415`; use `silent=True` for lenient parsing | `umsp/api.py` |
| `app.json_encoder` / `flask.json.JSONEncoder` | `app.json` provider (`DefaultJSONProvider`) | removed |
| `flask.escape`, `flask.Markup` | `markupsafe.escape`, `markupsafe.Markup` | removed |
| `@app.before_first_request` | run setup inside `create_app()` | removed |
| `werkzeug.__version__` | `importlib.metadata.version("werkzeug")` | `umsp/__init__.py` |
| `JSON_SORT_KEYS` / `JSONIFY_*` config keys | attributes on `app.json` | `umsp/config.py` |
