"""日程調整ボードの保存形式。日付の出欠と、進めた日の試合カードだけを持つ。"""

import re
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    JST = ZoneInfo('Asia/Tokyo')
except Exception:
    JST = timezone(timedelta(hours=9))

STATUSES = {'all', 'am', 'pm', 'pending', 'out'}
POSITIONS = {'', '投', '捕', '一', '二', '三', '遊', '左', '中', '右', 'DH'}
EVENT_NAMES = {'公式戦', '練習試合'}
UNIFORMS = {'黒', '青'}
BATS = {'ウレタン可', '金属・木製のみ', '使用可能バット情報なし'}


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
    return {'removed': [], 'added': [], 'answers': {}, 'games': {}}


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
    if any(row['p'] == 'DH' for row in bound[:9]):
        bound[9]['p'] = '投'
    return bound


def normalize_game(game, by_name=None):
    if not isinstance(game, dict) or game.get('slot') not in ('am', 'pm'):
        return None
    event_name = game.get('eventName')
    uniform = game.get('uniform')
    bat = game.get('bat')
    return {
        'slot': game['slot'],
        'opponent': clip(game.get('opponent'), 80).strip(),
        'eventName': event_name if event_name in EVENT_NAMES else '公式戦',
        'stadium': clip(game.get('stadium'), 80).strip(),
        'address': clip(game.get('address'), 120).strip(),
        'uniform': uniform if uniform in UNIFORMS else '黒',
        'bat': bat if bat in BATS else 'ウレタン可',
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
                people[str(player_id)] = item
            if people:
                poll['answers'][parsed.isoformat()] = people
    games = raw.get('games')
    if isinstance(games, dict):
        for iso, game in games.items():
            parsed = parse_iso(iso)
            cleaned = normalize_game(game)
            if parsed is not None and cleaned is not None:
                poll['games'][parsed.isoformat()] = cleaned
    return poll


def apply_answer(poll, roster_ids, player_id, answers, today):
    if player_id not in roster_ids:
        raise PollError('選手が見つかりません。')
    if not isinstance(answers, dict) or len(answers) > 62:
        raise PollError('回答の形式が違います。')
    key = str(player_id)
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
        if status == 'pending':
            by = parse_by(payload.get('by'))
            if not by:
                raise PollError('未定のときは、いつまでに答えるかを入れてください。')
            record['by'] = by
        bucket[key] = record


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


def apply_game(poll, iso, game, by_name, today):
    if not in_window(iso, today):
        raise PollError('今日から来月末までの日付だけ保存できます。')
    cleaned = normalize_game(game, by_name)
    if cleaned is None:
        raise PollError('午前か午後を選んでください。')
    poll['games'][iso] = cleaned


def public_view(poll):
    return {
        'removed': poll['removed'],
        'added': poll['added'],
        'answers': poll['answers'],
    }
