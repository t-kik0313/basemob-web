"""日程処理: events。"""
import re
import secrets
from webapp.scheduling.common import EVENT_STATUSES, PollError, _player_id
from webapp.scheduling.dates import clip, in_event_window, parse_by, parse_iso, plain_name, time_or_blank


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
