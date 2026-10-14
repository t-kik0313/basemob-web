"""画面移行の検証用データ。実チーム・実選手のデータを使わない。"""

import copy
import sys


SCREEN_PATHS = (
    "/players", "/register_player", "/edit_player/1", "/player_detail_R1/1",
    "/current_year_stats/1", "/player_history/1", "/input_form_R1/1",
    "/games", "/game/game1", "/teamstats", "/annual_stats_detail", "/pitchers",
    "/pawapuro", "/record_summary", "/schedule", "/events",
    "/admin/regulation", "/admin/qualitative_abilities",
)


def install(database, fixtures):
    database.documents = copy.deepcopy(fixtures)
    player = {
        "player_id": 1, "id": 1, "name": "選手A", "number": "1", "no": "1",
        "pos1": "遊", "pos2": "二", "pos3": "", "pitch_bat": "右投右打",
        "birth_date": "2000-01-01", "image_path": "default.png", "dan": 2,
        "meet_val": 70, "power_val": 70, "speed_val": 60, "arm_val": 60,
        "defense_val": 50, "catch_val": 50, "age": 26, "holding_points": 14,
        "chance_rank": "D", "left_rank": "D", "steal_rank": "D", "run_rank": "D",
        "injury": "D", "throw": "D", "catcher": "D", "monthly_avg_data": "[]",
        "pa": 4, "ab": 3, "hits": 2, "hr": 1, "avg": 2 / 3, "obp": .75,
        "slg": 5 / 3, "ops": .75 + 5 / 3, "games": 1, "sb": 1,
        "rbi": 2, "runs": 1, "so": 1, "bb": 1, "sf": 0, "sh": 0,
        "errors": 0, "gidp": 0,
    }
    for key in ("meet", "power", "speed", "arm", "defense", "catching"):
        player["plus_" + key] = 0
    database.documents[("teams", "DEMO", "players", "1")] = copy.deepcopy(player)
    database.documents[("players", "1")] = copy.deepcopy(player)
    database.documents[("basic_info", "1")] = copy.deepcopy(player)
    annual = dict.fromkeys((
        "games", "plate_apperances", "at_bats", "hits", "homeruns", "runs_batted_in",
        "scores", "stolen_bases", "doubles", "triples", "strike_outs", "bb", "hbp",
        "sacrifice_bants", "sacrifice_flies", "double_plays", "errors", "obp", "slg", "OPS",
    ), 0)
    annual.update(player_id=1, year=2025, batting_average=.3)
    database.documents[("annual_stats", "1_2025")] = annual
    database.documents[("record_meeting", "1")] = {
        "player_id": 1, "record_date": "2026-10-01", "run_short": 7,
        "run_long": 30, "throw_distance": 50, "batting_distance": 80,
        "pitch_speed": 100, "memo": "検証用",
    }
    database.documents[("teams", "DEMO", "games", "game1")] = {
        "date": "2026-10-25", "opponent": "チームB", "gameType": "practice",
        "scoreMy": 2, "scoreOpp": 1, "result": "W", "stadium": "1",
        "results": [{
            "player_id": 1, "name": "選手A", "order": 1, "position": "遊",
            "stats": {"PA": 4, "AB": 3, "H": 2, "HR": 1, "RBI": 2, "SB": 1},
            "actions": [
                {"action": "左安打", "result": "1B", "direction": "7", "runners": "0", "strikes": "0"},
                {"action": "本塁打", "result": "HR", "direction": "8", "runners": "2", "strikes": "1", "rbi": 2},
                {"action": "三振", "result": "K", "strikes": "2"},
                {"action": "四球", "result": "BB"},
            ],
        }],
        "pitchers": [{"name": "選手A", "outs": 6, "hits": 1, "hr": 0, "bb": 1, "hbp": 0, "so": 2, "runs": 1, "er": 1}],
    }
    originals = []
    for module in tuple(sys.modules.values()):
        if module and getattr(module, "__name__", "").startswith("webapp.") and hasattr(module, "get_players_data_json"):
            originals.append((module, module.get_players_data_json))
            module.get_players_data_json = lambda: [copy.deepcopy(player)]
    return originals


def restore(originals):
    for module, function in originals:
        module.get_players_data_json = function
