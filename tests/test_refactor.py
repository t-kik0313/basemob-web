"""構成変更後の互換性を、実 Firestore に接続せず確認する。"""

import copy
from datetime import date
import importlib
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from io import BytesIO
from tempfile import TemporaryDirectory

from werkzeug.security import generate_password_hash


ROOT = Path(os.environ.get("BASEMOB_TEST_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))


class Snapshot:
    def __init__(self, path, data):
        self.id = path[-1]
        self.exists = data is not None
        self.data = copy.deepcopy(data)

    def to_dict(self):
        return copy.deepcopy(self.data)


class Reference:
    def __init__(self, database, path):
        self.database = database
        self.path = path

    def collection(self, name):
        return Reference(self.database, self.path + (name,))

    def document(self, name):
        return Reference(self.database, self.path + (name,))

    def stream(self):
        return iter([
            Snapshot(path, data)
            for path, data in self.database.documents.items()
            if path[:-1] == self.path
        ])

    def get(self, transaction=None):
        if len(self.path) % 2:
            return list(self.stream())
        return Snapshot(self.path, self.database.documents.get(self.path))

    def order_by(self, field):
        return self

    def set(self, data, merge=False):
        existing = self.database.documents.get(self.path, {}) if merge else {}
        self.database.documents[self.path] = {**existing, **copy.deepcopy(data)}

    def update(self, data):
        self.set(data, merge=True)


class Transaction:
    def set(self, reference, data, merge=False):
        reference.set(data, merge=merge)


class Database:
    def __init__(self):
        self.documents = {}

    def collection(self, name):
        return Reference(self, (name,))

    def transaction(self):
        return Transaction()


# 起動前に DB 接続モジュールを置き換え、認証鍵の読み込みも防ぐ。
database = Database()
firebase = types.ModuleType("webapp.firebase")
firebase.db = database
firebase.db_old = database
firebase_admin = types.ModuleType("firebase_admin")
firebase_admin.firestore = types.SimpleNamespace(transactional=lambda function: function)
sys.modules["webapp.firebase"] = firebase
sys.modules["firebase_admin"] = firebase_admin

from webapp import app  # noqa: E402
from webapp import schedule_poll as poll  # noqa: E402
from webapp import tenant  # noqa: E402


FIXTURES = {
    ("teams", "DEMO"): {
        "name": "テストチーム", "slug": "demo", "login_id": "demo-login",
        "password_hash": generate_password_hash("test-only-password", method="pbkdf2:sha256"),
        "paPerGame": 1.8,
    },
    ("teams", "DEMO", "players", "1"): {
        "player_id": 1, "name": "選手A", "number": "1",
        "pos1": "遊", "pitch_bat": "右投右打", "image_path": "default.png",
    },
}


class RefactorCompatibilityTests(unittest.TestCase):
    def setUp(self):
        database.documents = copy.deepcopy(FIXTURES)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_registered_endpoints(self):
        expected = {
            "index", "players", "current_year_stats", "player_detail_R1",
            "update_abilities", "input_form_R1", "save_record", "update_game_record",
            "delete_game_record", "pawapuro", "register_player", "edit_player",
            "record_summary", "games", "teamstats", "player_history", "pitchers",
            "game_detail", "upload_scoreboard_image", "save_youtube_link",
            "annual_stats_detail", "api_schedule", "api_schedule_poll", "schedule",
            "api_events", "api_events_post", "events", "qualitative_abilities",
            "regulation_settings", "csv_data", "static",
        }
        actual = {rule.endpoint for rule in app.url_map.iter_rules()}
        self.assertEqual({name for name in actual if not name.startswith(("screen_api_", "action_api_"))}, expected)
        self.assertEqual(sum(name.startswith("screen_api_") for name in actual), 18)
        self.assertEqual(sum(name.startswith("action_api_") for name in actual), 5)

    def test_member_authentication(self):
        self.assertEqual(self.client.get("/t/demo/players").status_code, 401)
        response = self.client.get(
            "/t/demo/players", auth=("demo-login", "test-only-password")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("/static/app/app.js", response.get_data(as_text=True))
        self.assertNotIn("選手A", response.get_data(as_text=True))
        self.assertIn("team_login=", response.headers["Set-Cookie"])
        response.close()
        data = self.client.get("/t/demo/api/screens/players")
        self.assertEqual(data.json["data"]["players"][0]["name"], "選手A")

    def test_unprefixed_redirect_keeps_query(self):
        response = self.client.get(
            "/games?year=2026", auth=("demo-login", "test-only-password")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/t/demo/games?year=2026")

    def test_public_pages(self):
        for path in ("schedule", "events"):
            with self.subTest(path=path):
                response = self.client.get(f"/t/demo/{path}")
                self.assertEqual(response.status_code, 200)
                response.close()

    def test_public_api_response_shapes(self):
        schedule = self.client.get("/t/demo/api/schedule")
        self.assertEqual(schedule.status_code, 200)
        self.assertEqual(schedule.json["people"], [{"id": "1", "name": "選手A"}])
        self.assertEqual(schedule.json["games"], {})
        events = self.client.get("/t/demo/api/events")
        self.assertEqual(set(events.json), {"events", "people", "peopleCustom"})

    def test_public_answer_persists(self):
        with patch("webapp.routes.schedule.japan_today", return_value=date(2026, 10, 14)):
            response = self.client.post("/t/demo/api/schedule/poll", json={
                "action": "answer", "player_id": 1,
                "answers": {"2026-10-25": {"status": "all"}},
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["answers"]["2026-10-25"]["1"], {"status": "all"})

    def test_people_and_event_creation_require_login(self):
        requests = [
            ("/t/demo/api/schedule/poll", {"action": "people", "people": []}),
            ("/t/demo/api/events", {"action": "create", "event": {}}),
        ]
        for path, body in requests:
            with self.subTest(path=path):
                response = self.client.post(path, json=body)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json, {"error": "ログインが必要です。"})

    def test_invalid_json_returns_400(self):
        for path in ("api/schedule/poll", "api/events"):
            self.assertEqual(self.client.post(f"/t/demo/{path}", json=[]).status_code, 400)

    def test_ability_update_contract(self):
        response = self.client.post("/t/demo/api/update_abilities", json={
            "player_id": 1, "abilities": {"plus_meet": 3},
        }, auth=("demo-login", "test-only-password"))
        self.assertEqual(response.json, {"ok": True})
        self.assertEqual(database.documents[("teams", "DEMO", "players", "1")]["plus_meet"], 3)
        self.assertEqual(self.client.post("/t/demo/api/update_abilities", json={
            "player_id": 1, "abilities": {"plus_meet": 17},
        }).status_code, 400)

    def test_template_compilation(self):
        sources = json.loads((ROOT / "static/app/views.json").read_text())
        self.assertEqual(sum("/" not in name for name in sources), 18)
        self.assertTrue(all(name.endswith(".njk") for name in sources))

    def test_public_screen_data_and_private_data(self):
        for name in ("schedule", "events"):
            response = self.client.get(f"/t/demo/api/screens/{name}")
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json["meta"]["logged_in"])
            self.assertNotIn("password_hash", response.get_data(as_text=True))
        self.assertEqual(self.client.get("/t/demo/api/screens/players").status_code, 401)

    def test_form_api_redirect_and_validation(self):
        response = self.client.post("/t/demo/api/screens/register_player", data={
            "name": "", "number": "", "throw_hand": "右", "bat_hand": "右",
        }, auth=("demo-login", "test-only-password"))
        self.assertEqual(response.json["view"], "register.njk")
        self.assertIn("入力", response.json["data"]["error"])
        response = self.client.post("/t/demo/api/screens/register_player", data={
            "name": "選手B", "number": "2", "throw_hand": "右", "bat_hand": "右",
        })
        self.assertEqual(response.json, {"redirect": "/t/demo/players"})
        self.assertEqual(database.documents[("teams", "DEMO", "players", "2")]["name"], "選手B")

    def test_action_api_errors_and_redirect(self):
        response = self.client.post("/t/demo/api/actions/game/missing/youtube", data={
            "youtube_url": "https://example.com/video",
        }, auth=("demo-login", "test-only-password"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "試合が見つかりません"})
        database.documents[("teams", "DEMO", "games", "game1")] = {"date": "2026-10-25"}
        response = self.client.post("/t/demo/api/actions/game/game1/youtube", data={
            "youtube_url": "https://example.com/video",
        })
        self.assertEqual(response.json, {"redirect": "/t/demo/game/game1"})

    def test_all_screen_apis_return_structured_data(self):
        from screen_fixtures import SCREEN_PATHS, install, restore
        originals = install(database, FIXTURES)
        try:
            for path in SCREEN_PATHS:
                with self.subTest(path=path):
                    response = self.client.get("/t/demo/api/screens" + path,
                                               auth=("demo-login", "test-only-password"))
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(set(response.json), {"view", "data", "meta"})
                    self.assertNotIn("html", response.json)
                    self.assertNotIn("password_hash", response.get_data(as_text=True))
        finally:
            restore(originals)

    def test_upload_action_api(self):
        database.documents[("teams", "DEMO", "games", "game1")] = {"date": "2026-10-25"}
        with TemporaryDirectory() as directory:
            with patch("webapp.routes.game_detail.BASE_DIR", directory):
                response = self.client.post("/t/demo/api/actions/game/game1/scoreboard_image",
                    data={"scoreboard_image": (BytesIO(b"test-image"), "score.png")},
                    content_type="multipart/form-data", auth=("demo-login", "test-only-password"))
                self.assertEqual(response.json, {"redirect": "/t/demo/game/game1"})
                self.assertTrue((Path(directory) / "static/scoreboard_images/demo/game1.png").exists())

    def test_screen_errors_are_json(self):
        response = self.client.get("/t/demo/api/screens/player_detail_R1/999",
                                  auth=("demo-login", "test-only-password"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "Player not found"})
        with patch("webapp.routes.current_year.load_player_shell", side_effect=RuntimeError("test failure")):
            with self.assertLogs(app.logger, level="ERROR"):
                response = self.client.get("/t/demo/api/screens/current_year_stats/1")
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json, {"error": "データの読み込み・保存に失敗しました。"})

    def test_date_windows_and_game_normalization(self):
        self.assertEqual(poll.window_end(date(2026, 12, 14)), date(2027, 1, 31))
        self.assertEqual(poll.event_window_end(date(2026, 10, 14)), date(2027, 4, 30))
        game = poll.normalize_game({"slot": "am", "lineup": [{"n": "選手A", "p": "遊"}]})
        self.assertEqual(len(game["lineup"]), 10)
        self.assertEqual(game["uniform"], "黒")

    def test_event_date_replacement_keeps_answers(self):
        state = poll.normalize_poll(None)
        poll.apply_event_put(state, "", {"name": "イベント", "dates": ["2026-10-25"]}, date(2026, 10, 14))
        event_id = next(iter(state["events"]))
        poll.apply_event_answer(state, event_id, 1, None, {"2026-10-25": {"status": "in"}}, {1}, {})
        poll.apply_event_put(state, event_id, {"name": "イベント", "dates": ["2026-11-01"]}, date(2026, 10, 14))
        self.assertEqual(state["events"][event_id]["answers"], {"2026-11-01": {"1": {"status": "in"}}})

    def test_legacy_imports_and_commands(self):
        for name in (
            "webapp.routes.misc", "webapp.routes.annual_tables",
            "webapp.routes.current_year_records", "webapp.create_team",
            "webapp.migrate_team",
        ):
            importlib.import_module(name)
        with patch("sys.argv", ["webapp.create_team"]):
            with self.assertRaisesRegex(SystemExit, "使い方"):
                import runpy
                runpy.run_path(str(ROOT / "webapp" / "create_team.py"), run_name="__main__")
        with app.test_request_context("/players", environ_overrides={"basemob.team_slug": "demo"}):
            self.assertEqual(tenant.current_team_id(), "DEMO")
            self.assertEqual(tenant.next_player_id(), 2)


def response_snapshot():
    """分割前後のルート・公開画面・JSON 応答を比較する検証用出力。"""
    database.documents = copy.deepcopy(FIXTURES)
    with app.test_client() as client:
        responses = {}
        for path in ("/t/demo/schedule", "/t/demo/events", "/t/demo/api/schedule", "/t/demo/api/events"):
            response = client.get(path)
            responses[path] = {"status": response.status_code, "body": response.get_data(as_text=True)}
    rules = sorted((r.rule, r.endpoint, sorted(r.methods)) for r in app.url_map.iter_rules())
    return {"rules": rules, "responses": responses}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--snapshot":
        Path(sys.argv[2]).write_text(json.dumps(response_snapshot(), ensure_ascii=False, sort_keys=True))
    else:
        unittest.main()
