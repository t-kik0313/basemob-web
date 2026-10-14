"""旧 tenant.py の処理を役割別に分割。"""
from webapp.firebase import db
from webapp.repositories.references import players_ref
from webapp.teams.context import current_team_id

IDENTITY_FIELDS = (
    'name', 'number', 'no', 'pos1', 'pos2', 'pos3',
    'pitch_bat', 'image_path', 'birth_date', 'player_id',
)


def load_player_shell(player_id):
    from webapp.stats.json_cache import get_players_data_json

    player = next((row for row in get_players_data_json() if row.get('player_id') == player_id), None)
    stored = {}
    if db is not None and current_team_id():
        doc = players_ref().document(str(player_id)).get()
        if doc.exists:
            stored = doc.to_dict() or {}
    if player is None and not stored:
        return None
    if player is None:
        player = {'player_id': player_id}
    for key in IDENTITY_FIELDS:
        value = stored.get(key)
        if value not in (None, ''):
            player[key] = value
    for key, value in stored.items():
        if key.startswith('plus_') or key.startswith('qual_'):
            player[key] = value
    player['player_id'] = player_id
    player['id'] = player_id
    return player
