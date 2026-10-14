from flask import render_template, request, redirect, url_for
import traceback
from webapp import app
from webapp.firebase import db, db_old
from webapp.services.player_view import load_player_shell
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv
from webapp.stats.current_year_game import absorb_game
from webapp.services.season_records import PLATE_RESULT_MAP, extend_plate_records, iter_numbered_games


@app.route('/current_year_stats/<int:player_id>')
def current_year_stats(player_id):
    player = load_player_shell(player_id)
    if not player:
        return "Player not found", 404

    # ===== ここから今年度の個人成績（試合別詳細）を集計 =====
    target_name = str(player.get('name', '')).replace(" ", "").replace("　", "")
    target_id = str(player_id)

    current_year_games = []
    records = [] # テンプレートに渡すリストを追加
    annual_totals = {
        'pa': 0, 'ab': 0, 'hits': 0, 'hr': 0, 'rbi': 0, 'runs': 0, 'sb': 0,
        'doubles': 0, 'triples': 0, 'so': 0, 'bb': 0, 'hbp': 0, 'sh': 0, 'sf': 0,
        'gidp': 0, 'errors': 0, 'risp_ab': 0, 'risp_h': 0
    }

    RESULT_MAP = PLATE_RESULT_MAP

    try:
        for number, _doc, g_data in iter_numbered_games():
            game_date = g_data.get('date', '不明')

            results = g_data.get('results', [])
            for p in results:
                p_name = str(p.get('name', '')).replace(" ", "").replace("　", "")
                p_id = str(p.get('player_id', p.get('id', '')))

                if (target_name and (target_name in p_name or p_name in target_name)) or (target_id and target_id == p_id):
                    extend_plate_records(records, p, g_data, game_date, number, RESULT_MAP)
                    absorb_game(p, g_data, game_date, RESULT_MAP, annual_totals, current_year_games)

    except Exception as e:
        print(f"❌ 今年度成績 データ取得エラー: {e}")

    annual_totals['avg'] = annual_totals['hits'] / annual_totals['ab'] if annual_totals['ab'] > 0 else 0.0
    den = annual_totals['ab'] + annual_totals['bb'] + annual_totals['hbp'] + annual_totals['sf']
    annual_totals['obp'] = (annual_totals['hits'] + annual_totals['bb'] + annual_totals['hbp']) / den if den > 0 else 0.0
    tb = (annual_totals['hits'] - annual_totals['doubles'] - annual_totals['triples'] - annual_totals['hr']) + (annual_totals['doubles'] * 2) + (annual_totals['triples'] * 3) + (annual_totals['hr'] * 4)
    annual_totals['slg'] = tb / annual_totals['ab'] if annual_totals['ab'] > 0 else 0.0
    annual_totals['ops'] = annual_totals['obp'] + annual_totals['slg']
    annual_totals['risp_avg'] = annual_totals['risp_h'] / annual_totals['risp_ab'] if annual_totals['risp_ab'] > 0 else 0.0

    current_year_games.sort(key=lambda x: x['date'], reverse=True)

    return render_template('current_year_stats.html', player=player, records=records)
