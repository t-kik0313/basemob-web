import math

from flask import render_template, request, redirect, url_for
import traceback
from webapp import app
from webapp.firebase import db, db_old
from webapp.tenant import games_ref, pa_per_game, roster_rows
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv
from webapp.routes.annual_tables import build_annual_tables
from webapp.routes.annual_tally import tally_games


@app.route('/annual_stats_detail')
def annual_stats_detail():
    try:
        print("--- ⚾ 今年度の成績集計を開始します ---")
        loaded_games = list(games_ref().stream())
        team_games = sum(1 for doc in loaded_games if (doc.to_dict() or {}).get('results'))
        pa_coef = pa_per_game()
        regulation_pa = math.ceil(round(team_games * pa_coef, 6)) if team_games else 0
        player_stats = {}

        # 🌟 翻訳辞書
        RESULT_MAP = {
            "単打": "H", "2塁打": "2BH", "3塁打": "3BH", "本塁打": "HR",
            "ゴロ": "ゴロ", "フライ": "フライ", "ライナー": "ライナー",
            "三振": "三振", "四球": "四球", "死球": "死球",
            "犠打": "犠打", "犠飛": "犠飛", "失策出塁": "敵失", "野手選択": "野選"
        }

        # 🌟 マスターデータの事前ロード（ループ内で何度も呼ぶのを防ぐ）
        tally_games(loaded_games, player_stats, get_players_data_json(), RESULT_MAP)
        stats_list, team_total = build_annual_tables(player_stats, regulation_pa, roster_rows())

        return render_template(
            'annual_stats_detail.html',
            stats=stats_list,
            team_total=team_total,
            regulation_pa=regulation_pa,
        )

    except Exception as e:
        print(f"Error processing annual stats detail: {e}")
        return f"エラーが発生しました: {e}", 500

