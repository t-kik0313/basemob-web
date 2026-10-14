"""日程処理: games。"""
import re
import secrets
from webapp.scheduling.common import BATS, EVENT_NAMES, POSITIONS, PollError, UNIFORMS, _player_id
from webapp.scheduling.dates import clip, in_window, plain_name, time_or_blank


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
