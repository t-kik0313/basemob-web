from flask import render_template, request, redirect, url_for
import traceback
from webapp import app
from webapp.firebase import db, db_old
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv
from webapp.services.player_history import append_current_season


@app.route('/player_history/<int:player_id>')
def player_history(player_id):
    from flask import request
    players_df = load_players_df()
    annual_df = get_cleaned_df('annual_stats')
    if players_df.empty or player_id not in players_df['player_id'].values: return "Player not found", 404
    player = players_df[players_df['player_id'] == player_id].iloc[0].to_dict()
    player['id'] = player_id; player['player_id'] = player_id

    f_year = request.args.get('year', '')
    f_type = request.args.get('game_type', '')
    history_stats = []

    # 1. 過去データの取得
    if not annual_df.empty and 'player_id' in annual_df.columns:
        past_data = annual_df[annual_df['player_id'] == player_id].to_dict(orient='records')
        for r in past_data:
            if f_year and str(r.get('year', '')) != f_year: continue
            r['risp_ab'] = 0; r['risp_h'] = 0; r['risp_avg'] = 0.0
            history_stats.append(r)

    # 2. 最新（Firestore）データの集計
    append_current_season(player, player_id, f_year, f_type, history_stats)

    history_stats = sorted(history_stats, key=lambda x: int(x['year']), reverse=True)

    # 3. 通算成績（合計）の計算
    total_stats = {k: 0 for k in ['games', 'plate_apperances', 'at_bats', 'hits', 'homeruns', 'runs_batted_in', 'scores', 'stolen_bases', 'doubles', 'triples', 'strike_outs', 'bb', 'hbp', 'sacrifice_bants', 'sacrifice_flies', 'double_plays', 'errors', 'risp_ab', 'risp_h']}
    for r in history_stats:
        for k in total_stats.keys(): total_stats[k] += int(float(r.get(k, 0)))

    ts = total_stats
    ts['batting_average'] = ts['hits'] / ts['at_bats'] if ts['at_bats'] > 0 else 0.0
    den = ts['at_bats'] + ts['bb'] + ts['hbp'] + ts['sacrifice_flies']
    ts['obp'] = (ts['hits'] + ts['bb'] + ts['hbp']) / den if den > 0 else 0.0
    tb = (ts['hits'] - ts['doubles'] - ts['triples'] - ts['homeruns']) + (ts['doubles'] * 2) + (ts['triples'] * 3) + (ts['homeruns'] * 4)
    ts['slg'] = tb / ts['at_bats'] if ts['at_bats'] > 0 else 0.0
    ts['OPS'] = ts['obp'] + ts['slg']
    ts['risp_avg'] = ts['risp_h'] / ts['risp_ab'] if ts['risp_ab'] > 0 else 0.0

    return render_template('player_history.html', player=player, history_stats=history_stats, total_stats=total_stats, request=request)

