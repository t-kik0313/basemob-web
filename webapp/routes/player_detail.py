from flask import jsonify, render_template, request, redirect, url_for
import traceback
from webapp import app
from webapp.firebase import db, db_old
from webapp.services.player_view import load_player_shell
from webapp.repositories.references import players_ref
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv
from webapp.stats.player_form import build_form_summary
from webapp.services.player_records import collect_detail_records
from webapp.data import load_merged_data
from webapp.services.season_records import collect_season
from webapp.stats.ability_power import apply_season_meet, current_season_regulation_pa
from webapp.stats.ability_ranks import (
    apply_meeting_run_rank,
    apply_plate_abilities,
    apply_steal_rank,
    flag_on as _flag_on,
    lit_special_abilities,
)


@app.route('/player_detail_R1/<int:player_id>')
def player_detail_R1(player_id):
    player = load_player_shell(player_id)
    if not player:
        return "Player not found", 404

    # 🌟 名前の空白を消去して比較用ネームを作る
    target_name = str(player.get('name', '')).replace(" ", "").replace("　", "")
    target_id = str(player_id)

    records, annual_rbi, annual_sb, annual_h, annual_ab, annual_hr = collect_detail_records(target_name, target_id)
    summary = build_form_summary(records, annual_h, annual_ab)
    plate_records, stolen_bases = collect_season(target_name, target_id)
    apply_season_meet(player, plate_records, current_season_regulation_pa())
    apply_plate_abilities(player, plate_records)
    apply_steal_rank(player, stolen_bases)
    meeting = load_merged_data()
    apply_meeting_run_rank(player, [] if meeting.empty else meeting.to_dict(orient='records'))
    player['t_sayonara'] = _flag_on(player.get('qual_sayonara'))
    active_skills = lit_special_abilities(player)

    return render_template('player_detail_R1.html',
                           player=player,
                           active_skills=active_skills,
                           records=records,
                           annual_rbi=annual_rbi,
                           annual_sb=annual_sb,
                           annual_h=annual_h,
                           annual_ab=annual_ab,
                           annual_hr=annual_hr,
                           **summary)


ABILITY_KEYS = ('plus_meet', 'plus_power', 'plus_speed', 'plus_arm', 'plus_defense', 'plus_catching')


@app.route('/api/update_abilities', methods=['POST'])
def update_abilities():
    data = request.get_json(silent=True) or {}
    player_id = data.get('player_id')
    abilities = data.get('abilities') or {}
    update = {}
    for key in ABILITY_KEYS:
        if key not in abilities:
            continue
        try:
            value = int(abilities[key])
        except (TypeError, ValueError):
            return jsonify({'ok': False}), 400
        if value < 0 or value > 16:
            return jsonify({'ok': False}), 400
        update[key] = value
    if player_id is None:
        return jsonify({'ok': False}), 400
    if update:
        players_ref().document(str(player_id)).set(update, merge=True)
    return jsonify({'ok': True})
