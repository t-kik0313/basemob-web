"""日程処理: people。"""
import re
import secrets
from webapp.scheduling.common import PollError, _player_id
from webapp.scheduling.dates import clip, plain_name


def normalize_event_people(raw):
    cleaned = []
    seen = set()
    if not isinstance(raw, list):
        return cleaned
    for item in raw[:60]:
        if not isinstance(item, dict):
            continue
        name = clip(item.get('name'), 40).strip()
        if not name:
            continue
        raw_id = item.get('id')
        player_id = _player_id(raw_id)
        if player_id is not None:
            key = str(player_id)
        elif isinstance(raw_id, str) and re.fullmatch(r'm:[a-f0-9]{8}', raw_id):
            key = raw_id
        else:
            continue
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({'id': key, 'name': name})
    return cleaned



def _store_people(poll, field, payload, roster_rows):
    if not isinstance(payload, list):
        raise PollError('形式が違います。')
    by_id = {}
    by_name = {}
    for row in roster_rows or []:
        if not row.get('name'):
            continue
        by_id[str(row.get('player_id'))] = row
        key = plain_name(row.get('name'))
        if key and key not in by_name:
            by_name[key] = row
    built = []
    seen_ids = set()
    seen_names = set()
    for item in payload[:60]:
        if not isinstance(item, dict):
            continue
        name = clip(item.get('name'), 40).strip()
        plain = plain_name(name)[:40]
        if not plain or plain in seen_names:
            continue
        raw_id = str(item.get('id') or '')
        player = by_id.get(raw_id) if raw_id.isdigit() else None
        if player is None:
            player = by_name.get(plain_name(name))
        if player is not None:
            key = str(player.get('player_id'))
            name = player.get('name') or name
        elif re.fullmatch(r'm:[a-f0-9]{8}', raw_id):
            key = raw_id
        else:
            key = 'm:' + secrets.token_hex(4)
        if key in seen_ids:
            continue
        seen_ids.add(key)
        seen_names.add(plain_name(name)[:40])
        built.append({'id': key, 'name': name})
    poll[field] = built



def apply_event_people(poll, payload, roster_rows):
    _store_people(poll, 'eventPeople', payload, roster_rows)



def apply_answer_people(poll, payload, roster_rows):
    _store_people(poll, 'answerPeople', payload, roster_rows)



def _people_view(poll, field, roster_rows):
    stored = poll.get(field) if isinstance(poll, dict) else None
    if stored is None:
        people = [
            {'id': str(row.get('player_id')), 'name': row.get('name')}
            for row in roster_rows or []
            if row.get('name')
        ]
        return people, False
    return stored, True



def event_people_view(poll, roster_rows):
    return _people_view(poll, 'eventPeople', roster_rows)



def answer_people_view(poll, roster_rows):
    return _people_view(poll, 'answerPeople', roster_rows)
