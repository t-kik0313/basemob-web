from webapp.presentation import page_route, screen_response, action_route
from flask import request, redirect, url_for
import traceback
from webapp import app
from webapp.firebase import db, db_old
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv


@page_route('/input_form_R1/<int:player_id>')
def input_form_R1(player_id):
    players_df = load_players_df()
    player = players_df[players_df['player_id'] == player_id].iloc[0].to_dict()
    player['id'] = player_id
    player['player_id'] = player_id
    return screen_response('input_form_R1.html', player=player)

@action_route('/save_record/<int:player_id>', methods=['POST'])
def save_record(player_id):
    game_date = request.form.get('game_date')
    game_id = request.form.get('game_id')
    stadium = request.form.get('stadium')
    game_type = request.form.get('game_type', 'official')
    batting_order = request.form.get('batting_order', 'sub')
    fielding_position = request.form.get('fielding_position', 'PR')

    game_sb = int(request.form.get('game_sb', 0))
    game_runs = int(request.form.get('game_runs', 0))
    game_rbi = int(request.form.get('game_rbi', 0))
    game_errors = int(request.form.get('game_errors', 0))
    game_gidp = int(request.form.get('game_gidp', 0))

    results = request.form.getlist('result[]')
    directions = request.form.getlist('direction[]')
    runners = request.form.getlist('runner[]')
    vs_lefts = request.form.getlist('vs_left[]')
    sayonaras = request.form.getlist('sayonara[]')

    batch = db.batch()
    coll_ref = db.collection('game_records')

    for i in range(len(results)):
        strikes = request.form.get(f's{i+1}', '0')
        record = {
            'player_id': player_id, 'game_date': game_date, 'game_id': game_id,
            'stadium': stadium, 'game_type': game_type,
            'batting_order': batting_order, 'fielding_position': fielding_position,
            'result': results[i], 'direction': directions[i], 'runner': runners[i], 'strikes': strikes,
            'vs_left': vs_lefts[i] if i < len(vs_lefts) else 0,
            'sayonara': sayonaras[i] if i < len(sayonaras) else 0,
            'sb': game_sb if i == 0 else 0, 'runs': game_runs if i == 0 else 0,
            'rbi': game_rbi if i == 0 else 0, 'errors': game_errors if i == 0 else 0,
            'gidp': game_gidp if i == 0 else 0
        }
        doc_ref = coll_ref.document() # Firebaseが自動でIDを発行
        batch.set(doc_ref, record)

    batch.commit()
    update_json_from_csv()
    return redirect(url_for('player_detail_R1', player_id=player_id))



@action_route('/update_game_record/<int:player_id>', methods=['POST'])
def update_game_record(player_id):
    doc_id = request.form.get('csv_index') # FirebaseのIDを受け取る
    update_fields = ['game_date', 'game_id', 'result', 'direction', 'runner', 'strikes',
                     'stadium', 'game_type', 'batting_order', 'fielding_position']
    checkbox_fields = ['is_official', 'is_4th_bat', 'is_hr', 'advancing_runner', 'vs_left', 'multi_hit', 'sayonara']

    update_data = {}
    for f in update_fields:
        if request.form.get(f) is not None: update_data[f] = request.form.get(f)
    for f in checkbox_fields:
        update_data[f] = '1' if request.form.get(f) else '0'

    if doc_id and db is not None:
        db.collection('game_records').document(str(doc_id)).update(update_data)

    update_json_from_csv()
    return redirect(url_for('player_detail_R1', player_id=player_id))

@action_route('/delete_game_record/<int:player_id>/<string:csv_index>', methods=['POST'])
def delete_game_record(player_id, csv_index):
    if db is not None:
        db.collection('game_records').document(str(csv_index)).delete()
    update_json_from_csv()
    return redirect(url_for('player_detail_R1', player_id=player_id))


