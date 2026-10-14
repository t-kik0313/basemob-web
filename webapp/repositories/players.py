"""旧 tenant.py の処理を役割別に分割。"""
from webapp.repositories.references import players_ref


def roster_rows(team_id=None):
    rows = []
    for doc in players_ref(team_id).stream():
        data = doc.to_dict() or {}
        try:
            player_id = int(data.get('player_id') or doc.id)
        except (TypeError, ValueError):
            continue
        number = data.get('number')
        if number is None or str(number).strip() == '':
            number = data.get('no', '')
        rows.append({
            'player_id': player_id,
            'name': data.get('name') or '',
            'no': number,
            'number': number,
            'image_path': data.get('image_path') or 'default.png',
            'pos1': data.get('pos1') or '',
            'pitch_bat': data.get('pitch_bat') or '',
        })
    rows.sort(key=lambda row: _jersey_sort(row['no']))
    return rows



def _jersey_sort(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 999



def next_player_id(team_id=None):
    numbers = [row['player_id'] for row in roster_rows(team_id)]
    return max(numbers) + 1 if numbers else 1
