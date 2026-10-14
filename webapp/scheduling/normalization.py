"""日程処理: normalization。"""
import re
import secrets
from webapp.scheduling.common import STATUSES, _player_id
from webapp.scheduling.dates import clip, parse_by, parse_iso, plain_name
from webapp.scheduling.events import normalize_events
from webapp.scheduling.games import normalize_game
from webapp.scheduling.people import normalize_event_people


def empty_poll():
    return {'removed': [], 'added': [], 'answers': {}, 'games': {}, 'events': {}}



def _iso_list(values):
    cleaned = []
    if not isinstance(values, list):
        return cleaned
    for item in values:
        parsed = parse_iso(item)
        if parsed is None:
            continue
        iso = parsed.isoformat()
        if iso not in cleaned:
            cleaned.append(iso)
    cleaned.sort()
    return cleaned[:80]



def normalize_poll(raw):
    poll = empty_poll()
    if not isinstance(raw, dict):
        return poll
    poll['removed'] = _iso_list(raw.get('removed'))
    poll['added'] = _iso_list(raw.get('added'))
    answers = raw.get('answers')
    if isinstance(answers, dict):
        for iso, bucket in answers.items():
            parsed = parse_iso(iso)
            if parsed is None or not isinstance(bucket, dict):
                continue
            people = {}
            for player_id, record in bucket.items():
                if not isinstance(record, dict) or record.get('status') not in STATUSES:
                    continue
                item = {'status': record['status']}
                if record['status'] == 'pending':
                    by = parse_by(record.get('by'))
                    if not by:
                        continue
                    item['by'] = by
                key = str(player_id)
                if _player_id(key) is not None:
                    people[key] = item
                    continue
                if re.fullmatch(r'm:[a-f0-9]{8}', key):
                    name = clip(record.get('name'), 40).strip()
                    if name:
                        item['name'] = name
                    people[key] = item
                    continue
                if not key.startswith('n:') or len(key) <= 2:
                    continue
                name = clip(record.get('name'), 40).strip()
                if not name or plain_name(name)[:40] != key[2:]:
                    continue
                item['name'] = name
                people[key] = item
            if people:
                poll['answers'][parsed.isoformat()] = people
    games = raw.get('games')
    if isinstance(games, dict):
        for iso, game in games.items():
            parsed = parse_iso(iso)
            cleaned = normalize_game(game)
            if parsed is not None and cleaned is not None:
                poll['games'][parsed.isoformat()] = cleaned
    poll['events'] = normalize_events(raw.get('events'))
    if 'eventPeople' in raw and raw.get('eventPeople') is not None:
        poll['eventPeople'] = normalize_event_people(raw.get('eventPeople'))
    else:
        poll['eventPeople'] = None
    if 'answerPeople' in raw and raw.get('answerPeople') is not None:
        poll['answerPeople'] = normalize_event_people(raw.get('answerPeople'))
    else:
        poll['answerPeople'] = None
    return poll



def public_view(poll):
    return {
        'removed': poll['removed'],
        'added': poll['added'],
        'answers': poll['answers'],
    }
