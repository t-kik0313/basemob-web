"""日程処理: answers。"""
import re
import secrets
from webapp.scheduling.common import PollError, STATUSES, _player_id
from webapp.scheduling.dates import clip, in_window, parse_by, plain_name


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
