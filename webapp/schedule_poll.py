"""日程調整ボードの保存形式。日付の出欠と試合カードに加え、別枠のイベントを持つ。"""

import re
import secrets
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    JST = ZoneInfo('Asia/Tokyo')
except Exception:
    JST = timezone(timedelta(hours=9))

STATUSES = {'all', 'am', 'pm', 'pending', 'out'}
EVENT_STATUSES = {'in', 'pending', 'out'}
POSITIONS = {'', '投', '捕', '一', '二', '三', '遊', '左', '中', '右', 'DH'}
EVENT_NAMES = {'公式戦', '練習試合'}
UNIFORMS = {'黒', '青'}
BATS = {'ウレタン可', '金属・木製のみ', '情報なし'}


class PollError(ValueError):
    pass


def japan_today():
    return datetime.now(JST).date()


def window_end(today):
    month = today.month + 2
    year = today.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return date(year, month, 1) - timedelta(days=1)


def parse_iso(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def in_window(value, today):
    parsed = parse_iso(value)
    return parsed is not None and today <= parsed <= window_end(today)


def event_window_end(today):
    month = today.month + 6
    year = today.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month + 1, 1) - timedelta(days=1)


def in_event_window(value, today):
    parsed = parse_iso(value)
    return parsed is not None and today <= parsed <= event_window_end(today)


def parse_by(value):
    parsed = parse_iso(value)
    if parsed is None or parsed.year < 2000 or parsed.year > 2100:
        return None
    return parsed.isoformat()


def plain_name(name):
    return str(name or '').replace(' ', '').replace('　', '')


def clip(value, limit):
    text = str(value or '').replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')
    return text[:limit]


def time_or_blank(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{2}:\d{2}', value):
        return ''
    hour, minute = int(value[:2]), int(value[3:])
    if hour > 23 or minute > 59:
        return ''
    return f'{hour:02d}:{minute:02d}'


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


def _player_id(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def normalize_lineup(rows, by_name=None):
    bound = []
    if not isinstance(rows, list):
        rows = []
    for slot in rows[:10]:
        if not isinstance(slot, dict):
            slot = {}
        name = clip(slot.get('n'), 40).strip()
        pos = slot.get('p') if slot.get('p') in POSITIONS else ''
        record = {'n': name, 'p': pos}
        if by_name is not None:
            player_id = by_name.get(plain_name(name))
            if player_id:
                record['player_id'] = int(player_id)
        else:
            player_id = _player_id(slot.get('player_id'))
            if player_id:
                record['player_id'] = player_id
        bound.append(record)
    while len(bound) < 10:
        bound.append({'n': '', 'p': ''})
    return bound


def normalize_game(game, by_name=None):
    if not isinstance(game, dict) or game.get('slot') not in ('am', 'pm'):
        return None
    event_name = game.get('eventName')
    uniform = game.get('uniform')
    bat = game.get('bat')
    if bat == '使用可能バット情報なし':
        bat = '情報なし'
    return {
        'slot': game['slot'],
        'opponent': clip(game.get('opponent'), 80).strip(),
        'eventName': event_name if event_name in EVENT_NAMES else '練習試合',
        'stadium': clip(game.get('stadium'), 80).strip(),
        'address': clip(game.get('address'), 120).strip(),
        'uniform': uniform if uniform in UNIFORMS else '黒',
        'bat': bat if bat in BATS else '情報なし',
        'timeGather': time_or_blank(game.get('timeGather')),
        'timePB': time_or_blank(game.get('timePB')),
        'bench': clip(game.get('bench'), 500).strip(),
        'lineup': normalize_lineup(game.get('lineup'), by_name),
    }


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


def _event_id(value):
    if isinstance(value, str) and re.fullmatch(r'[a-f0-9]{8}', value):
        return value
    return None


def _event_people(bucket):
    people = {}
    if not isinstance(bucket, dict):
        return people
    for player_id, record in bucket.items():
        if not isinstance(record, dict) or record.get('status') not in EVENT_STATUSES:
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
    return people


def normalize_events(raw):
    cleaned = {}
    if not isinstance(raw, dict):
        return cleaned
    for key, event in list(raw.items())[:40]:
        event_id = _event_id(key)
        if event_id is None or not isinstance(event, dict):
            continue
        name = clip(event.get('name'), 40).strip()
        dates = []
        for iso in event.get('dates') or []:
            parsed = parse_iso(iso)
            if parsed is None:
                continue
            text = parsed.isoformat()
            if text not in dates:
                dates.append(text)
        dates = sorted(dates)[:14]
        if not name or not dates:
            continue
        raw_answers = event.get('answers') if isinstance(event.get('answers'), dict) else {}
        answers = {}
        for iso in dates:
            people = _event_people(raw_answers.get(iso))
            if people:
                answers[iso] = people
        cleaned[event_id] = {
            'name': name,
            'place': clip(event.get('place'), 80).strip(),
            'address': clip(event.get('address'), 120).strip(),
            'timeStart': time_or_blank(event.get('timeStart')),
            'note': clip(event.get('note'), 500).strip(),
            'dates': dates,
            'answers': answers,
            'confirmed': bool(event.get('confirmed')),
        }
    return cleaned


def _write_answers(poll, key, answers, today, name=None):
    if not isinstance(answers, dict) or len(answers) > 62:
        raise PollError('回答の形式が違います。')
    for iso, payload in answers.items():
        if not in_window(iso, today):
            raise PollError('今日から来月末までの日付だけ回答できます。')
        if not isinstance(payload, dict):
            raise PollError('回答の形式が違います。')
        status = payload.get('status') or ''
        bucket = poll['answers'].setdefault(iso, {})
        if status == '':
            bucket.pop(key, None)
            if not bucket:
                poll['answers'].pop(iso, None)
            continue
        if status not in STATUSES:
            raise PollError('選択肢が違います。')
        record = {'status': status}
        if name:
            record['name'] = name
        if status == 'pending':
            by = parse_by(payload.get('by'))
            if not by:
                raise PollError('未定の場合は、回答期日を設定してください。')
            record['by'] = by
        bucket[key] = record


def apply_answer(poll, roster_ids, player_id, answers, today):
    listed = poll.get('answerPeople')
    key = str(player_id)
    if listed is None:
        if player_id not in roster_ids:
            raise PollError('選手が見つかりません。')
    elif not any(person.get('id') == key for person in listed):
        raise PollError('回答対象ではありません。')
    _write_answers(poll, key, answers, today)


def apply_board_member_answer(poll, person_id, answers, today, roster_ids=None):
    key = str(person_id or '')
    listed = poll.get('answerPeople')
    if listed is None:
        player_id = _player_id(key)
        if player_id is None or (roster_ids is not None and player_id not in roster_ids):
            raise PollError('回答対象ではありません。')
        _write_answers(poll, str(player_id), answers, today)
        return
    match = next((person for person in listed if person.get('id') == key), None)
    if match is None:
        raise PollError('回答対象ではありません。')
    _write_answers(poll, key, answers, today, match.get('name') if key.startswith('m:') else None)


def apply_guest_answer(poll, name, answers, today, by_name):
    display = clip(name, 40).strip()
    plain = plain_name(display)[:40]
    if not plain:
        raise PollError('名前を入力してください。')
    listed = poll.get('answerPeople')
    if listed is not None:
        match = next((person for person in listed if plain_name(person.get('name')) == plain_name(display)), None)
        if match:
            key = match.get('id')
            _write_answers(poll, key, answers, today, match.get('name') if str(key).startswith('m:') else None)
            return
        _write_answers(poll, 'n:' + plain, answers, today, display)
        return
    player_id = (by_name or {}).get(plain_name(display))
    if player_id:
        try:
            player_id = int(player_id)
        except (TypeError, ValueError):
            player_id = None
    if player_id:
        apply_answer(poll, {player_id}, player_id, answers, today)
        return
    _write_answers(poll, 'n:' + plain, answers, today, display)


def apply_add(poll, iso, routine, today):
    if not in_window(iso, today):
        raise PollError('足せるのは今日から来月末までです。')
    if routine:
        if iso not in poll['removed']:
            raise PollError('その日はもう並んでいます。')
        poll['removed'] = [item for item in poll['removed'] if item != iso]
        return
    if iso in poll['added']:
        raise PollError('その日はもう並んでいます。')
    if len(poll['added']) >= 62:
        raise PollError('これ以上は足せません。')
    poll['removed'] = [item for item in poll['removed'] if item != iso]
    poll['added'].append(iso)
    poll['added'].sort()


def apply_remove(poll, iso, today):
    if not in_window(iso, today):
        raise PollError('外せるのは今日から来月末までです。')
    poll['added'] = [item for item in poll['added'] if item != iso]
    if iso not in poll['removed']:
        poll['removed'].append(iso)
        poll['removed'].sort()
    poll['answers'].pop(iso, None)
    poll['games'].pop(iso, None)


def apply_clear_game(poll, iso, today):
    if not in_window(iso, today):
        raise PollError('今日から来月末までの試合カードだけ削除できます。')
    poll['games'].pop(iso, None)


def apply_game(poll, iso, game, by_name, today):
    if not in_window(iso, today):
        raise PollError('今日から来月末までの日付だけ保存できます。')
    cleaned = normalize_game(game, by_name)
    if cleaned is None:
        raise PollError('午前か午後を選んでください。')
    poll['games'][iso] = cleaned


def _event_dates(payload, existing, today):
    raw_dates = payload.get('dates') if isinstance(payload, dict) else None
    if not isinstance(raw_dates, list) or not raw_dates:
        raise PollError('日付を1つ以上選んでください。')
    dates = []
    known = set(existing or [])
    for iso in raw_dates:
        parsed = parse_iso(iso)
        if parsed is None:
            raise PollError('日付の形式が違います。')
        text = parsed.isoformat()
        if text in dates:
            continue
        if text not in known and not in_event_window(text, today):
            raise PollError('足せるのは今日から6か月先の月末までです。')
        dates.append(text)
    if len(dates) > 14:
        raise PollError('日付は14日までです。')
    dates.sort()
    return dates


def apply_event_put(poll, event_id, payload, today):
    if not isinstance(payload, dict):
        raise PollError('形式が違います。')
    name = clip(payload.get('name'), 40).strip()
    if not name:
        raise PollError('名前を入力してください。')
    creating = not event_id
    if creating:
        if len(poll['events']) >= 40:
            raise PollError('これ以上は追加できません。')
        event_id = secrets.token_hex(4)
        while event_id in poll['events']:
            event_id = secrets.token_hex(4)
        previous = {}
    else:
        if _event_id(event_id) is None or event_id not in poll['events']:
            raise PollError('イベントが見つかりません。')
        previous = poll['events'][event_id]
    dates = _event_dates(payload, previous.get('dates'), today)
    old_answers = dict(previous.get('answers') or {})
    previous_dates = set(previous.get('dates') or [])
    removed = [iso for iso in previous_dates if iso not in dates]
    added = [iso for iso in dates if iso not in previous_dates]
    if len(removed) == 1 and len(added) == 1 and added[0] not in old_answers:
        old_answers[added[0]] = old_answers.pop(removed[0], {})
    answers = {iso: old_answers[iso] for iso in dates if iso in old_answers}
    poll['events'][event_id] = {
        'name': name,
        'place': clip(payload.get('place'), 80).strip(),
        'address': clip(payload.get('address'), 120).strip(),
        'timeStart': time_or_blank(payload.get('timeStart')),
        'note': clip(payload.get('note'), 500).strip(),
        'dates': dates,
        'answers': answers,
        'confirmed': bool(previous.get('confirmed')),
    }


def apply_event_confirm(poll, event_id):
    if _event_id(event_id) is None or event_id not in poll['events']:
        raise PollError('イベントが見つかりません。')
    poll['events'][event_id]['confirmed'] = True


def apply_event_delete(poll, event_id):
    if _event_id(event_id) is None or event_id not in poll['events']:
        raise PollError('イベントが見つかりません。')
    poll['events'].pop(event_id, None)


def _write_event_answers(poll, event_id, key, answers, name=None):
    event = poll['events'].get(event_id)
    if event is None:
        raise PollError('イベントが見つかりません。')
    if not isinstance(answers, dict) or len(answers) > 14:
        raise PollError('回答の形式が違います。')
    allowed = set(event['dates'])
    stored = event.setdefault('answers', {})
    for iso, payload in answers.items():
        if iso not in allowed or not isinstance(payload, dict):
            raise PollError('その日はこのイベントに含まれていません。')
        status = payload.get('status') or ''
        bucket = stored.setdefault(iso, {})
        if status == '':
            bucket.pop(key, None)
            if not bucket:
                stored.pop(iso, None)
            continue
        if status not in EVENT_STATUSES:
            raise PollError('選択肢が違います。')
        record = {'status': status}
        if name:
            record['name'] = name
        if status == 'pending':
            by = parse_by(payload.get('by'))
            if not by:
                raise PollError('未定の場合は、回答期日を設定してください。')
            record['by'] = by
        bucket[key] = record


def apply_event_member_answer(poll, event_id, person_id, answers, roster_ids=None):
    if _event_id(event_id) is None:
        raise PollError('イベントが見つかりません。')
    key = str(person_id or '')
    listed = poll.get('eventPeople')
    if listed is None:
        player_id = _player_id(key)
        if player_id is None or (roster_ids is not None and player_id not in roster_ids):
            raise PollError('回答対象ではありません。')
        _write_event_answers(poll, event_id, key, answers)
        return
    match = next((person for person in listed if person.get('id') == key), None)
    if match is None:
        raise PollError('回答対象ではありません。')
    _write_event_answers(poll, event_id, key, answers, match.get('name') if key.startswith('m:') else None)


def apply_event_answer(poll, event_id, player_id, name, answers, roster_ids, by_name):
    if _event_id(event_id) is None:
        raise PollError('イベントが見つかりません。')
    if player_id is None:
        display = clip(name, 40).strip()
        plain = plain_name(display)[:40]
        if not plain:
            raise PollError('名前を入力してください。')
        matched = (by_name or {}).get(plain_name(display))
        try:
            matched = int(matched) if matched else None
        except (TypeError, ValueError):
            matched = None
        if matched:
            _write_event_answers(poll, event_id, str(matched), answers)
            return
        _write_event_answers(poll, event_id, 'n:' + plain, answers, display)
        return
    if player_id not in roster_ids:
        raise PollError('選手が見つかりません。')
    _write_event_answers(poll, event_id, str(player_id), answers)


def public_view(poll):
    return {
        'removed': poll['removed'],
        'added': poll['added'],
        'answers': poll['answers'],
    }
