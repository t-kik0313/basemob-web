import uuid

from flask import redirect, render_template, request, url_for

from webapp import app
from webapp.firebase import db
from webapp.stats.ability_ranks import flag_on
from webapp.teams.context import current_team
from webapp.repositories.references import players_ref
from webapp.repositories.players import roster_rows


def _ability_kinds():
    team = current_team()
    if not team or not team.get('ability_kinds'):
        return [('qual_sayonara', 'サヨナラ男')]
    return team['ability_kinds']


def _player_rows(kinds):
    rows = []
    flags_by_id = {}
    try:
        for doc in players_ref().stream():
            flags_by_id[str(doc.id)] = doc.to_dict() or {}
    except Exception as error:
        print(f"⚠️ 定性特殊能力の読み込みエラー: {error}")
    for player in roster_rows():
        flags = flags_by_id.get(str(player['player_id']), {})
        rows.append({
            'player_id': player['player_id'],
            'no': player['no'],
            'name': player['name'],
            'flags': {key: flag_on(flags.get(key)) for key, _label in kinds},
        })
    return rows


@app.route('/admin/qualitative_abilities', methods=['GET', 'POST'])
def qualitative_abilities():
    kinds = _ability_kinds()
    if request.method == 'POST':
        shown = [key for key in request.form.getlist('kind_keys') if key]
        label = (request.form.get('new_kind') or '').strip()
        if label and db is not None:
            team = current_team()
            stored = [{'key': key, 'label': name} for key, name in kinds]
            if not any(item['label'] == label for item in stored):
                stored.append({'key': f'qual_{uuid.uuid4().hex[:8]}', 'label': label})
                db.collection('teams').document(team['id']).set({'ability_kinds': stored}, merge=True)
        roster = roster_rows()
        for key in shown:
            selected = {str(value) for value in request.form.getlist(key)}
            for player in roster:
                player_id = str(player['player_id'])
                players_ref().document(player_id).set({key: player_id in selected}, merge=True)
        return redirect(url_for('qualitative_abilities'))
    return render_template(
        'qualitative_abilities.html',
        players=_player_rows(kinds),
        abilities=kinds,
    )
