import json
import os
import pandas as pd
from webapp.config import JSON_PLAYERS
from webapp.stats.ability_power import ability_power
from webapp.stats.ability_ranks import ability_ranks
from webapp.stats.batting_count import batting_count
from webapp.stats.batting_splits import batting_splits
from webapp.stats.player_shell import player_shell
from webapp.stats.prepare_frames import prepare_frames
from webapp.stats.recent_form import recent_form
from webapp.utils import numpy_encoder


def _log_error(message):
    from webapp import app
    app.logger.error(message)


def _cache_path():
    from webapp.teams.context import current_team_id
    team_id = current_team_id()
    if not team_id or team_id == 'RYUNEN':
        return JSON_PLAYERS
    folder = os.path.dirname(JSON_PLAYERS)
    return os.path.join(folder, f'players_data_{team_id}.json')


def update_json_from_csv():
    try:
        frames = prepare_frames()
        if frames is None:
            return

        players_list = []
        game_df = frames["game_df"]
        player_games = {}
        if not game_df.empty and "player_id" in game_df.columns:
            for key, grp in game_df.groupby("player_id", sort=False):
                try:
                    player_games[int(key)] = grp
                except (TypeError, ValueError):
                    player_games[key] = grp
        empty_games = pd.DataFrame(columns=game_df.columns) if not game_df.empty else pd.DataFrame()
        for _, p_row in frames["players_df"].iterrows():
            try:
                pid, p_data = player_shell(p_row)
                box = batting_count(player_games.get(pid, empty_games))
                box["pid"] = pid
                batting_splits(p_data, box)
                ability_power(p_data, box, frames)
                ability_ranks(p_data, box, frames)
                recent_form(p_data, box)
                players_list.append(p_data)
            except Exception as loop_e:
                _log_error(f"Error processing player {p_row.get('player_id', 'Unknown')}: {loop_e}")
                continue

        with open(_cache_path(), 'w', encoding='utf-8') as f:
            json.dump(players_list, f, ensure_ascii=False, indent=4, default=numpy_encoder)

    except Exception as e:
        _log_error(f"FATAL ERROR in update_json_from_csv: {e}")


def get_players_data_json():
    path = _cache_path()
    if not os.path.exists(path):
        if path != JSON_PLAYERS:
            return []
        update_json_from_csv()
        path = _cache_path()
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return []
