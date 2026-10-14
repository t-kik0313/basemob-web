"""日程処理: common。"""
import re
import secrets

STATUSES = {'all', 'am', 'pm', 'pending', 'out'}
EVENT_STATUSES = {'in', 'pending', 'out'}
POSITIONS = {'', '投', '捕', '一', '二', '三', '遊', '左', '中', '右', 'DH'}
EVENT_NAMES = {'公式戦', '練習試合'}
UNIFORMS = {'黒', '青'}
BATS = {'ウレタン可', '金属・木製のみ', '情報なし'}


class PollError(ValueError):
    pass



def _player_id(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None
