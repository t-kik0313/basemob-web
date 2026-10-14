"""旧 tenant.py の処理を役割別に分割。"""
from webapp.teams.context import plain_name


def bind_schedule_people(items, roster):
    by_name = {}
    for player in roster:
        key = plain_name(player.get('name'))
        if key and key not in by_name:
            by_name[key] = player.get('player_id')

    def with_id(name, extra=None):
        record = {'n': name}
        if extra:
            record.update(extra)
        player_id = by_name.get(plain_name(name))
        if player_id:
            record['player_id'] = player_id
        else:
            record.pop('player_id', None)
        return record

    bound = []
    for event in items:
        if not isinstance(event, dict):
            continue
        copied = dict(event)
        lineup = []
        for slot in copied.get('lineup') or []:
            if isinstance(slot, dict):
                row = with_id(slot.get('n') or '', {k: v for k, v in slot.items() if k not in ('n', 'player_id')})
            else:
                row = with_id(str(slot or ''))
            lineup.append(row)
        copied['lineup'] = lineup
        for key in ('attendees', 'absentees'):
            people = []
            for person in copied.get(key) or []:
                name = person.get('n') if isinstance(person, dict) else person
                people.append(with_id(name or ''))
            copied[key] = people
        pendings = []
        for person in copied.get('pendings') or []:
            if isinstance(person, dict):
                pendings.append(with_id(person.get('n') or '', {'d': person.get('d') or ''}))
            else:
                pendings.append(with_id(str(person or ''), {'d': ''}))
        copied['pendings'] = pendings
        bound.append(copied)
    return bound



def public_event(event):
    return {
        'opponent': (event or {}).get('opponent') or '',
        'date': (event or {}).get('date') or '',
        'time': (event or {}).get('timePB') or '',
    }
