"""既存の業務処理を、画面データ API と静的シェルから呼び出す。"""

from datetime import date, datetime
from functools import wraps
import math

from flask import current_app, g, jsonify, make_response, request, send_from_directory
from werkzeug.exceptions import HTTPException

from webapp.teams.context import current_slug, current_team


def json_value(value):
    """画面に必要な値だけを JSON に変換する（Flask の内部情報は渡さない）。"""
    if value is request:
        return {"args": request.args.to_dict(), "path": request.path}
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if hasattr(value, "item"):
        return json_value(value.item())
    raise TypeError(f"Unsupported screen value: {type(value).__name__}")


def team_path(path):
    slug = current_slug()
    if slug and path.startswith("/") and not path.startswith(("/t/", "/static/")):
        return f"/t/{slug}{path}"
    return path


def screen_response(template, **context):
    """HTML を生成せず、ブラウザ描画用の構造化データを返す。"""
    team = current_team()
    slug = current_slug()
    shared = {
        "team_name": team["name"] if team else "",
        "team_id": team["id"] if team else "",
        "schedule_api": team_path("/api/schedule"),
        "abilities_api": team_path("/api/update_abilities"),
        "score_entry_url": "https://basemob-207a2.web.app/app.html"
        + (f"?team={team['id']}" if team else ""),
    }
    routes = {
        rule.endpoint: rule.rule
        for rule in current_app.url_map.iter_rules()
        if not rule.endpoint.startswith(("screen_api_", "action_api_"))
    }
    return jsonify({
        "view": template.replace(".html", ".njk"),
        "data": json_value({**shared, **context}),
        "meta": {
            "team_slug": slug,
            "logged_in": not bool(getattr(g, "public_view", False)),
            "routes": routes,
            "screen_routes": current_app.config["CLIENT_SCREEN_ROUTES"],
            "action_routes": current_app.config["CLIENT_ACTION_ROUTES"],
        },
    })


def api_response(result):
    response = make_response(result)
    if 300 <= response.status_code < 400 and response.headers.get("Location"):
        response = jsonify({"redirect": team_path(response.headers["Location"])})
    if response.is_json:
        response.headers["Cache-Control"] = "no-store"
        return response
    message = response.get_data(as_text=True)
    response = jsonify({"error": message or "処理に失敗しました。"})
    response.status_code = make_response(result).status_code
    return response


def execute_api(function, *args, **kwargs):
    try:
        return api_response(function(*args, **kwargs))
    except HTTPException as error:
        return jsonify({"error": error.description}), error.code
    except Exception:
        current_app.logger.exception("画面 API の処理に失敗しました")
        return jsonify({"error": "データの読み込み・保存に失敗しました。"}), 500


def page_route(rule, **options):
    """GET は静的シェル、/api/screens/... は既存処理の JSON を返す。"""
    def decorate(function):
        from webapp import app

        methods = options.get("methods", ["GET"])
        app.config.setdefault("CLIENT_SCREEN_ROUTES", {})[rule] = list(methods)
        app.config.setdefault("CLIENT_ACTION_ROUTES", {})

        @wraps(function)
        def page(*args, **kwargs):
            if request.method in ("GET", "HEAD"):
                return send_from_directory(app.static_folder, "spa/index.html")
            return execute_api(function, *args, **kwargs)

        @wraps(function)
        def screen_api(*args, **kwargs):
            return execute_api(function, *args, **kwargs)

        app.route(rule, **options)(page)
        app.route("/api/screens" + rule, methods=methods,
                  endpoint="screen_api_" + function.__name__)(screen_api)
        return page
    return decorate


def action_route(rule, **options):
    """既存フォームの更新処理を JSON 応答の API としても公開する。"""
    def decorate(function):
        from webapp import app

        app.config.setdefault("CLIENT_ACTION_ROUTES", {})[rule] = options.get("methods", ["POST"])

        @wraps(function)
        def action_api(*args, **kwargs):
            return execute_api(function, *args, **kwargs)

        app.route(rule, **options)(function)
        app.route("/api/actions" + rule, endpoint="action_api_" + function.__name__,
                  **options)(action_api)
        return function
    return decorate
